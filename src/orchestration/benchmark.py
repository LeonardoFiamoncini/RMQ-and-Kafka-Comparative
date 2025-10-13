"""
Módulo de orquestração de benchmarks
"""
import time
import subprocess
import multiprocessing
from multiprocessing import Pool
from typing import Dict, List, Any, Optional, Tuple
from ..core.config import BENCHMARK_CONFIG
from ..core.logger import Logger
from ..core.metrics import MetricsCollector
from ..brokers.kafka.producer import KafkaProducerBroker as KafkaProd
from ..brokers.kafka.consumer import KafkaConsumerBroker as KafkaCons
from ..brokers.rabbitmq.producer import RabbitMQProducer as RabbitMQProd
from ..brokers.rabbitmq.consumer import RabbitMQConsumer as RabbitMQCons
from ..brokers.baseline.client import BaselineClient

class BenchmarkOrchestrator:
    """Orquestrador de benchmarks"""
    
    def __init__(self):
        self.logger = Logger.get_logger("benchmark.orchestrator")
        self.config = BENCHMARK_CONFIG
        
    def run_producer_process(self, tech: str, producer_id: int, messages_per_producer: int, 
                           message_size: int, rps: Optional[int] = None) -> Dict[str, Any]:
        """Executa um processo produtor individual"""
        try:
            if tech == "kafka":
                producer = KafkaProd()
                success = producer.send_messages(messages_per_producer, message_size, rps)
            elif tech == "rabbitmq":
                producer = RabbitMQProd()
                success = producer.send_messages(messages_per_producer, message_size, rps)
            elif tech == "baseline":
                client = BaselineClient()
                success = client.send_messages(messages_per_producer, message_size, rps)
            else:
                return {"success": False, "error": f"Tecnologia {tech} não suportada"}
                
            return {
                "success": success,
                "producer_id": producer_id,
                "messages_sent": messages_per_producer
            }
        except Exception as e:
            self.logger.error(f"Erro no produtor {producer_id}: {e}")
            return {"success": False, "producer_id": producer_id, "error": str(e)}
    
    def run_consumer_process(self, tech: str, consumer_id: int, expected_count: int) -> Dict[str, Any]:
        """Executa um processo consumidor individual"""
        try:
            if tech == "kafka":
                consumer = KafkaCons()
                success = consumer.consume_messages(expected_count)
            elif tech == "rabbitmq":
                consumer = RabbitMQCons()
                success = consumer.consume_messages(expected_count)
            else:
                return {"success": False, "error": f"Tecnologia {tech} não suportada"}
                
            return {
                "success": success,
                "consumer_id": consumer_id
            }
        except Exception as e:
            self.logger.error(f"Erro no consumidor {consumer_id}: {e}")
            return {"success": False, "consumer_id": consumer_id, "error": str(e)}
    
    def run_benchmark(self, tech: str, count: int, size: int, 
                     num_producers: int = 1, num_consumers: int = 1, 
                     rps: Optional[int] = None) -> Dict[str, Any]:
        """
        Executa benchmark para uma tecnologia específica
        """
        self.logger.info(f"Iniciando benchmark para {tech.upper()}")
        self.logger.info(f"   • Produtores: {num_producers}")
        self.logger.info(f"   • Consumidores: {num_consumers}")
        self.logger.info(f"   • Mensagens totais: {count}")
        self.logger.info(f"   • Tamanho da mensagem: {size} bytes")
        
        start_time = time.time()
        
        # Calcular mensagens por produtor
        messages_per_producer = count // num_producers
        
        # Iniciar consumidores (exceto para baseline)
        consumer_results = []
        if tech != "baseline":
            self.logger.info(f"   • Iniciando {num_consumers} consumidor(es)...")
            with Pool(processes=num_consumers) as pool:
                consumer_args = [(tech, i, count) for i in range(num_consumers)]
                consumer_results = pool.starmap(self.run_consumer_process, consumer_args)
            
            # Aguardar um pouco para os consumidores se conectarem
            time.sleep(3)
        else:
            self.logger.info(f"   • Baseline HTTP - sem consumidor separado")
            consumer_results = [{"success": True, "consumer_id": 0}]  # Mock para baseline
        
        # Iniciar produtores
        self.logger.info(f"   • Iniciando {num_producers} produtor(es)...")
        with Pool(processes=num_producers) as pool:
            producer_args = [(tech, i, messages_per_producer, size, rps) for i in range(num_producers)]
            producer_results = pool.starmap(self.run_producer_process, producer_args)
        
        end_time = time.time()
        
        # Calcular estatísticas
        successful_producers = sum(1 for r in producer_results if r["success"])
        successful_consumers = sum(1 for r in consumer_results if r["success"])
        
        # Calcular métricas agregadas
        duration = end_time - start_time
        total_messages_sent = sum(r.get("messages_sent", 0) for r in producer_results if r["success"])
        
        # Calcular latência e throughput (simplificado)
        avg_latency = 0.0  # Será calculado pelos consumidores
        throughput = total_messages_sent / duration if duration > 0 else 0
        
        results = {
            "tech": tech,
            "duration": duration,
            "total_messages": count,
            "messages_sent": total_messages_sent,
            "successful_producers": successful_producers,
            "successful_consumers": successful_consumers,
            "avg_latency": avg_latency,
            "throughput": throughput,
            "producer_results": producer_results,
            "consumer_results": consumer_results
        }
        
        # Salvar resultados consolidados
        self._save_benchmark_results(tech, results, {
            "messages": count,
            "message_size": size,
            "num_producers": num_producers,
            "num_consumers": num_consumers,
            "rps": rps,
            "successful_producers": successful_producers,
            "successful_consumers": successful_consumers
        })
        
        self.logger.info(f"✅ Benchmark {tech.upper()} finalizado:")
        self.logger.info(f"   • Latência média: {avg_latency:.4f}s")
        self.logger.info(f"   • Throughput: {throughput:.2f} msgs/s")
        self.logger.info(f"   • Mensagens processadas: {total_messages_sent}")
        self.logger.info(f"   • Duração total: {duration:.2f}s")
        
        return results
    
    def _save_benchmark_results(self, tech: str, results: Dict[str, Any], config: Dict[str, Any]):
        """Salva resultados do benchmark"""
        metrics = MetricsCollector(tech, "benchmark")
        metrics.save_benchmark_results(config)
    
    def run_all_benchmarks(self, count: int, size: int, 
                          num_producers: int = 1, num_consumers: int = 1, 
                          rps: Optional[int] = None) -> Dict[str, Any]:
        """
        Executa benchmarks para todas as tecnologias
        """
        technologies = ["rabbitmq", "kafka", "baseline"]
        all_results = {}
        
        for tech in technologies:
            self.logger.info(f"\n{'='*60}")
            try:
                results = self.run_benchmark(tech, count, size, num_producers, num_consumers, rps)
                all_results[tech] = results
            except Exception as e:
                self.logger.error(f"Erro no benchmark {tech}: {e}")
                all_results[tech] = {"error": str(e)}
        
        return all_results
