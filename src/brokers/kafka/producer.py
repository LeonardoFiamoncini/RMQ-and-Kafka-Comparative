"""
Implementação do produtor Kafka.

Este módulo implementa o produtor Kafka com suporte a Queue Mode (KIP-932)
e configurações otimizadas para benchmarks de performance.
"""

from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
import time
import json
from typing import Optional
from ..base import BaseBroker
from ...core.config import BROKER_CONFIGS


class KafkaProducerBroker(BaseBroker):
    """Implementação do produtor Kafka."""

    def __init__(self):
        """Inicializa o produtor Kafka."""
        super().__init__("kafka")
        self.config = BROKER_CONFIGS["kafka"]

    def create_topic_for_queue_mode(
        self,
        topic_name: str = None,
        num_partitions: int = 3,
        replication_factor: int = 1,
    ) -> bool:
        """
        Cria um tópico configurado para Queue Mode (Share Groups) do Kafka 4.0.

        Args:
            topic_name: Nome do tópico
            num_partitions: Número de partições
            replication_factor: Fator de replicação

        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        if topic_name is None:
            topic_name = self.config["topic"]

        try:
            admin_client = KafkaAdminClient(
                bootstrap_servers=self.config["bootstrap_servers"],
                client_id="queue_mode_admin",
            )

            # Verificar se o tópico já existe
            existing_topics = admin_client.list_topics()
            if topic_name in existing_topics:
                self.logger.info(f"Tópico {topic_name} já existe")
                admin_client.close()
                return True

            # Criar novo tópico com configurações para Queue Mode
            topic = NewTopic(
                name=topic_name,
                num_partitions=num_partitions,
                replication_factor=replication_factor,
                topic_configs={
                    # Configurações específicas para Queue Mode/Share Groups
                    "cleanup.policy": "delete",
                    "retention.ms": "604800000",  # 7 dias
                    "segment.ms": "604800000",  # 7 dias
                    "compression.type": "gzip",
                },
            )

            # Criar o tópico
            fs = admin_client.create_topics([topic])
            try:
                # Aguardar a criação do tópico
                for topic_name, f in fs.items():
                    f.result()  # Aguardar a criação
                    self.logger.info(
                        f"Tópico {topic_name} criado com sucesso para Queue Mode"
                    )
            except Exception as e:
                self.logger.error(f"Erro ao criar tópico {topic_name}: {e}")
                return False

            admin_client.close()
            return True

        except Exception as e:
            self.logger.error(f"Erro na criação do tópico: {e}")
            return False

    def send_messages(
        self, count: int, message_size: int, rps: Optional[int] = None, id_offset: int = 0
    ) -> bool:
        """
        Envia mensagens para o Kafka.

        Args:
            count: Número de mensagens
            message_size: Tamanho de cada mensagem em bytes
            rps: Rate limiting (mensagens por segundo)

        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        try:
            # Criar tópico para Queue Mode antes de enviar mensagens
            if not self.create_topic_for_queue_mode():
                self.logger.error("Falha ao criar tópico para Queue Mode")
                return False

            # Inicializar métricas
            self.metrics.start_timing()

            producer = KafkaProducer(
                bootstrap_servers=self.config["bootstrap_servers"],
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                acks="all",  # Confirmação de todos os brokers
                # Configurações específicas para Queue Mode
                retries=3,
                retry_backoff_ms=100,
                max_in_flight_requests_per_connection=1,  # Garantir ordenação
            )

            message_content = "x" * (message_size - 10)

            # Calcular intervalo de sleep para Rate Limiting
            sleep_interval = 0
            if rps and rps > 0:
                sleep_interval = 1.0 / rps
                self.logger.info(
                    f"Rate Limiting ativado: {rps} RPS "
                    f"(intervalo: {sleep_interval:.6f}s)"
                )

            for i in range(count):
                # Usar offset para garantir IDs únicos entre múltiplos produtores
                msg_id = str(id_offset + i)
                payload = {"id": msg_id, "body": message_content}

                # Enviar mensagem e aguardar confirmação
                future = producer.send(self.config["topic"], value=payload)
                try:
                    # Aguardar confirmação do broker
                    future.get(timeout=10)

                    # Capturar timestamp T1 APÓS a confirmação (precisão melhorada)
                    self.metrics.record_send_time(msg_id, time.time())
                    self.logger.info(
                        f"Mensagem {msg_id} enviada e confirmada com "
                        f"{message_size} bytes"
                    )
                except Exception as e:
                    self.logger.error(f"Falha ao enviar mensagem {msg_id}: {e}")
                    # Não registrar timestamp para mensagens que falharam

                # Rate Limiting: aguardar o intervalo calculado
                if sleep_interval > 0:
                    time.sleep(sleep_interval)

            producer.flush()
            self.metrics.end_timing()

            # Salvar métricas
            additional_metrics = {}
            if rps:
                additional_metrics["target_rps"] = rps
                duration = (
                    self.metrics.end_time - self.metrics.start_time
                    if self.metrics.start_time and self.metrics.end_time
                    else 0
                )
                actual_rps = count / duration if duration > 0 else 0
                additional_metrics["actual_rps"] = actual_rps

            self.save_metrics(additional_metrics)
            return True

        except Exception as e:
            self.logger.error(f"Erro no envio de mensagens: {e}")
            return False

    def consume_messages(self, expected_count: int) -> bool:
        """Não implementado para produtor."""
        raise NotImplementedError("Consumo não implementado no produtor")

    def get_leader(self) -> Optional[str]:
        """Identifica o nó líder do cluster Kafka."""
        return self.config["container_name"]  # Para cluster de 1 nó
