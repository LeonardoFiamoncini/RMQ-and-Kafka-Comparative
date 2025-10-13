"""
Sistema de coleta e armazenamento de métricas
"""
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from .config import LOGS_DIR
from .logger import Logger

class MetricsCollector:
    """Coletor de métricas para benchmarks"""
    
    def __init__(self, tech: str, experiment_type: str = "benchmark"):
        self.tech = tech
        self.experiment_type = experiment_type
        self.logger = Logger.get_logger(f"metrics.{tech}")
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        self.metrics_dir = LOGS_DIR / tech
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Métricas coletadas
        self.latencies: List[tuple] = []
        self.send_times: Dict[str, float] = {}
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        
    def start_timing(self):
        """Inicia o cronômetro"""
        self.start_time = time.time()
        
    def end_timing(self):
        """Finaliza o cronômetro"""
        self.end_time = time.time()
        
    def record_send_time(self, message_id: str, timestamp: float):
        """Registra o tempo de envio de uma mensagem"""
        self.send_times[message_id] = timestamp
        
    def record_latency(self, message_id: str, latency: float):
        """Registra a latência de uma mensagem"""
        self.latencies.append((message_id, latency))
        
    def save_send_times(self) -> Path:
        """Salva os tempos de envio em arquivo JSON"""
        file_path = self.metrics_dir / f"{self.timestamp}_send_times.json"
        with open(file_path, 'w') as f:
            json.dump(self.send_times, f)
        self.logger.info(f"Send times salvos em: {file_path}")
        return file_path
        
    def save_latencies(self) -> Path:
        """Salva as latências em arquivo CSV"""
        file_path = self.metrics_dir / f"{self.timestamp}_latency.csv"
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['msg_id', 'latency_seconds'])
            writer.writerows(self.latencies)
        self.logger.info(f"Latências salvas em: {file_path}")
        return file_path
        
    def save_summary(self, additional_metrics: Dict[str, Any] = None) -> Path:
        """Salva resumo das métricas em CSV"""
        file_path = self.metrics_dir / f"{self.timestamp}_summary.csv"
        
        duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        avg_latency = sum(lat for _, lat in self.latencies) / len(self.latencies) if self.latencies else 0
        throughput = len(self.latencies) / duration if duration > 0 else 0
        
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['metric', 'value'])
            writer.writerow(['total_messages', len(self.send_times)])
            writer.writerow(['total_received', len(self.latencies)])
            writer.writerow(['duration_sec', duration])
            writer.writerow(['avg_latency_sec', avg_latency])
            writer.writerow(['throughput_msgs_per_sec', throughput])
            
            # Métricas adicionais
            if additional_metrics:
                for key, value in additional_metrics.items():
                    writer.writerow([key, value])
                    
        self.logger.info(f"Summary salvo em: {file_path}")
        return file_path
        
    def save_benchmark_results(self, config: Dict[str, Any]) -> Path:
        """Salva resultados do benchmark em CSV consolidado"""
        file_path = self.metrics_dir / "benchmark_results.csv"
        
        # Calcular métricas
        duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        latencies = [lat for _, lat in self.latencies]
        
        if latencies:
            latencies.sort()
            n = len(latencies)
            latency_50 = latencies[int(n * 0.5)]
            latency_95 = latencies[int(n * 0.95)]
            latency_99 = latencies[int(n * 0.99)]
            latency_avg = sum(latencies) / n
        else:
            latency_50 = latency_95 = latency_99 = latency_avg = 0
            
        throughput = len(self.latencies) / duration if duration > 0 else 0
        
        # Verificar se arquivo existe para decidir se escreve cabeçalho
        write_header = not file_path.exists()
        
        with open(file_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow([
                    "timestamp", "tech", "messages", "message_size", "num_producers", 
                    "num_consumers", "rps", "latency_avg", "latency_50", "latency_95", 
                    "latency_99", "throughput", "successful_producers", "successful_consumers"
                ])
            
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                self.tech,
                config.get('messages', 0),
                config.get('message_size', 0),
                config.get('num_producers', 1),
                config.get('num_consumers', 1),
                config.get('rps', 'unlimited'),
                round(latency_avg, 6),
                round(latency_50, 6),
                round(latency_95, 6),
                round(latency_99, 6),
                round(throughput, 2),
                config.get('successful_producers', 0),
                config.get('successful_consumers', 0)
            ])
            
        self.logger.info(f"Benchmark results salvos em: {file_path}")
        return file_path
