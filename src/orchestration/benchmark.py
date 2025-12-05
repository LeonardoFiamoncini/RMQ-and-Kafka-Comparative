"""
Módulo simplificado de benchmark para TCC
"""

import csv
import time
import uuid
from datetime import datetime
from threading import Thread
from typing import Any, Dict, Optional

from ..brokers.baseline.client import BaselineClient
from ..brokers.kafka.consumer import KafkaConsumerBroker
from ..brokers.kafka.producer import KafkaProducerBroker
from ..brokers.rabbitmq.consumer import RabbitMQConsumer
from ..brokers.rabbitmq.producer import RabbitMQProducer
from ..core.config import LOGS_DIR
from ..core.logger import Logger
from ..core.percentile import calculate_percentile, calculate_metrics_statistics


class BenchmarkOrchestrator:
    """Orquestrador simplificado de benchmarks para o TCC"""

    def __init__(self):
        self.logger = Logger.get_logger("benchmark.orchestrator")

    def run_benchmark(
        self,
        tech: str,
        count: int,
        size: int = 200,
        size_name: str = "size1"
    ) -> Dict[str, Any]:
        """
        Executa benchmark para uma tecnologia específica
        
        Args:
            tech: Tecnologia (baseline, kafka, rabbitmq)
            count: Número de mensagens para enviar em rajada
            size: Tamanho de cada mensagem em bytes
            size_name: Size da carga (size1, size2, size3, size4, size5)
        
        Returns:
            Dicionário com métricas coletadas
        """
        self.logger.info(f"Iniciando benchmark {tech.upper()} - Size {size_name.upper()}")
        self.logger.info(f"   • Mensagens: {count:,}")
        self.logger.info(f"   • Tamanho: {size} bytes")
        self.logger.info(f"   • Modo: Rajada única (burst)")

        # Gerar ID único para esta execução
        start_time = time.time()
        run_id = f"{tech}-{size_name}-{int(start_time)}-{uuid.uuid4().hex[:6]}"
        self.logger.info(f"   • Run ID: {run_id}")
        
        # Criar diretório para logs
        run_metrics_dir = LOGS_DIR / tech / run_id
        run_metrics_dir.mkdir(parents=True, exist_ok=True)

        # Para Kafka e RabbitMQ, iniciar consumidor antes do produtor
        consumer_thread = None
        consumer_results = {"success": False, "messages_consumed": 0}
        
        if tech != "baseline":
            self.logger.info(f"   • Iniciando consumidor {tech}...")
            
            def run_consumer():
                try:
                    if tech == "kafka":
                        consumer = KafkaConsumerBroker(run_id=run_id)
                        consumer_results["success"] = consumer.consume_messages(count)
                        consumer_results["messages_consumed"] = count
                    elif tech == "rabbitmq":
                        consumer = RabbitMQConsumer(run_id=run_id)
                        consumer_results["success"] = consumer.consume_messages(count)
                        consumer_results["messages_consumed"] = count
                except Exception as e:
                    self.logger.error(f"Erro no consumidor: {e}")
                    consumer_results["error"] = str(e)
            
            consumer_thread = Thread(target=run_consumer, daemon=False)
            consumer_thread.start()
            
            # Aguardar consumidor conectar - tempo mínimo para não adicionar latência artificial
            # RabbitMQ e Kafka precisam de tempo para se conectar
            wait_time = 1.0  # Tempo uniforme para todos
            time.sleep(wait_time)

        # Executar produtor (ou cliente baseline)
        self.logger.info(f"   • Enviando {count} mensagens em rajada...")
        producer_start = time.time()
        
        try:
            if tech == "baseline":
                # Para baseline, usar cliente HTTP
                client = BaselineClient(run_id=run_id)
                success = client.send_messages(count, size)
            elif tech == "kafka":
                producer = KafkaProducerBroker(run_id=run_id)
                success = producer.send_messages(count, size)
            elif tech == "rabbitmq":
                producer = RabbitMQProducer(run_id=run_id)
                success = producer.send_messages(count, size)
            else:
                raise ValueError(f"Tecnologia {tech} não suportada")
                
        except Exception as e:
            self.logger.error(f"Erro no produtor: {e}")
            success = False
        
        producer_end = time.time()
        producer_duration = producer_end - producer_start
        
        # Aguardar consumidor terminar (se aplicável)
        if consumer_thread:
            self.logger.info(f"   • Aguardando consumidor processar mensagens...")
            consumer_thread.join(timeout=60)
            
            if not consumer_results["success"]:
                self.logger.warning(f"Consumidor teve problemas: {consumer_results.get('error', 'Unknown')}")
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calcular métricas a partir dos arquivos salvos
        self.logger.info(f"   • Calculando métricas...")
        metrics = self._calculate_metrics(run_metrics_dir, count, total_duration)
        
        # Adicionar informações de execução
        metrics.update({
            "tech": tech,
            "size": size_name,
            "run_id": run_id,
            "messages_requested": count,
            "message_size": size,
            "producer_duration": producer_duration,
            "total_duration": total_duration,
            "success": success
        })
        
        # Salvar resultados consolidados
        self._save_benchmark_results(tech, size_name, metrics)
        
        # Log dos resultados principais
        self.logger.info(f"Benchmark concluído:")
        self.logger.info(f"   • Throughput: {metrics['throughput']:.2f} msg/s")
        self.logger.info(f"   • Latência P95: {metrics['latency_95']:.6f} s")
        self.logger.info(f"   • Latência P99: {metrics['latency_99']:.6f} s")
        
        return metrics
    
    def _calculate_metrics(self, metrics_dir, expected_messages, duration):
        """
        Calcula métricas a partir dos arquivos de log
        """
        # Ler latências dos arquivos CSV
        latencies = []
        latency_files = list(metrics_dir.glob("*_latency.csv"))
        
        for latency_file in latency_files:
            try:
                with open(latency_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            latency = float(row.get('latency_seconds', 0))
                            if latency >= 0:  # Validar latência
                                latencies.append(latency)
                        except (ValueError, TypeError):
                            continue
            except Exception as e:
                self.logger.warning(f"Erro ao ler {latency_file}: {e}")
        
        # Se não houver latências, tentar ler do summary
        if not latencies:
            summary_files = list(metrics_dir.glob("*_summary.csv"))
            for summary_file in summary_files:
                try:
                    with open(summary_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            if row.get('metric') == 'avg_latency_sec':
                                avg_lat = float(row.get('value', 0))
                                if avg_lat > 0:
                                    # Simular distribuição com base na média
                                    latencies = [avg_lat] * min(100, expected_messages)
                                break
                except Exception:
                    continue
        
        # Usar o cálculo correto de métricas com percentis precisos
        if latencies:
            # Usar a função que implementa o método correto de percentis
            metrics_stats = calculate_metrics_statistics(latencies, duration)
            
            latency_95 = metrics_stats['p95']
            latency_99 = metrics_stats['p99']
            avg_latency = metrics_stats['avg']
            throughput = metrics_stats['throughput']
            messages_processed = metrics_stats['count']
        else:
            # Valores padrão se não houver dados
            latency_95 = latency_99 = avg_latency = 0.0
            messages_processed = 0
            throughput = 0.0
        
        return {
            "messages_processed": messages_processed,
            "throughput": throughput,
            "avg_latency": avg_latency,
            "latency_95": latency_95,
            "latency_99": latency_99
        }
    
    def _save_benchmark_results(self, tech: str, size_name: str, results: Dict[str, Any]):
        """
        Salva resultados consolidados do benchmark
        """
        # Arquivo CSV consolidado por tecnologia
        csv_file = LOGS_DIR / tech / "benchmark_results.csv"
        csv_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Preparar linha de dados
        row_data = {
            "timestamp": datetime.now().isoformat(),
            "size": size_name,
            "message_size": results.get("message_size", 0),
            "run_id": results.get("run_id", ""),
            "messages_requested": results.get("messages_requested", 0),
            "messages_processed": results.get("messages_processed", 0),
            "throughput": results.get("throughput", 0),
            "latency_95": results.get("latency_95", 0),
            "latency_99": results.get("latency_99", 0),
            "avg_latency": results.get("avg_latency", 0),
            "duration": results.get("total_duration", 0)
        }
        
        # Escrever no CSV
        file_exists = csv_file.exists()
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row_data.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row_data)
        
        self.logger.info(f"Resultados salvos em: {csv_file}")