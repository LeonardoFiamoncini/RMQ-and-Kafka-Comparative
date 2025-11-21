"""
Implementação simplificada do produtor Kafka para TCC
"""

import json
import time
import uuid
from typing import Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class KafkaProducerBroker(BaseBroker):
    """Produtor Kafka simplificado - envia mensagens com timestamp embutido"""

    def __init__(self, run_id: Optional[str] = None):
        super().__init__("kafka", run_id=run_id)
        self.config = BROKER_CONFIGS["kafka"].copy()
        self.run_id = run_id  # Guardar run_id para usar nas mensagens
        # Usar sempre o tópico padrão para compatibilidade com consumidor
        # self.config["topic"] permanece como "bcc-tcc"

    def send_messages(
        self, count: int, size: int, rps: Optional[int] = None, **kwargs
    ) -> bool:
        """
        Envia mensagens para o Kafka em rajada única
        
        Args:
            count: Número de mensagens para enviar
            size: Tamanho de cada mensagem em bytes
            rps: Rate limiting (não usado - sempre rajada)
        """
        try:
            self.metrics.start_timing()
            
            # Configuração balanceada do produtor
            producer = KafkaProducer(
                bootstrap_servers=self.config["bootstrap_servers"],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks=1,  # Aguardar confirmação do líder para garantir entrega
                compression_type=None,  # Sem compressão para comparação justa
                batch_size=1024,  # Batch pequeno para reduzir latência
                linger_ms=10,  # Pequeno delay para permitir batching mínimo
                max_in_flight_requests_per_connection=5,  # Permitir paralelismo
            )
            
            self.logger.info(f"✅ Produtor Kafka conectado. Enviando {count} mensagens...")
            
            # Gerar payload com tamanho especificado
            payload = "x" * max(0, size - 50)  # Descontar overhead do JSON
            
            # Enviar mensagens em rajada
            futures = []
            for i in range(count):
                msg_id = f"msg_{i+1}"
                
                # Mensagem com timestamp embutido e run_id
                message = {
                    "id": msg_id,
                    "run_id": self.run_id,  # Identificador único da execução
                    "timestamp": time.time(),  # Timestamp do envio
                    "body": payload
                }
                
                try:
                    # Enviar mensagem de forma assíncrona
                    future = producer.send(self.config["topic"], value=message)
                    futures.append(future)
                    
                    # Log a cada 1000 mensagens
                    if (i + 1) % 1000 == 0:
                        self.logger.info(f"Enviadas {i+1}/{count} mensagens")
                    
                    # Registrar métrica
                    self.metrics.messages_sent += 1
                    
                except KafkaError as e:
                    self.logger.error(f"Erro ao enviar mensagem {msg_id}: {e}")
                    continue
            
            # Garantir que todas as mensagens foram enviadas
            producer.flush(timeout=30)
            
            # Verificar se todas as mensagens foram enviadas com sucesso
            success_count = 0
            for future in futures:
                try:
                    future.get(timeout=1)
                    success_count += 1
                except Exception as e:
                    self.logger.warning(f"Erro ao confirmar envio: {e}")
            
            self.logger.info(f"✅ {success_count}/{count} mensagens confirmadas")
            
            producer.close()
            
            # Finalizar métricas
            self.metrics.end_timing()
            self.metrics.save_summary()
            
            self.logger.info(f"✅ {self.metrics.messages_sent} mensagens enviadas com sucesso")
            
            return self.metrics.messages_sent == count
            
        except Exception as e:
            self.logger.error(f"❌ Erro no produtor Kafka: {e}")
            return False