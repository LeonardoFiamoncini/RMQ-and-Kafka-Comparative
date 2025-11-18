"""
Módulo de orquestração de benchmarks
"""

import math
import time
from multiprocessing import Pool
from threading import Event, Thread
from typing import Any, Dict, Optional

import subprocess

from ..brokers.baseline.client import BaselineClient
from ..brokers.baseline.server import BaselineServer
from ..brokers.kafka.consumer import KafkaConsumerBroker as KafkaCons
from ..brokers.kafka.producer import KafkaProducerBroker as KafkaProd
from ..brokers.rabbitmq.consumer import RabbitMQConsumer as RabbitMQCons
from ..brokers.rabbitmq.producer import RabbitMQProducer as RabbitMQProd
from ..core.config import BENCHMARK_CONFIG
from ..core.logger import Logger
from ..core.metrics import MetricsCollector


class BenchmarkOrchestrator:
    """Orquestrador de benchmarks"""

    def __init__(self):
        self.logger = Logger.get_logger("benchmark.orchestrator")
        self.config = BENCHMARK_CONFIG

    def run_producer_process(
        self,
        tech: str,
        producer_id: int,
        messages_per_producer: int,
        message_size: int,
        rps: Optional[int] = None,
        total_messages: int = 0,  # Mantido para compatibilidade
        id_offset: int = 0,
    ) -> Dict[str, Any]:
        """Executa um processo produtor individual"""
        try:
            if tech == "kafka":
                producer = KafkaProd()
                success = producer.send_messages(
                    messages_per_producer, message_size, rps, id_offset=id_offset
                )
            elif tech == "rabbitmq":
                producer = RabbitMQProd()
                success = producer.send_messages(
                    messages_per_producer, message_size, rps, id_offset=id_offset
                )
            elif tech == "baseline":
                client = BaselineClient()
                success = client.send_messages(
                    messages_per_producer, message_size, rps, id_offset=id_offset
                )
            else:
                return {"success": False, "error": f"Tecnologia {tech} não suportada"}

            return {
                "success": success,
                "producer_id": producer_id,
                "messages_sent": messages_per_producer,
            }
        except Exception as e:
            self.logger.error(f"Erro no produtor {producer_id}: {e}")
            return {"success": False, "producer_id": producer_id, "error": str(e)}

    def run_consumer_process(
        self,
        tech: str,
        consumer_id: int,
        expected_count: int,
        start_event: Optional[Event] = None,
        start_timeout: float = 120.0,
    ) -> Dict[str, Any]:
        """Executa um processo consumidor individual"""
        try:
            if start_event is not None:
                self.logger.info(
                    f"   • Consumidor {consumer_id} aguardando liberação para iniciar consumo"
                )
                if not start_event.wait(timeout=start_timeout):
                    self.logger.error(
                        f"Consumidor {consumer_id} não foi liberado para consumir dentro do timeout"
                    )
                    return {
                        "success": False,
                        "consumer_id": consumer_id,
                        "error": "Timeout aguardando liberação para consumir",
                    }

            if tech == "kafka":
                consumer = KafkaCons()
                success = consumer.consume_messages(expected_count)
            elif tech == "rabbitmq":
                consumer = RabbitMQCons()
                success = consumer.consume_messages(expected_count)
            else:
                return {"success": False, "error": f"Tecnologia {tech} não suportada"}

            return {"success": success, "consumer_id": consumer_id}
        except Exception as e:
            self.logger.error(f"Erro no consumidor {consumer_id}: {e}")
            return {"success": False, "consumer_id": consumer_id, "error": str(e)}

    def run_benchmark(
        self,
        tech: str,
        count: int,
        size: int,
        num_producers: int = 1,
        num_consumers: int = 1,
        rps: Optional[int] = None,
    ) -> Dict[str, Any]:
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
        consumer_threads = []
        messages_per_consumer = max(1, math.ceil(count / num_consumers))

        send_times_event: Optional[Event] = None

        if tech != "baseline":
            # IMPORTANTE: Iniciar consumidores ANTES dos produtores para que estejam prontos,
            # mas eles só começam a processar após os produtores terminarem
            self.logger.info(f"   • Preparando {num_consumers} consumidor(es)...")
            send_times_event = Event()
            
            # Iniciar consumidores em threads separadas para não bloquear
            def run_consumer_wrapper(tech_arg, consumer_id_arg, expected_count_arg):
                """Wrapper para executar consumidor e armazenar resultado"""
                try:
                    result = self.run_consumer_process(
                        tech_arg,
                        consumer_id_arg,
                        expected_count_arg,
                        start_event=send_times_event,
                    )
                    consumer_results.append(result)
                except Exception as e:
                    self.logger.error(f"Erro no consumidor {consumer_id_arg}: {e}")
                    consumer_results.append({"success": False, "consumer_id": consumer_id_arg, "error": str(e)})
            
            for i in range(num_consumers):
                thread = Thread(
                    target=run_consumer_wrapper,
                    args=(tech, i, messages_per_consumer),
                    daemon=False,
                )  # Não daemon para não terminar prematuramente
                thread.start()
                consumer_threads.append(thread)

            # Aguardar um pouco para os consumidores se conectarem aos brokers
            time.sleep(3)
        else:
            self.logger.info(f"   • Baseline HTTP - sem consumidor separado")
            consumer_results = [
                {"success": True, "consumer_id": 0}
            ]  # Mock para baseline

        # Iniciar produtores
        self.logger.info(f"   • Iniciando {num_producers} produtor(es)...")
        with Pool(processes=num_producers) as pool:
            producer_args = []
            current_offset = 0
            for i in range(num_producers):
                messages_for_this_producer = messages_per_producer + (
                    1 if i < (count % num_producers) else 0
                )
                producer_args.append(
                    (
                        tech,
                        i,
                        messages_for_this_producer,
                        size,
                        rps,
                        count,
                        current_offset,
                    )
                )
                current_offset += messages_for_this_producer

            producer_results = pool.starmap(self.run_producer_process, producer_args)
        
        # CRÍTICO: Aguardar produtores terminarem e salvarem send_times ANTES de consumidores processarem
        # Aguardar um pouco mais para garantir que TODOS os arquivos send_times foram salvos
        self.logger.info("   • Aguardando produtores salvarem métricas...")
        time.sleep(10)  # Aumentar tempo de espera para garantir que arquivos foram salvos
        
        # Verificar se os arquivos send_times foram criados
        from ..core.config import LOGS_DIR
        metrics_dir = LOGS_DIR / tech
        wait_start = time.time()
        required_files = num_producers if tech != "baseline" else 0
        send_times_files = []
        if tech != "baseline":
            while time.time() - wait_start < 30:
                send_times_files = list(metrics_dir.glob("*_send_times.json"))
                if len(send_times_files) >= required_files:
                    break
                time.sleep(1)
            if send_times_files:
                self.logger.info(
                    f"   • {len(send_times_files)} arquivo(s) send_times encontrado(s)"
                )
            else:
                self.logger.warning(
                    "   • ⚠️ Nenhum arquivo send_times encontrado após aguardar 30s"
                )

        # Liberar consumidores após confirmação dos arquivos de send_times
        if send_times_event is not None:
            self.logger.info(
                "   • Liberando consumidores após confirmação dos arquivos send_times"
            )
            send_times_event.set()
        
        # Aguardar consumidores terminarem (com timeout)
        if tech != "baseline":
            # Notificar consumidores para recarregar send_times (se necessário)
            # Os consumidores já fazem isso automaticamente no consume_messages
            for thread in consumer_threads:
                thread.join(timeout=120)  # Timeout de 2 minutos
            # Aguardar um pouco para garantir que os arquivos foram salvos
            time.sleep(2)

        end_time = time.time()

        # Calcular estatísticas
        successful_producers = sum(1 for r in producer_results if r["success"])
        successful_consumers = sum(1 for r in consumer_results if r["success"])

        # Calcular métricas agregadas
        duration = end_time - start_time
        total_messages_sent = sum(
            r.get("messages_sent", 0) for r in producer_results if r["success"]
        )

        # Calcular latência (T) e throughput (V) a partir dos arquivos de métricas
        from ..core.config import LOGS_DIR
        from pathlib import Path
        import csv
        import json
        
        avg_latency = 0.0
        total_latencies = []
        messages_processed = 0
        
        # Buscar TODOS os arquivos de latência criados recentemente (últimos 5 minutos)
        # e consolidar as latências de todos eles
        metrics_dir = LOGS_DIR / tech
        import time as time_module
        current_time = time_module.time()
        latency_files = sorted(metrics_dir.glob("*_latency.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        
        # Filtrar apenas arquivos criados nos últimos 5 minutos (300 segundos)
        recent_files = [f for f in latency_files if (current_time - f.stat().st_mtime) < 300]
        
        if recent_files:
            # Ler latências de TODOS os arquivos recentes e consolidar
            for latency_file in recent_files:
                try:
                    with open(latency_file, 'r') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            try:
                                latency_val = float(row['latency_seconds'])
                                msg_id = row.get('msg_id', '')
                                # Evitar duplicatas usando msg_id como chave
                                if latency_val > 0:  # Ignorar latências inválidas
                                    total_latencies.append(latency_val)
                                    messages_processed += 1
                            except (ValueError, KeyError):
                                continue
                except Exception as e:
                    self.logger.warning(f"Erro ao ler arquivo de latência {latency_file}: {e}")
                    continue
            
            if total_latencies:
                # Remover duplicatas mantendo a ordem
                seen_ids = set()
                unique_latencies = []
                for lat in total_latencies:
                    if lat not in seen_ids:
                        unique_latencies.append(lat)
                        seen_ids.add(lat)
                total_latencies = unique_latencies
                messages_processed = len(total_latencies)
                avg_latency = sum(total_latencies) / len(total_latencies) if total_latencies else 0
                
                # Calcular percentis de latência
                sorted_latencies = sorted(total_latencies)
                n = len(sorted_latencies)
                latency_50 = sorted_latencies[int(n * 0.5)] if n > 0 else 0
                latency_95 = sorted_latencies[int(n * 0.95)] if n > 0 else 0
                latency_99 = sorted_latencies[int(n * 0.99)] if n > 0 else 0
            else:
                latency_50 = latency_95 = latency_99 = 0
        
        # Para baseline, também pode ter latências ou usar tempo de processamento
        if tech == "baseline" and not total_latencies:
            # Tentar calcular a partir do summary
            summary_files = sorted(metrics_dir.glob("*_summary.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
            if summary_files:
                with open(summary_files[0], 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        if row.get('metric') == 'avg_latency_sec':
                            avg_latency = float(row.get('value', 0))
                        elif row.get('metric') == 'total_received':
                            messages_processed = int(row.get('value', 0))
        
        # Se ainda não temos mensagens processadas, usar mensagens enviadas
        if messages_processed == 0:
            messages_processed = total_messages_sent
        
        # Calcular throughput (V): mensagens processadas por segundo
        throughput = messages_processed / duration if duration > 0 else 0
        
        # Inicializar percentis se não foram calculados
        if 'latency_50' not in locals():
            latency_50 = latency_95 = latency_99 = avg_latency

        results = {
            "tech": tech,
            "duration": duration,
            "total_messages": count,
            "messages_sent": total_messages_sent,
            "messages_processed": messages_processed,
            "successful_producers": successful_producers,
            "successful_consumers": successful_consumers,
            "avg_latency": avg_latency,  # T: Tempo de permanência na fila
            "throughput": throughput,    # V: Throughput (mensagens/segundo)
            "latency_50": latency_50,
            "latency_95": latency_95,
            "latency_99": latency_99,
            "producer_results": producer_results,
            "consumer_results": consumer_results,
        }

        # Salvar resultados consolidados
        self._save_benchmark_results(
            tech,
            results,
            {
                "messages": count,
                "message_size": size,
                "num_producers": num_producers,
                "num_consumers": num_consumers,
                "rps": rps,
                "successful_producers": successful_producers,
                "successful_consumers": successful_consumers,
                "avg_latency": avg_latency,  # Passar latência calculada
                "throughput": throughput,    # Passar throughput calculado
                "duration": duration,         # Passar duração calculada
                "messages_processed": messages_processed,  # Passar mensagens processadas
                "latency_50": latency_50,
                "latency_95": latency_95,
                "latency_99": latency_99,
            },
        )

        self.logger.info(f"✅ Benchmark {tech.upper()} finalizado:")
        self.logger.info(f"   • T (Latência média): {avg_latency:.6f} segundos")
        self.logger.info(f"   • V (Throughput): {throughput:.2f} mensagens/segundo")
        self.logger.info(f"   • Mensagens processadas: {messages_processed:,}")
        self.logger.info(f"   • Duração total: {duration:.2f} segundos")

        return results

    def _save_benchmark_results(
        self, tech: str, results: Dict[str, Any], config: Dict[str, Any]
    ):
        """Salva resultados do benchmark"""
        metrics = MetricsCollector(tech, "benchmark")
        metrics.save_benchmark_results(config)

    def run_all_benchmarks(
        self,
        count: int,
        size: int,
        num_producers: int = 1,
        num_consumers: int = 1,
        rps: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Executa benchmarks para todas as tecnologias
        """
        technologies = ["rabbitmq", "kafka", "baseline"]
        all_results = {}
        
        # Iniciar servidor baseline se necessário
        baseline_server = None
        baseline_port = 5000

        for tech in technologies:
            self.logger.info(f"\n{'='*60}")
            try:
                # Iniciar servidor baseline antes do benchmark baseline
                if tech == "baseline" and baseline_server is None:
                    self.logger.info("🚀 Iniciando servidor baseline...")
                    baseline_server = BaselineServer(port=baseline_port)
                    baseline_thread = Thread(target=baseline_server.run, daemon=True)
                    baseline_thread.start()
                    time.sleep(3)  # Aguardar servidor iniciar
                
                results = self.run_benchmark(
                    tech, count, size, num_producers, num_consumers, rps
                )
                all_results[tech] = results
            except Exception as e:
                self.logger.error(f"Erro no benchmark {tech}: {e}")
                all_results[tech] = {"error": str(e)}
        
        # Parar servidor baseline se foi iniciado
        if baseline_server is not None:
            self.logger.info("🛑 Parando servidor baseline...")
            try:
                subprocess.run(["pkill", "-f", "python.*baseline"], timeout=5)
            except:
                pass

        return all_results
