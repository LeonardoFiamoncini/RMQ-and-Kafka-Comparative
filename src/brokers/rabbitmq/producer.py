"""
Implementação do produtor RabbitMQ
"""

import json
import sys
import time
from typing import Optional

import pika

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class RabbitMQProducer(BaseBroker):
    """Implementação do produtor RabbitMQ"""

    def __init__(self):
        super().__init__("rabbitmq")
        self.config = BROKER_CONFIGS["rabbitmq"]

    def send_messages(
        self, count: int, message_size: int, rps: Optional[int] = None, id_offset: int = 0
    ) -> bool:
        """
        Envia mensagens para o RabbitMQ
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

            # Habilitar confirmação de entrega
            channel.confirm_delivery()
            self.logger.info("Confirmação de entrega habilitada")

            message_content = "x" * (message_size - 10)
            successful_deliveries = 0
            failed_deliveries = 0

            # Calcular intervalo de sleep para Rate Limiting
            sleep_interval = 0
            if rps and rps > 0:
                sleep_interval = 1.0 / rps
                self.logger.info(
                    f"Rate Limiting ativado: {rps} RPS (intervalo: {sleep_interval:.6f}s)"
                )

            for i in range(count):
                # Usar offset para garantir IDs únicos entre múltiplos produtores
                msg_id = str(id_offset + i)
                payload = {"id": msg_id, "body": message_content}
                body = json.dumps(payload)

                try:
                    # Publicar mensagem com confirmação de entrega
                    channel.basic_publish(
                        exchange="",
                        routing_key=self.config["queue"],
                        body=body,
                        mandatory=True,
                        properties=pika.BasicProperties(
                            delivery_mode=2,  # Tornar mensagem persistente
                            timestamp=int(time.time()),
                        ),
                    )

                    # Com confirm_delivery() habilitado, se chegou até aqui, a mensagem foi confirmada
                    # Capturar timestamp T1 APÓS a confirmação (precisão melhorada)
                    self.metrics.record_send_time(msg_id, time.time())
                    successful_deliveries += 1
                    self.logger.info(
                        f"Mensagem {msg_id} enviada e confirmada com {message_size} bytes"
                    )

                except pika.exceptions.UnroutableError:
                    failed_deliveries += 1
                    self.logger.error(
                        f"Mensagem {msg_id} não pôde ser roteada (UnroutableError)"
                    )
                except pika.exceptions.NackError:
                    failed_deliveries += 1
                    self.logger.error(
                        f"Mensagem {msg_id} foi rejeitada pelo broker (NackError)"
                    )
                except Exception as e:
                    failed_deliveries += 1
                    self.logger.error(
                        f"Erro inesperado ao enviar mensagem {msg_id}: {e}"
                    )
                    # Não registrar timestamp para mensagens que falharam

                # Rate Limiting: aguardar o intervalo calculado
                if sleep_interval > 0:
                    time.sleep(sleep_interval)

            connection.close()
            self.metrics.end_timing()

            # Log de estatísticas de entrega
            self.logger.info(
                f"Entrega finalizada: {successful_deliveries} sucessos, {failed_deliveries} falhas"
            )

            # Salvar métricas
            additional_metrics = {
                "successful_deliveries": successful_deliveries,
                "failed_deliveries": failed_deliveries,
                "delivery_success_rate": (
                    (successful_deliveries / count * 100) if count > 0 else 0
                ),
            }

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
        """Não implementado para produtor"""
        raise NotImplementedError("Consumo não implementado no produtor")

    def get_leader(self) -> Optional[str]:
        """Identifica o nó líder do cluster RabbitMQ"""
        return self.config["container_names"][0]  # Primeiro nó como líder


def main():
    """Função principal para execução standalone"""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="RabbitMQ Producer")
    parser.add_argument(
        "count", type=int, nargs="?", default=1000, help="Número de mensagens"
    )
    parser.add_argument(
        "size", type=int, nargs="?", default=100, help="Tamanho das mensagens"
    )
    parser.add_argument(
        "rps", type=int, nargs="?", default=None, help="Rate limiting (RPS)"
    )

    args = parser.parse_args()

    producer = RabbitMQProducer()

    try:
        success = producer.send_messages(args.count, args.size, args.rps)
        if success:
            print(f"✅ Envio concluído com sucesso")
        else:
            print(f"❌ Erro no envio")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Interrompido pelo usuário")
        sys.exit(0)


if __name__ == "__main__":
    main()
