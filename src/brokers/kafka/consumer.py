"""
Implementação do consumidor Kafka
"""

import glob
import json
import os
import signal
import sys
import time
from typing import Optional

from kafka import KafkaConsumer

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class KafkaConsumerBroker(BaseBroker):
    """Implementação do consumidor Kafka"""

    def __init__(self):
        super().__init__("kafka")
        self.config = BROKER_CONFIGS["kafka"]
        self.send_times = {}
        self._load_send_times()

    def _load_send_times(self):
        """Carrega os tempos de envio do arquivo mais recente"""
        try:
            # Tentar carregar arquivo específico primeiro
            send_times_file = (
                self.metrics.metrics_dir / f"{self.metrics.timestamp}_send_times.json"
            )
            if send_times_file.exists():
                with open(send_times_file, "r") as f:
                    self.send_times = json.load(f)
                return

            # Se não existir, buscar o arquivo mais recente
            send_times_files = glob.glob(
                str(self.metrics.metrics_dir / "*_send_times.json")
            )
            if send_times_files:
                latest_file = max(send_times_files, key=os.path.getctime)
                with open(latest_file, "r") as f:
                    self.send_times = json.load(f)
                self.logger.info(f"Usando arquivo de tempos: {latest_file}")
            else:
                self.logger.error("Arquivo de tempos de envio não encontrado.")
                self.send_times = {}
        except Exception as e:
            self.logger.error(f"Erro ao carregar tempos de envio: {e}")
            self.send_times = {}

    def consume_messages(self, expected_count: int) -> bool:
        """
        Consome mensagens do Kafka
        """
        try:
            # Inicializar métricas
            self.metrics.start_timing()

            # Configuração para Queue Mode (Share Groups) - KIP-932
            # Nota: A biblioteca kafka-python ainda não suporta nativamente Share Groups
            # Implementando uma simulação usando consumer groups tradicionais com configurações otimizadas
            consumer = KafkaConsumer(
                self.config["topic"],
                bootstrap_servers=self.config["bootstrap_servers"],
                auto_offset_reset="earliest",
                enable_auto_commit=False,  # Desabilitar auto-commit para controle manual
                group_id=self.config["group_id"],  # Nome específico para Queue Mode
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                # Configurações otimizadas para simular comportamento de Queue Mode
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_records=500,  # Processar em lotes para melhor performance
                fetch_min_bytes=1,
                fetch_max_wait_ms=500,
            )

            self.logger.info(
                f"Aguardando até {expected_count} mensagens em Queue Mode (Share Groups)"
            )
            timeout = time.time() + 60  # Timeout de 60 segundos

            try:
                for message in consumer:
                    recv_time = time.time()
                    if self.metrics.start_time is None:
                        self.metrics.start_timing()

                    msg_id = message.value.get("id")
                    if msg_id in self.send_times:
                        latency = recv_time - float(self.send_times[msg_id])
                        self.metrics.record_latency(msg_id, latency)
                        self.logger.info(
                            f"Mensagem {msg_id} recebida com latência de {latency:.6f} segundos"
                        )
                    else:
                        self.logger.warning(
                            f"Mensagem {msg_id} recebida sem timestamp de envio"
                        )

                    # Reconhecimento individual da mensagem (específico para Share Groups)
                    try:
                        # Para consumer groups tradicionais, usar commit assíncrono
                        consumer.commit()
                        self.logger.debug(
                            f"Mensagem {msg_id} reconhecida (acknowledged)"
                        )
                    except Exception as e:
                        self.logger.error(f"Erro ao reconhecer mensagem {msg_id}: {e}")

                    if len(self.metrics.latencies) >= expected_count:
                        self.logger.info(f"✅ Recebidas {len(self.metrics.latencies)} mensagens esperadas. Finalizando consumo.")
                        break
                    if time.time() > timeout:
                        self.logger.warning(f"⏰ Timeout atingido. Recebidas {len(self.metrics.latencies)}/{expected_count} mensagens.")
                        break

            except Exception as e:
                self.logger.error(f"Erro durante o consumo: {e}")
                return False
            finally:
                consumer.close()
                self.metrics.end_timing()

            # Salvar métricas
            self.save_metrics()
            return True

        except Exception as e:
            self.logger.error(f"Erro no consumo de mensagens: {e}")
            return False

    def send_messages(
        self, count: int, message_size: int, rps: Optional[int] = None
    ) -> bool:
        """Não implementado para consumidor"""
        raise NotImplementedError("Envio não implementado no consumidor")

    def get_leader(self) -> Optional[str]:
        """Identifica o nó líder do cluster Kafka"""
        return self.config["container_name"]  # Para cluster de 1 nó


def main():
    """Função principal para execução standalone"""
    import argparse

    parser = argparse.ArgumentParser(description="Kafka Consumer")
    parser.add_argument(
        "expected_count",
        type=int,
        nargs="?",
        default=1000,
        help="Número esperado de mensagens",
    )

    args = parser.parse_args()

    consumer = KafkaConsumerBroker()

    def signal_handler(sig, frame):
        print("\n[!] Interrompido pelo usuário. Salvando resultados...")
        consumer.save_metrics()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        success = consumer.consume_messages(args.expected_count)
        if success:
            print(f"✅ Consumo concluído com sucesso")
        else:
            print(f"❌ Erro no consumo")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Interrompido pelo usuário")
        consumer.save_metrics()
        sys.exit(0)


if __name__ == "__main__":
    main()
