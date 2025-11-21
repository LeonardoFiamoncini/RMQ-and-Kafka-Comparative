"""
Implementação simplificada do cliente Baseline HTTP para TCC
"""

import json
import time
from typing import Optional

import requests

from ...core.config import BROKER_CONFIGS
from ..base import BaseBroker


class BaselineClient(BaseBroker):
    """Cliente HTTP simplificado - envia requisições síncronas"""

    def __init__(self, run_id: Optional[str] = None):
        super().__init__("baseline", run_id=run_id)
        self.config = BROKER_CONFIGS["baseline"]
        self.base_url = f"http://{self.config['host']}:{self.config['port']}"

    def send_messages(
        self, count: int, size: int, rps: Optional[int] = None, **kwargs
    ) -> bool:
        """
        Envia requisições HTTP síncronas em rajada
        
        Args:
            count: Número de requisições para enviar
            size: Tamanho de cada mensagem em bytes
            rps: Rate limiting (não usado - sempre rajada)
        """
        try:
            self.metrics.start_timing()
            
            # Verificar se servidor está respondendo
            try:
                response = requests.get(f"{self.base_url}/health", timeout=2)
                if response.status_code != 200:
                    self.logger.warning(f"Servidor baseline retornou status {response.status_code}")
            except requests.exceptions.RequestException:
                self.logger.info("Servidor ainda iniciando, continuando mesmo assim...")
            
            self.logger.info(f"✅ Cliente Baseline conectado. Enviando {count} requisições...")
            
            # Gerar payload com tamanho especificado
            payload = "x" * max(0, size - 50)  # Descontar overhead do JSON
            
            # Enviar requisições em rajada
            for i in range(count):
                msg_id = f"msg_{i+1}"
                
                # Mensagem com timestamp embutido
                message = {
                    "id": msg_id,
                    "timestamp": time.time(),  # Timestamp do envio
                    "body": payload
                }
                
                try:
                    # Medir latência da requisição
                    start_time = time.time()
                    
                    # Enviar requisição POST síncrona
                    response = requests.post(
                        f"{self.base_url}/message",
                        json=message,
                        timeout=10
                    )
                    
                    # Calcular latência
                    latency = time.time() - start_time
                    
                    if response.status_code == 200:
                        # Registrar latência
                        self.metrics.record_latency(latency, msg_id)
                        self.metrics.messages_sent += 1
                    else:
                        self.logger.warning(f"Requisição {msg_id} retornou status {response.status_code}")
                    
                    # Log a cada 1000 requisições
                    if (i + 1) % 1000 == 0:
                        self.logger.info(f"Enviadas {i+1}/{count} requisições")
                    
                except requests.exceptions.RequestException as e:
                    self.logger.error(f"Erro ao enviar requisição {msg_id}: {e}")
                    continue
            
            # Finalizar métricas
            self.metrics.end_timing()
            self.metrics.messages_consumed = self.metrics.messages_sent  # Para baseline, enviado = consumido
            self.metrics.save_latencies()
            self.metrics.save_summary()
            
            self.logger.info(f"✅ {self.metrics.messages_sent} requisições enviadas com sucesso")
            
            return self.metrics.messages_sent == count
            
        except Exception as e:
            self.logger.error(f"❌ Erro no cliente Baseline: {e}")
            return False