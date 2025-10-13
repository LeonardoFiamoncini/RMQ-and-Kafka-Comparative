"""
Módulo de Chaos Engineering para testes de tolerância a falhas
"""
import time
import subprocess
import threading
from typing import Optional, Dict, Any
from ..core.config import CHAOS_CONFIG, BROKER_CONFIGS
from ..core.logger import Logger
from ..core.metrics import MetricsCollector

class ChaosEngineer:
    """Engenheiro de Chaos para testes de tolerância a falhas"""
    
    def __init__(self):
        self.logger = Logger.get_logger("chaos.engineer")
        self.config = CHAOS_CONFIG
        
    def get_kafka_leader(self) -> Optional[str]:
        """Identifica o nó líder do cluster Kafka"""
        try:
            # Usar kafka-topics.sh para obter informações do cluster
            result = subprocess.run([
                'docker', 'exec', 'kafka', 'kafka-topics.sh',
                '--bootstrap-server', 'localhost:9092',
                '--describe', '--topic', 'bcc-tcc'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Para um cluster de 1 nó, o líder é sempre o próprio kafka
                return 'kafka'
            else:
                self.logger.error(f"Erro ao identificar líder Kafka: {result.stderr}")
                return None
        except Exception as e:
            self.logger.error(f"Erro ao identificar líder Kafka: {e}")
            return None

    def get_rabbitmq_leader(self) -> Optional[str]:
        """Identifica o nó líder do cluster RabbitMQ"""
        try:
            # Verificar qual nó está ativo como líder
            for node_num in [1, 2, 3]:
                container_name = f'rabbitmq-{node_num}'
                try:
                    result = subprocess.run([
                        'docker', 'exec', container_name, 'rabbitmqctl', 'cluster_status'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0 and 'running_nodes' in result.stdout:
                        # Se o comando funcionou, este é um nó ativo
                        # Para simplificar, vamos considerar o primeiro nó como líder
                        return container_name
                except:
                    continue
            
            # Fallback: retornar o primeiro nó
            return 'rabbitmq-1'
        except Exception as e:
            self.logger.error(f"Erro ao identificar líder RabbitMQ: {e}")
            return 'rabbitmq-1'

    def kill_container(self, container_name: str) -> bool:
        """Mata um contêiner Docker"""
        try:
            result = subprocess.run(['docker', 'kill', container_name], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                self.logger.info(f"✅ Contêiner {container_name} foi terminado")
                return True
            else:
                self.logger.error(f"❌ Erro ao terminar contêiner {container_name}: {result.stderr}")
                return False
        except Exception as e:
            self.logger.error(f"❌ Erro ao terminar contêiner {container_name}: {e}")
            return False

    def wait_for_container_recovery(self, container_name: str, max_wait: int = None) -> float:
        """Aguarda um contêiner se recuperar"""
        if max_wait is None:
            max_wait = self.config["max_recovery_wait"]
            
        self.logger.info(f"⏳ Aguardando recuperação do contêiner {container_name}...")
        start_wait = time.time()
        
        while time.time() - start_wait < max_wait:
            try:
                result = subprocess.run(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and 'Up' in result.stdout:
                    recovery_time = time.time() - start_wait
                    self.logger.info(f"✅ Contêiner {container_name} recuperado em {recovery_time:.2f}s")
                    return recovery_time
            except:
                pass
            time.sleep(self.config["monitoring_interval"])
        
        self.logger.warning(f"⚠️ Timeout aguardando recuperação do contêiner {container_name}")
        return max_wait

    def run_chaos_experiment(self, tech: str, count: int, size: int, 
                           rps: Optional[int] = None, chaos_delay: int = None) -> Dict[str, Any]:
        """
        Executa experimento de tolerância a falhas (Chaos Engineering)
        """
        if chaos_delay is None:
            chaos_delay = self.config["default_delay"]
            
        self.logger.info(f"🔥 Iniciando experimento de tolerância a falhas para {tech.upper()}")
        self.logger.info(f"   • Mensagens: {count}")
        self.logger.info(f"   • Tamanho: {size} bytes")
        self.logger.info(f"   • Rate Limiting: {rps or 'unlimited'} RPS")
        self.logger.info(f"   • Delay para falha: {chaos_delay}s")
        
        # Identificar líder
        if tech == 'kafka':
            leader = self.get_kafka_leader()
        elif tech == 'rabbitmq':
            leader = self.get_rabbitmq_leader()
        else:
            self.logger.error(f"❌ Tecnologia {tech} não suportada para experimento de chaos")
            return {}
        
        if not leader:
            self.logger.error(f"❌ Não foi possível identificar líder para {tech}")
            return {}
        
        self.logger.info(f"🎯 Líder identificado: {leader}")
        
        # Criar métricas para o experimento
        metrics = MetricsCollector(tech, "chaos")
        
        # Timestamps para medição
        experiment_start = time.time()
        chaos_start = None
        chaos_end = None
        recovery_start = None
        recovery_end = None
        
        # Iniciar produtor em thread separada
        producer_thread = None
        producer_results = {'success': False, 'errors': [], 'messages_sent': 0}
        
        def producer_worker():
            try:
                # Importar e executar produtor
                if tech == "kafka":
                    from ..brokers.kafka.producer import KafkaProducerBroker
                    producer = KafkaProducerBroker()
                    producer_results['success'] = producer.send_messages(count, size, rps)
                elif tech == "rabbitmq":
                    from ..brokers.rabbitmq.producer import RabbitMQProducer
                    producer = RabbitMQProducer()
                    producer_results['success'] = producer.send_messages(count, size, rps)
                else:
                    producer_results['success'] = False
                    producer_results['errors'].append(f"Tecnologia {tech} não suportada")
                    
            except Exception as e:
                producer_results['success'] = False
                producer_results['errors'].append(str(e))
        
        # Iniciar produtor
        self.logger.info(f"🚀 Iniciando produtor...")
        producer_thread = threading.Thread(target=producer_worker, daemon=True)
        producer_thread.start()
        
        # Aguardar delay antes de causar falha
        self.logger.info(f"⏰ Aguardando {chaos_delay}s antes de causar falha...")
        time.sleep(chaos_delay)
        
        # Causar falha no líder
        self.logger.info(f"💥 Causando falha no líder {leader}...")
        chaos_start = time.time()
        
        if self.kill_container(leader):
            chaos_end = time.time()
            self.logger.info(f"🔥 Falha causada em {chaos_end - chaos_start:.2f}s")
            
            # Aguardar um pouco para ver o impacto
            time.sleep(5)
            
            # Aguardar recuperação
            recovery_start = time.time()
            recovery_time = self.wait_for_container_recovery(leader)
            recovery_end = time.time()
            
            self.logger.info(f"🔄 Tempo de recuperação: {recovery_time:.2f}s")
        else:
            self.logger.error(f"❌ Falha ao causar falha no líder {leader}")
            return {}
        
        # Aguardar produtor finalizar
        self.logger.info(f"⏳ Aguardando produtor finalizar...")
        producer_thread.join(timeout=60)
        
        experiment_end = time.time()
        
        # Calcular métricas
        downtime = chaos_end - chaos_start if chaos_end and chaos_start else 0
        recovery_time = recovery_end - recovery_start if recovery_end and recovery_start else 0
        total_experiment_time = experiment_end - experiment_start
        
        # Salvar resultados do experimento
        chaos_results = {
            'leader_container': leader,
            'total_messages': count,
            'message_size': size,
            'rps': rps or 'unlimited',
            'chaos_delay_sec': chaos_delay,
            'downtime_sec': downtime,
            'recovery_time_sec': recovery_time,
            'total_experiment_time_sec': total_experiment_time,
            'producer_success': producer_results['success'],
            'messages_sent': producer_results['messages_sent']
        }
        
        # Salvar métricas
        metrics.save_summary(chaos_results)
        
        # Exibir resultados
        self.logger.info(f"\n📊 RESULTADOS DO EXPERIMENTO DE TOLERÂNCIA A FALHAS:")
        self.logger.info(f"   • Líder testado: {leader}")
        self.logger.info(f"   • Tempo de indisponibilidade: {downtime:.2f}s")
        self.logger.info(f"   • Tempo de recuperação: {recovery_time:.2f}s")
        self.logger.info(f"   • Tempo total do experimento: {total_experiment_time:.2f}s")
        self.logger.info(f"   • Produtor bem-sucedido: {producer_results['success']}")
        
        return chaos_results
