"""
Implementação simplificada do consumidor RabbitMQ para TCC
"""

import json
import time
from typing import Optional

import pika
import pika.exceptions

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class RabbitMQConsumer(BaseBroker):
    """Consumidor RabbitMQ simplificado - mede latência real sem dependências"""

    def __init__(self, run_id: Optional[str] = None):
        super().__init__("rabbitmq", run_id=run_id)
        self.config = BROKER_CONFIGS["rabbitmq"]
        self.received_count = 0
        self.expected_count = 0
        self.channel = None
        self.connection = None
    
    def send_messages(self, count: int, message_size: int, rps: Optional[int] = None) -> bool:
        """Método não usado por consumidores - apenas para compatibilidade com BaseBroker"""
        return True

    def consume_messages(self, expected_count: int, **kwargs) -> bool:
        """
        Consome mensagens do RabbitMQ de forma simples e eficiente
        
        Args:
            expected_count: Número de mensagens esperadas
        """
        try:
            self.metrics.start_timing()
            self.expected_count = expected_count
            self.received_count = 0
            
            # Conectar ao RabbitMQ
            self.connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.config["host"],
                    port=self.config["port"],
                    credentials=pika.PlainCredentials(
                        self.config["username"], 
                        self.config["password"]
                    ),
                    heartbeat=300,  # Heartbeat de 5 minutos
                    blocked_connection_timeout=300,  # Timeout de 5 minutos
                )
            )
            self.channel = self.connection.channel()
            
            # Declarar fila (Quorum Queue)
            self.channel.queue_declare(
                queue=self.config["queue"],
                durable=True,
                arguments={
                    "x-queue-type": "quorum"
                }
            )
            
            # Configurar QoS 
            self.channel.basic_qos(prefetch_count=100)
            
            self.logger.info(f"Consumidor RabbitMQ conectado à fila {self.config['queue']}")
            
            # Callback para processar mensagens
            def callback(ch, method, properties, body):
                try:
                    # Calcular latência simples: tempo atual - timestamp da mensagem
                    current_time = time.time()
                    
                    # Decodificar mensagem
                    msg_data = json.loads(body.decode("utf-8"))
                    
                    # Extrair timestamp do envio
                    if isinstance(msg_data, dict) and "timestamp" in msg_data:
                        send_time = msg_data["timestamp"]
                    else:
                        send_time = current_time  # Fallback
                    
                    latency = current_time - send_time
                    
                    # Validar latência (deve ser positiva e razoável)
                    if 0 <= latency <= 10:  # Latência máxima esperada de 10 segundos
                        self.metrics.record_latency(latency, str(self.received_count + 1))
                    
                    self.received_count += 1
                    
                    # Log a cada 1000 mensagens ou a cada 10 para cargas pequenas (<=100 mensagens)
                    log_interval = 10 if self.expected_count <= 100 else 1000
                    if self.received_count % log_interval == 0:
                        self.logger.info(f"Recebidas {self.received_count}/{self.expected_count} mensagens")
                    
                    # Confirmar recebimento
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                    
                    # Parar se recebemos todas as mensagens
                    if self.received_count >= self.expected_count:
                        self.logger.info(f"Recebidas {self.received_count} mensagens esperadas. Finalizando consumo.")
                        ch.stop_consuming()
                        
                except Exception as e:
                    self.logger.warning(f"Erro ao processar mensagem: {e}")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
            
            # Iniciar consumo
            self.channel.basic_consume(
                queue=self.config["queue"],
                on_message_callback=callback,
                auto_ack=False
            )
            
            # Consumir mensagens
            self.logger.info(f"Iniciando consumo de {expected_count} mensagens...")
            
            # Usar timeout baseado no número de mensagens esperadas
            timeout_seconds = max(30, expected_count / 100)  # No mínimo 30s, ou 100msg/s
            start_consuming_time = time.time()
            
            try:
                while self.received_count < self.expected_count:
                    # Processar mensagens
                    self.connection.process_data_events(time_limit=1)
                    
                    # Verificar timeout
                    if time.time() - start_consuming_time > timeout_seconds:
                        self.logger.warning(f"Timeout após {timeout_seconds}s. Recebidas {self.received_count}/{self.expected_count} mensagens")
                        break
                        
            except KeyboardInterrupt:
                self.logger.info("Consumo interrompido pelo usuário")
            except Exception as e:
                self.logger.error(f"Erro durante consumo: {e}")
            
            # Fechar conexão
            if self.connection and not self.connection.is_closed:
                self.connection.close()
            
            # Finalizar métricas
            self.metrics.end_timing()
            self.metrics.messages_consumed = self.received_count
            self.metrics.save_latencies()
            self.metrics.save_summary()
            
            # Log resumo
            self.logger.info(f"Consumo finalizado: {self.received_count} mensagens recebidas")
            
            return self.received_count >= self.expected_count
            
        except Exception as e:
            self.logger.error(f"Erro no consumidor RabbitMQ: {e}")
            return False