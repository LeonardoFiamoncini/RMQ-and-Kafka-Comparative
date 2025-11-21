"""
Implementação simplificada do consumidor Kafka para TCC
"""

import json
import time
import uuid
from typing import Optional

from kafka import KafkaConsumer, TopicPartition
from kafka.errors import KafkaError

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class KafkaConsumerBroker(BaseBroker):
    """Consumidor Kafka simplificado - mede latência real sem dependências"""

    def __init__(self, run_id: Optional[str] = None):
        super().__init__("kafka", run_id=run_id)
        self.config = BROKER_CONFIGS["kafka"]
        self.run_id = run_id  # Guardar run_id para filtrar mensagens
    
    def send_messages(self, count: int, message_size: int, rps: Optional[int] = None) -> bool:
        """Método não usado por consumidores - apenas para compatibilidade com BaseBroker"""
        return True
    
    def consume_messages(self, expected_count: int, **kwargs) -> bool:
        """
        Consome mensagens do Kafka de forma simples e eficiente
        
        Args:
            expected_count: Número de mensagens esperadas
        """
        try:
            self.metrics.start_timing()
            
            # Timestamp de início para filtrar mensagens antigas
            # Subtrair 2 segundos para capturar mensagens enviadas logo após o consumidor iniciar
            start_timestamp = time.time() - 2.0
            
            # Group ID único para cada execução
            unique_group_id = f"{self.config['group_id']}-{uuid.uuid4().hex[:8]}"
            
            # Configuração do consumidor otimizada para baixa latência
            consumer = KafkaConsumer(
                self.config["topic"],
                bootstrap_servers=self.config["bootstrap_servers"],
                group_id=unique_group_id,
                auto_offset_reset="earliest",  # Ler desde o início para não perder mensagens
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                enable_auto_commit=True,
                max_poll_records=100,  # Menos records por poll para processar mais rápido
                fetch_min_bytes=1,  # Não aguardar acumular dados
                fetch_max_wait_ms=10,  # Tempo mínimo de espera para reduzir latência
                session_timeout_ms=30000,
                request_timeout_ms=31000,
            )
            
            self.logger.info(f"✅ Consumidor Kafka conectado ao tópico {self.config['topic']}")
            
            # Subscribe to the topic
            consumer.subscribe([self.config["topic"]])
            
            # Fazer um poll inicial para garantir que estamos conectados
            consumer.poll(timeout_ms=100)
            
            received_count = 0
            latencies = []
            valid_messages = 0
            start_time = time.time()
            timeout = max(60, expected_count / 50)  # Timeout dinâmico
            empty_polls = 0
            max_empty_polls = 20  # Aumentar para dar mais tempo
            
            self.logger.info(f"Aguardando {expected_count} mensagens (run_id: {self.run_id})...")
            
            # Consumir mensagens
            while received_count < expected_count:
                # Verificar timeout
                if time.time() - start_time > timeout:
                    self.logger.warning(f"Timeout após {timeout}s. Recebidas {received_count}/{expected_count}")
                    break
                
                # Poll por mensagens
                messages = consumer.poll(timeout_ms=500)  # Poll mais frequente
                
                if not messages:
                    empty_polls += 1
                    if empty_polls > max_empty_polls and received_count == 0:
                        self.logger.warning(f"Nenhuma mensagem recebida após {max_empty_polls} tentativas")
                        break
                    # Aguardar um pouco mais se ainda não recebemos mensagens
                    if received_count == 0:
                        time.sleep(0.1)
                    continue
                else:
                    empty_polls = 0  # Reset counter se recebemos mensagens
                
                # Processar mensagens recebidas
                for topic_partition, records in messages.items():
                    for message in records:
                        try:
                            # Calcular latência
                            current_time = time.time()
                            msg_data = message.value
                            
                            # Processar apenas mensagens com estrutura válida
                            if isinstance(msg_data, dict):
                                # Verificar run_id se presente
                                msg_run_id = msg_data.get("run_id", "")
                                
                                # Se a mensagem tem run_id e não corresponde, pular
                                if msg_run_id and self.run_id and msg_run_id != self.run_id:
                                    continue
                                
                                # Verificar timestamp
                                if "timestamp" in msg_data:
                                    send_time = msg_data["timestamp"]
                                    
                                    # FILTRO CRÍTICO: Apenas mensagens enviadas APÓS o início desta execução
                                    if send_time < start_timestamp - 1:  # -1 segundo de tolerância
                                        continue  # Mensagem de execução anterior
                                    
                                    latency = current_time - send_time
                                    
                                    # Validar latência (máximo 30 segundos)
                                    if 0 <= latency <= 30:
                                        latencies.append(latency)
                                        self.metrics.record_latency(latency, str(received_count + 1))
                                        valid_messages += 1
                                    else:
                                        self.logger.debug(f"Latência inválida ignorada: {latency:.3f}s")
                            
                            received_count += 1
                            
                            # Log de progresso
                            if received_count <= 10 or received_count % 100 == 0:
                                self.logger.info(f"Recebidas {received_count}/{expected_count} mensagens (válidas: {valid_messages})")
                            
                            if received_count >= expected_count:
                                break
                                
                        except Exception as e:
                            self.logger.warning(f"Erro ao processar mensagem: {e}")
                            continue
                    
                    if received_count >= expected_count:
                        break
            
            # Fechar consumidor
            consumer.close()
            
            # Finalizar métricas
            self.metrics.end_timing()
            self.metrics.messages_consumed = valid_messages  # Usar apenas mensagens válidas
            self.metrics.save_latencies()
            self.metrics.save_summary()
            
            # Log resumo
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                self.logger.info(f"📊 Latência média: {avg_latency:.3f}s")
                
                # Alertar se latência média está muito alta
                if avg_latency > 1.0:
                    self.logger.warning(f"⚠️ Latência média muito alta: {avg_latency:.3f}s - possível consumo de mensagens antigas!")
            
            self.logger.info(f"✅ Consumo finalizado: {valid_messages} mensagens válidas recebidas de {received_count} total")
            
            return valid_messages >= expected_count
            
        except Exception as e:
            self.logger.error(f"❌ Erro no consumidor Kafka: {e}")
            return False