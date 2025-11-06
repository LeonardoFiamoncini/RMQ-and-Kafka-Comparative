"""
Cliente HTTP baseline para comparação síncrona
"""

import time
from typing import Optional

import sys

import requests

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class BaselineClient(BaseBroker):
    """Cliente HTTP baseline para comparação síncrona"""

    def __init__(self):
        super().__init__("baseline")
        self.config = BROKER_CONFIGS["baseline"]
        self.base_url = f"http://{self.config['host']}:{self.config['port']}"

    def send_messages(
        self, count: int, message_size: int, rps: Optional[int] = None
    ) -> bool:
        """
        Envia mensagens HTTP para o servidor baseline
        """
        try:
            # Inicializar métricas
            self.metrics.start_timing()

            message_content = "x" * (message_size - 10)
            successful_requests = 0
            failed_requests = 0

            # Calcular intervalo de sleep para Rate Limiting
            sleep_interval = 0
            if rps and rps > 0:
                sleep_interval = 1.0 / rps
                self.logger.info(
                    f"Rate Limiting ativado: {rps} RPS (intervalo: {sleep_interval:.6f}s)"
                )

            # Verificar se o servidor está rodando
            try:
                health_response = requests.get(f"{self.base_url}/health", timeout=5)
                if health_response.status_code != 200:
                    self.logger.error(
                        f"Servidor não está saudável: {health_response.status_code}"
                    )
                    return False
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Servidor não está acessível: {e}")
                return False

            for i in range(count):
                msg_id = str(i)
                payload = {"id": msg_id, "body": message_content}

                try:
                    # Capturar timestamp ANTES de enviar (T1)
                    send_time = time.time()
                    self.metrics.record_send_time(msg_id, send_time)
                    
                    response = requests.post(
                        f"{self.base_url}{self.config['endpoint']}",
                        json=payload,
                        timeout=5,
                    )
                    
                    # Capturar timestamp APÓS receber resposta (T2)
                    recv_time = time.time()
                    
                    if response.status_code == 200:
                        successful_requests += 1
                        # Calcular latência: tempo de resposta HTTP (T2 - T1)
                        # Para baseline síncrono, a latência é o tempo total da requisição
                        latency = recv_time - send_time
                        self.metrics.record_latency(msg_id, latency)
                        processing_time = response.json().get('processing_time', 0)
                        self.logger.info(
                            f"Mensagem {msg_id} enviada com sucesso - "
                            f"Latência total: {latency:.6f}s, "
                            f"Tempo de processamento servidor: {processing_time:.6f}s"
                        )
                    else:
                        failed_requests += 1
                        self.logger.error(
                            f"Falha ao enviar mensagem {msg_id}: Status {response.status_code}, Resposta: {response.text}"
                        )
                except requests.exceptions.Timeout:
                    failed_requests += 1
                    self.logger.error(f"Timeout ao enviar mensagem {msg_id}")
                except requests.exceptions.ConnectionError as e:
                    failed_requests += 1
                    self.logger.error(
                        f"Erro de conexão ao enviar mensagem {msg_id}: {e}"
                    )
                except Exception as e:
                    failed_requests += 1
                    self.logger.error(
                        f"Erro inesperado ao enviar mensagem {msg_id}: {e}"
                    )

                # Rate Limiting: aguardar o intervalo calculado
                if sleep_interval > 0:
                    time.sleep(sleep_interval)

            self.metrics.end_timing()

            self.logger.info(
                f"Envio finalizado: {successful_requests} sucessos, {failed_requests} falhas"
            )

            # Salvar métricas
            additional_metrics = {
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
            }

            if rps:
                additional_metrics["target_rps"] = rps
                duration = (
                    self.metrics.end_time - self.metrics.start_time
                    if self.metrics.start_time and self.metrics.end_time
                    else 0
                )
                actual_rps = successful_requests / duration if duration > 0 else 0
                additional_metrics["actual_rps"] = actual_rps

            self.save_metrics(additional_metrics)
            return True

        except Exception as e:
            self.logger.error(f"Erro no envio de mensagens: {e}")
            return False

    def consume_messages(self, expected_count: int) -> bool:
        """Não implementado para cliente baseline"""
        raise NotImplementedError("Consumo não implementado no cliente baseline")

    def get_leader(self) -> Optional[str]:
        """Baseline não tem conceito de líder"""
        return None


def main():
    """Função principal para execução standalone"""
    import argparse

    parser = argparse.ArgumentParser(description="Baseline HTTP Client")
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

    client = BaselineClient()

    try:
        success = client.send_messages(args.count, args.size, args.rps)
        if success:
            print("✅ Envio concluído com sucesso")
        else:
            print("❌ Erro no envio")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n[!] Interrompido pelo usuário")
        sys.exit(0)


if __name__ == "__main__":
    main()
