"""
Implementação do consumidor RabbitMQ
"""

import glob
import json
import os
import signal
import sys
import time
from typing import Optional

import pika

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class RabbitMQConsumer(BaseBroker):
    """Implementação do consumidor RabbitMQ"""

    def __init__(self):
        super().__init__("rabbitmq")
        self.config = BROKER_CONFIGS["rabbitmq"]
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

    def _callback(self, ch, method, properties, body):
        """Callback para processar mensagens recebidas"""
        recv_time = time.time()
        if self.metrics.start_time is None:
            self.metrics.start_timing()

        try:
            msg = json.loads(body.decode("utf-8"))
            msg_id = msg.get("id")
        except Exception as e:
            self.logger.error(f"Falha ao decodificar mensagem: {e}")
            # Rejeitar mensagem malformada (nack)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return

        try:
            # Processar mensagem
            if msg_id in self.send_times:
                latency = recv_time - float(self.send_times[msg_id])
                self.metrics.record_latency(msg_id, latency)
                self.logger.info(
                    f"Mensagem {msg_id} recebida com latência de {latency:.6f} segundos"
                )
            else:
                self.logger.warning(
                    f"Mensagem {msg_id} recebida sem timestamp correspondente"
                )

            # Confirmar processamento bem-sucedido (ack)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            self.logger.debug(f"Mensagem {msg_id} confirmada (ack)")

        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem {msg_id}: {e}")
            # Rejeitar mensagem com erro (nack) - pode ser reprocessada
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def consume_messages(self, expected_count: int) -> bool:
        """
        Consome mensagens do RabbitMQ
        """
        try:
            # Inicializar métricas
            self.metrics.start_timing()

            credentials = pika.PlainCredentials(
                self.config["username"], self.config["password"]
            )
            parameters = pika.ConnectionParameters(
                self.config["host"], self.config["port"], "/", credentials
            )

            connection = pika.BlockingConnection(parameters)
            channel = connection.channel()
            channel.queue_declare(
                queue=self.config["queue"],
                durable=True,
                arguments={"x-queue-type": "quorum"},
            )

            channel.basic_consume(
                queue=self.config["queue"],
                on_message_callback=self._callback,
                auto_ack=False,
            )

            self.logger.info(
                f"Aguardando até {expected_count} mensagens. Pressione CTRL+C para sair"
            )

            try:
                # Consumir mensagens até atingir o limite ou timeout
                timeout = time.time() + 60  # Timeout de 60 segundos
                while (
                    len(self.metrics.latencies) < expected_count
                    and time.time() < timeout
                ):
                    connection.process_data_events(time_limit=1)

            except KeyboardInterrupt:
                self.logger.info("Interrompido pelo usuário")
            finally:
                channel.stop_consuming()
                connection.close()
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
        """Identifica o nó líder do cluster RabbitMQ"""
        return self.config["container_names"][0]  # Primeiro nó como líder


def main():
    """Função principal para execução standalone"""
    import argparse

    parser = argparse.ArgumentParser(description="RabbitMQ Consumer")
    parser.add_argument(
        "expected_count",
        type=int,
        nargs="?",
        default=1000,
        help="Número esperado de mensagens",
    )

    args = parser.parse_args()

    consumer = RabbitMQConsumer()

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
