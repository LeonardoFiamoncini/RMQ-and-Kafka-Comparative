"""
Sistema de coleta e armazenamento de métricas.

Este módulo fornece funcionalidades para coletar, processar e armazenar
métricas de performance dos benchmarks e experimentos.
"""

import csv
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .config import LOGS_DIR
from .logger import Logger
from .percentile import calculate_percentile


class MetricsCollector:
    """Coletor de métricas para benchmarks."""

    def __init__(
        self,
        tech: str,
        experiment_type: str = "benchmark",
        run_id: Optional[str] = None,
    ):
        """Inicializa o coletor de métricas."""
        self.tech = tech
        self.experiment_type = experiment_type
        self.logger = Logger.get_logger(f"metrics.{tech}")
        unique_suffix = uuid.uuid4().hex[:6]
        self.timestamp = f"{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_{unique_suffix}"
        self.base_dir = LOGS_DIR / tech
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.metrics_dir = self.base_dir / self.run_id
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # Métricas coletadas
        self.latencies: List[tuple] = []
        self.send_times: Dict[str, float] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.messages_sent: int = 0
        self.messages_consumed: int = 0
        # Rastrear msg_ids já registrados para evitar duplicatas
        self._recorded_msg_ids: set = set()

    def start_timing(self):
        """Inicia o cronômetro."""
        self.start_time = time.time()

    def end_timing(self):
        """Finaliza o cronômetro."""
        self.end_time = time.time()

    def record_send_time(self, message_id: str, timestamp: float):
        """Registra o tempo de envio de uma mensagem."""
        self.send_times[message_id] = timestamp

    def record_latency(self, latency: float, message_id: str):
        """
        Registra a latência de uma mensagem.
        
        Args:
            latency: Latência em segundos
            message_id: ID da mensagem
        
        Evita registrar a mesma mensagem múltiplas vezes.
        Se a mensagem já foi registrada, ignora silenciosamente.
        """
        # Evitar duplicatas: se já registramos esta mensagem, ignorar
        if message_id in self._recorded_msg_ids:
            self.logger.debug(f"Mensagem {message_id} já foi registrada, ignorando duplicata")
            return
        
        # Registrar mensagem
        self._recorded_msg_ids.add(message_id)
        self.latencies.append((message_id, latency))

    def save_send_times(self) -> Path:
        """Salva os tempos de envio em arquivo JSON."""
        file_path = self.metrics_dir / f"{self.timestamp}_send_times.json"
        with open(file_path, "w") as f:
            json.dump(self.send_times, f)
        self.logger.info(f"Send times salvos em: {file_path}")
        return file_path

    def save_latencies(self) -> Path:
        """Salva as latências em arquivo CSV."""
        file_path = self.metrics_dir / f"{self.timestamp}_latency.csv"
        
        # Só criar arquivo se houver latências para salvar
        if not self.latencies:
            self.logger.warning(f"Nenhuma latência para salvar, não criando arquivo vazio")
            return file_path
            
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["msg_id", "latency_seconds"])
            writer.writerows(self.latencies)
        self.logger.info(f"Latências salvas em: {file_path} ({len(self.latencies)} registros)")
        return file_path

    def save_summary(self, additional_metrics: Dict[str, Any] = None) -> Path:
        """Salva resumo das métricas em CSV."""
        file_path = self.metrics_dir / f"{self.timestamp}_summary.csv"

        duration = (
            (self.end_time - self.start_time)
            if self.start_time and self.end_time
            else 0
        )
        avg_latency = (
            sum(lat for _, lat in self.latencies) / len(self.latencies)
            if self.latencies
            else 0
        )
        throughput = len(self.latencies) / duration if duration > 0 else 0

        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["metric", "value"])
            writer.writerow(["total_messages", len(self.send_times)])
            writer.writerow(["total_received", len(self.latencies)])
            writer.writerow(["duration_sec", duration])
            writer.writerow(["avg_latency_sec", avg_latency])
            writer.writerow(["throughput_msgs_per_sec", throughput])

            # Métricas adicionais
            if additional_metrics:
                for key, value in additional_metrics.items():
                    writer.writerow([key, value])

        self.logger.info(f"Summary salvo em: {file_path}")
        return file_path

    def save_benchmark_results(self, config: Dict[str, Any]) -> Path:
        """Salva resultados do benchmark em CSV consolidado."""
        file_path = self.base_dir / "benchmark_results.csv"

        # Usar valores passados no config se disponíveis (valores calculados pelo orchestrator)
        # Caso contrário, calcular a partir das latências coletadas
        if "avg_latency" in config and "throughput" in config:
            # Usar valores já calculados pelo orchestrator
            latency_avg = config.get("avg_latency", 0)
            throughput = config.get("throughput", 0)
            duration = config.get("duration", 0)
            
            # Usar percentis passados no config se disponíveis
            if "latency_95" in config and "latency_99" in config:
                latency_95 = config.get("latency_95", latency_avg)
                latency_99 = config.get("latency_99", latency_avg)
            else:
                # Calcular percentis usando o método correto
                latencies = [lat for _, lat in self.latencies]
                if latencies:
                    sorted_latencies = sorted(latencies)
                    # Usar o método correto de cálculo de percentis (Hyndman & Fan método 7)
                    latency_95 = calculate_percentile(sorted_latencies, 95)
                    latency_99 = calculate_percentile(sorted_latencies, 99)
                else:
                    # Se não temos latências coletadas, usar avg_latency para todos os percentis
                    latency_95 = latency_99 = latency_avg
        else:
            # Calcular métricas a partir das latências coletadas (comportamento antigo)
            duration = (
                (self.end_time - self.start_time)
                if self.start_time and self.end_time
                else 0
            )
            latencies = [lat for _, lat in self.latencies]

            if latencies:
                sorted_latencies = sorted(latencies)
                n = len(latencies)
                # Usar o método correto de cálculo de percentis (Hyndman & Fan método 7)
                latency_95 = calculate_percentile(sorted_latencies, 95)
                latency_99 = calculate_percentile(sorted_latencies, 99)
                latency_avg = sum(latencies) / n
            else:
                latency_95 = latency_99 = latency_avg = 0

            throughput = len(self.latencies) / duration if duration > 0 else 0

        # Verificar se arquivo existe para decidir se escreve cabeçalho
        write_header = not file_path.exists()

        with open(file_path, "a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(
                    [
                        "timestamp",
                        "tech",
                        "messages",
                        "message_size",
                        "num_producers",
                        "num_consumers",
                        "rps",
                        "latency_avg",
                        "latency_95",
                        "latency_99",
                        "throughput",
                        "successful_producers",
                        "successful_consumers",
                    ]
                )

            writer.writerow(
                [
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    self.tech,
                    config.get("messages", 0),
                    config.get("message_size", 0),
                    config.get("num_producers", 1),
                    config.get("num_consumers", 1),
                    config.get("rps", "unlimited"),
                    round(latency_avg, 6),
                    round(latency_95, 6),
                    round(latency_99, 6),
                    round(throughput, 2),
                    config.get("successful_producers", 0),
                    config.get("successful_consumers", 0),
                ]
            )

        self.logger.info(f"Benchmark results salvos em: {file_path}")
        return file_path
