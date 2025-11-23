"""
Implementação simplificada do produtor RabbitMQ para TCC
"""

import json
import time
import uuid
from typing import Optional

import pika
import pika.exceptions

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class RabbitMQProducer(BaseBroker):
    """Produtor RabbitMQ simplificado - envia mensagens com timestamp embutido"""

    def __init__(self, run_id: Optional[str] = None):
        super().__init__("rabbitmq", run_id=run_id)
        self.config = BROKER_CONFIGS["rabbitmq"]

    def send_messages(
        self, count: int, size: int, rps: Optional[int] = None, **kwargs
    ) -> bool:
        """
        Envia mensagens para o RabbitMQ em rajada única
        
        Args:
            count: Número de mensagens para enviar
            size: Tamanho de cada mensagem em bytes
            rps: Rate limiting
        """
        try:
            self.metrics.start_timing()
            
            # Conectar ao RabbitMQ
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=self.config["host"],
                    port=self.config["port"],
                    credentials=pika.PlainCredentials(
                        self.config["username"], 
                        self.config["password"]
                    ),
                )
            )
            channel = connection.channel()
            
            # Declarar fila (Quorum Queue para alta disponibilidade)
            channel.queue_declare(
                queue=self.config["queue"],
                durable=True,
                arguments={
                    "x-queue-type": "quorum"  # Usar Quorum Queue (RabbitMQ 4.1.1)
                }
            )
            
            self.logger.info(f"Produtor RabbitMQ conectado. Enviando {count} mensagens...")
            
            # Gerar payload com tamanho especificado
            payload = "x" * max(0, size - 50)  # Descontar overhead do JSON
            
            # Enviar mensagens em rajada
            for i in range(count):
                msg_id = f"msg_{i+1}"
                
                # Mensagem com timestamp embutido
                message = {
                    "id": msg_id,
                    "timestamp": time.time(),  # Timestamp do envio
                    "body": payload
                }
                
                try:
                    # Enviar mensagem
                    channel.basic_publish(
                        exchange="",
                        routing_key=self.config["queue"],
                        body=json.dumps(message),
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # Mensagem persistente
                        )
                    )
                    
                    # Log a cada 1000 mensagens
                    if (i + 1) % 1000 == 0:
                        self.logger.info(f"Enviadas {i+1}/{count} mensagens")
                    
                    # Registrar métrica
                    self.metrics.messages_sent += 1
                    
                except pika.exceptions.AMQPError as e:
                    self.logger.error(f"Erro ao enviar mensagem {msg_id}: {e}")
                    continue
            
            # Fechar conexão
            connection.close()
            
            # Finalizar métricas
            self.metrics.end_timing()
            self.metrics.save_summary()
            
            self.logger.info(f"{self.metrics.messages_sent} mensagens enviadas com sucesso")
            
            return self.metrics.messages_sent == count
            
        except Exception as e:
            self.logger.error(f"Erro no produtor RabbitMQ: {e}")
            return False