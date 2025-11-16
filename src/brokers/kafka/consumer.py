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
        # Tentar múltiplas vezes se o arquivo não existir (produtores podem estar salvando)
        max_retries = 20
        retry_delay = 1.0
        
        for attempt in range(max_retries):
            try:
                # Tentar carregar arquivo específico primeiro
                send_times_file = (
                    self.metrics.metrics_dir / f"{self.metrics.timestamp}_send_times.json"
                )
                if send_times_file.exists():
                    with open(send_times_file, "r") as f:
                        self.send_times = json.load(f)
                    self.logger.info(f"Send_times carregado do arquivo específico: {len(self.send_times)} timestamps")
                    return

                # Se não existir, buscar TODOS os arquivos send_times e consolidá-los
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
                                if content.startswith('{}{'):
                                    # Pegar o último objeto JSON válido (o mais completo)
                                    # Procurar por todos os pares de chaves
                                    brace_count = 0
                                    last_brace = -1
                                    start_brace = -1
                                    for i, char in enumerate(content):
                                        if char == '{':
                                            if brace_count == 0:
                                                start_brace = i
                                            brace_count += 1
                                        elif char == '}':
                                            brace_count -= 1
                                            if brace_count == 0:
                                                last_brace = i
                                    if start_brace >= 0 and last_brace > start_brace:
                                        content = content[start_brace:last_brace+1]
                                    else:
                                        # Fallback: pegar o último objeto
                                        last_brace = content.rfind('}')
                                        if last_brace > 0:
                                            content = content[content.rfind('{', 0, last_brace):last_brace+1]
                                # Parsear JSON
                                file_data = json.loads(content)
                                # Fazer merge (arquivos mais recentes sobrescrevem)
                                if isinstance(file_data, dict):
                                    consolidated_send_times.update(file_data)
                        except (json.JSONDecodeError, ValueError) as e:
                            self.logger.warning(f"Erro ao fazer parse do JSON em {file_path}: {e}")
                            continue
                    
                    self.send_times = consolidated_send_times
                    self.logger.info(f"Consolidados {len(send_times_files)} arquivos send_times: {len(self.send_times)} timestamps únicos")
                    return  # Sucesso, sair do loop
                else:
                    # Arquivo não existe ainda, tentar novamente
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        continue
                    else:
                        self.logger.warning(f"Arquivo de tempos de envio não encontrado após {max_retries} tentativas.")
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
            # IMPORTANTE: Usar group_id único por execução para evitar ler mensagens antigas
            import uuid
            unique_group_id = f"{self.config['group_id']}-{uuid.uuid4().hex[:8]}"
            
            # Obter timestamp de início para filtrar apenas mensagens desta execução
            # Assumir que mensagens enviadas nos últimos 5 minutos são desta execução
            start_timestamp = time.time() - 300  # 5 minutos atrás
            
            consumer = KafkaConsumer(
                self.config["topic"],
                bootstrap_servers=self.config["bootstrap_servers"],
                auto_offset_reset="earliest",  # Ler desde o início, mas filtrar por timestamp
                enable_auto_commit=False,  # Desabilitar auto-commit para controle manual
                group_id=unique_group_id,  # Group ID único para evitar conflitos
                value_deserializer=lambda v: json.loads(v.decode("utf-8")),
                # Configurações otimizadas para simular comportamento de Queue Mode
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
                max_poll_records=500,  # Processar em lotes para melhor performance
                fetch_min_bytes=1,
                fetch_max_wait_ms=500,
            )
            
            self.logger.info(f"Consumer criado com group_id: {unique_group_id}, filtrando mensagens após {start_timestamp}")

            self.logger.info(
                f"Aguardando até {expected_count} mensagens em Queue Mode (Share Groups)"
            )
            # Recarregar send_times antes de começar a consumir
            # (os produtores podem ter terminado de salvar após o __init__)
            self._load_send_times()
            self.logger.info(f"Send_times carregados antes de consumir: {len(self.send_times)} timestamps")
            
            # Aguardar um pouco para garantir que os produtores terminaram de enviar
            # e que as mensagens estão disponíveis no broker
            time.sleep(2)
            
            timeout = time.time() + 120  # Aumentar timeout para 120 segundos
            last_message_time = time.time()
            no_message_timeout = 10  # Aumentar timeout de sem mensagens para 10 segundos

            try:
                # Usar polling ao invés de loop infinito para ter controle sobre timeouts
                while time.time() < timeout:
                    # Poll com timeout de 1 segundo
                    message_batch = consumer.poll(timeout_ms=1000)
                    
                    if not message_batch:
                        # Se não houve mensagens, verificar se devemos parar
                        if time.time() - last_message_time > no_message_timeout:
                            self.logger.info(f"✅ Nenhuma mensagem nova por {no_message_timeout}s. Recebidas {len(self.metrics.latencies)} mensagens. Finalizando consumo.")
                            break
                        continue
                    
                    # Processar mensagens do batch
                    for topic_partition, messages in message_batch.items():
                        for message in messages:
                            recv_time = time.time()
                            last_message_time = recv_time
                            
                            if self.metrics.start_time is None:
                                self.metrics.start_timing()

                            msg_id = message.value.get("id")
                            
                            # Filtrar apenas mensagens desta execução (que estão nos send_times)
                            # Se a mensagem não está nos send_times, é uma mensagem antiga - ignorar
                            if msg_id not in self.send_times:
                                # Tentar recarregar send_times uma vez
                                old_count = len(self.send_times)
                                self._load_send_times()
                                new_count = len(self.send_times)
                                if new_count > old_count:
                                    self.logger.info(f"Send_times recarregado: {old_count} -> {new_count} timestamps")
                            
                            # Processar apenas se a mensagem está nos send_times (é desta execução)
                            if msg_id in self.send_times:
                                # Verificar se já processamos esta mensagem (evitar duplicatas)
                                # Criar chave única: msg_id + partition + offset
                                unique_key = f"{msg_id}-{topic_partition.partition}-{message.offset}"
                                
                                # Verificar se já processamos esta mensagem
                                if not hasattr(self, '_processed_messages'):
                                    self._processed_messages = set()
                                
                                if unique_key in self._processed_messages:
                                    self.logger.debug(f"Mensagem {msg_id} (offset {message.offset}) já foi processada, ignorando duplicata")
                                    continue
                                
                                # Marcar como processada
                                self._processed_messages.add(unique_key)
                                
                                latency = recv_time - float(self.send_times[msg_id])
                                self.metrics.record_latency(msg_id, latency)
                                self.logger.info(
                                    f"Mensagem {msg_id} recebida com latência de {latency:.6f} segundos"
                                )
                            else:
                                # Mensagem antiga ou de outra execução - ignorar silenciosamente
                                self.logger.debug(
                                    f"Mensagem {msg_id} ignorada (não está nos send_times desta execução, send_times tem {len(self.send_times)} entradas)"
                                )
                                # Continuar para próxima mensagem sem processar
                                continue

                            # Reconhecimento individual da mensagem
                            try:
                                consumer.commit()
                                self.logger.debug(f"Mensagem {msg_id} reconhecida (acknowledged)")
                            except Exception as e:
                                self.logger.error(f"Erro ao reconhecer mensagem {msg_id}: {e}")

                            # Parar se recebeu todas as mensagens esperadas
                            if len(self.metrics.latencies) >= expected_count:
                                self.logger.info(f"✅ Recebidas {len(self.metrics.latencies)} mensagens esperadas. Finalizando consumo.")
                                break
                    
                    # Verificar se devemos parar após processar o batch
                    if len(self.metrics.latencies) >= expected_count:
                        break
                    
                    # Verificar timeout de sem mensagens
                    if time.time() - last_message_time > no_message_timeout:
                        self.logger.info(f"✅ Nenhuma mensagem nova por {no_message_timeout}s. Recebidas {len(self.metrics.latencies)} mensagens. Finalizando consumo.")
                        break
                
                # Se timeout geral foi atingido
                if time.time() >= timeout:
                    self.logger.warning(f"⏰ Timeout geral atingido. Recebidas {len(self.metrics.latencies)}/{expected_count} mensagens.")

            except Exception as e:
                self.logger.error(f"Erro durante o consumo: {e}")
                return False
            finally:
                consumer.close()
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
