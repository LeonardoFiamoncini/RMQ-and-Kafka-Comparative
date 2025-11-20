"""
Implementação do consumidor RabbitMQ
"""

import glob
import json
import os
import signal
import sys
import time
from threading import Event
from typing import Optional

import pika

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class RabbitMQConsumer(BaseBroker):
    """Implementação do consumidor RabbitMQ"""

    def __init__(self, run_id: Optional[str] = None):
        super().__init__("rabbitmq", run_id=run_id)
        self.config = BROKER_CONFIGS["rabbitmq"]
        self.send_times = {}
        self.send_times_event = None  # Event para aguardar send_times
        self.send_times_loaded = False  # Flag para carregar apenas uma vez
        # NÃO carregar send_times no __init__, aguardar Event

    def _load_send_times(self):
        """Carrega os tempos de envio do arquivo mais recente"""
        # Tentar múltiplas vezes se o arquivo não existir (produtores podem estar salvando)
        max_retries = 20  # Aumentar tentativas
        retry_delay = 1.0  # Aumentar delay para 1 segundo
        
        for attempt in range(max_retries):
            try:
                # Buscar TODOS os arquivos send_times e consolidá-los
                # (múltiplos produtores podem ter criado arquivos separados)
                send_times_files = glob.glob(
                    str(self.metrics.metrics_dir / "*_send_times.json")
                )
                if send_times_files:
                    # Ordenar por mtime (mais recente primeiro)
                    send_times_files.sort(key=os.path.getmtime, reverse=True)

                    # Consolidar todos os arquivos send_times (de múltiplos produtores)
                    consolidated_send_times = {}
                    for file_path in send_times_files:
                        try:
                            with open(file_path, "r") as f:
                                content = f.read().strip()
                                # Tentar corrigir JSON malformado (pode ter múltiplos objetos)
                                # Se começar com {}{, significa que há múltiplos objetos JSON
                                if content.startswith("{}{"):
                                    # Pegar o último objeto JSON válido (o mais completo)
                                    # Procurar por todos os pares de chaves
                                    brace_count = 0
                                    last_brace = -1
                                    start_brace = -1
                                    for i, char in enumerate(content):
                                        if char == "{":
                                            if brace_count == 0:
                                                start_brace = i
                                            brace_count += 1
                                        elif char == "}":
                                            brace_count -= 1
                                            if brace_count == 0:
                                                last_brace = i
                                    if start_brace >= 0 and last_brace > start_brace:
                                        content = content[start_brace : last_brace + 1]
                                    else:
                                        # Fallback: pegar o último objeto
                                        last_brace = content.rfind("}")
                                        if last_brace > 0:
                                            content = content[
                                                content.rfind("{", 0, last_brace) : last_brace + 1
                                            ]
                                # Parsear JSON
                                file_data = json.loads(content)
                                # Fazer merge (arquivos mais recentes sobrescrevem)
                                if isinstance(file_data, dict):
                                    consolidated_send_times.update(file_data)
                        except (json.JSONDecodeError, ValueError) as e:
                            self.logger.warning(
                                f"Erro ao fazer parse do JSON em {file_path}: {e}"
                            )
                            continue

                    self.send_times = consolidated_send_times
                    self.logger.info(
                        f"Consolidados {len(send_times_files)} arquivos send_times: {len(self.send_times)} timestamps únicos"
                    )
                    return  # Sucesso, sair do loop de retry
                else:
                    # Arquivo não existe ainda, tentar novamente
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        self.logger.warning(
                            f"Arquivo de tempos de envio não encontrado após {max_retries} tentativas."
                        )
                        self.send_times = {}
                        return
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.debug(f"Erro ao carregar send_times (tentativa {attempt+1}/{max_retries}): {e}")
                    time.sleep(retry_delay)
                    continue
                else:
                    self.logger.error(f"Erro ao carregar tempos de envio após {max_retries} tentativas: {e}")
                    self.send_times = {}
                    return

    def _callback(self, ch, method, properties, body):
        """
        Callback para processar mensagens recebidas
        
        CORRIGIDO: Aguarda send_times estarem disponíveis antes de calcular latência.
        Isso não bloqueia o recebimento de mensagens, apenas o cálculo de latência.
        """
        recv_time = time.time()  # T2: Capturar IMEDIATAMENTE ao receber
        
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
            # CORRIGIDO: Aguardar send_times estarem disponíveis
            # (aguarda Event apenas na primeira vez)
            if not self.send_times_loaded:
                # Tentar carregar send_times (com retry ativo)
                self._load_send_times()
                
                # Se ainda não temos send_times, aguardar Event se disponível
                if not self.send_times and self.send_times_event is not None:
                    self.logger.debug("Send_times vazio, aguardando Event...")
                    self.send_times_event.wait(timeout=120)
                    self._load_send_times()
                
                self.send_times_loaded = True
                self.logger.info(f"Send_times carregados: {len(self.send_times)} timestamps")
            
            # Se não encontrar o timestamp, tentar recarregar
            if msg_id not in self.send_times:
                self.logger.debug(f"Timestamp não encontrado para {msg_id}, recarregando...")
                old_count = len(self.send_times)
                self._load_send_times()
                new_count = len(self.send_times)
                if new_count > old_count:
                    self.logger.info(f"Send_times recarregado: {old_count} -> {new_count} timestamps")
            
            # Processar mensagem
            if msg_id in self.send_times:
                latency = recv_time - float(self.send_times[msg_id])
                
                # CORRIGIDO: Tratar latências muito pequenas/negativas (erro de precisão)
                # Latências negativas ou < 1 microssegundo são tratadas como 0
                if latency < 0.000001:  # < 1 microssegundo
                    if latency < 0:
                        self.logger.debug(
                            f"Latência negativa detectada para msg_id {msg_id}: {latency:.9f}s "
                            f"(erro de precisão de timestamp). Ajustando para 0.000001s"
                        )
                    latency = max(0.000001, latency)  # Mínimo de 1 microssegundo
                
                self.metrics.record_latency(msg_id, latency)
                self.logger.info(
                    f"Mensagem {msg_id} recebida com latência de {latency:.6f} segundos"
                )
                # Confirmar processamento bem-sucedido (ack)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                self.logger.debug(f"Mensagem {msg_id} confirmada (ack)")
            else:
                self.logger.warning(
                    f"Mensagem {msg_id} recebida sem timestamp correspondente (send_times tem {len(self.send_times)} entradas); reenfileirando para aguardar send_times."
                )
                # Reenfileirar mensagem para ser processada quando send_times estiver disponível
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                return

        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem {msg_id}: {e}")
            # Rejeitar mensagem com erro (nack) - pode ser reprocessada
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def consume_messages(self, expected_count: int, send_times_event: Optional['Event'] = None) -> bool:
        """
        Consome mensagens do RabbitMQ
        
        CORRIGIDO: Consumidor inicia IMEDIATAMENTE e processa mensagens conforme chegam.
        O Event é usado apenas para aguardar send_times serem salvos (para cálculo de latência).
        
        Args:
            expected_count: Número de mensagens esperadas
            send_times_event: Event para sinalizar que send_times estão disponíveis
        """
        try:
            # Armazenar Event para uso no callback
            self.send_times_event = send_times_event
            
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
                # Timeout global de 60 segundos OU timeout de inatividade de 10 segundos
                global_timeout = time.time() + 60
                last_message_time = time.time()
                inactivity_timeout = 10  # Segundos sem receber mensagens
                
                while len(self.metrics.latencies) < expected_count:
                    # Verificar timeout global
                    if time.time() >= global_timeout:
                        self.logger.warning(f"Timeout global atingido após 60s")
                        break
                    
                    # Verificar timeout de inatividade
                    if time.time() - last_message_time >= inactivity_timeout:
                        self.logger.info(
                            f"Timeout de inatividade: {inactivity_timeout}s sem novas mensagens. "
                            f"Recebidas {len(self.metrics.latencies)}/{expected_count} mensagens."
                        )
                        break
                    
                    # Armazenar contagem anterior para detectar novas mensagens
                    previous_count = len(self.metrics.latencies)
                    connection.process_data_events(time_limit=1)
                    
                    # Se recebemos novas mensagens, atualizar timestamp
                    if len(self.metrics.latencies) > previous_count:
                        last_message_time = time.time()

            except KeyboardInterrupt:
                self.logger.info("Interrompido pelo usuário")
            finally:
                channel.stop_consuming()
                connection.close()
                self.metrics.end_timing()
                
                # Salvar métricas apenas se houver latências coletadas
                # (evitar salvar arquivos vazios que sobrescrevem arquivos com dados)
                if len(self.metrics.latencies) > 0:
                    self.logger.info(f"Salvando {len(self.metrics.latencies)} latências coletadas")
                    self.save_metrics()
                else:
                    self.logger.warning("Nenhuma latência coletada, não salvando métricas vazias")

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
