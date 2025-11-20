"""
Classe base abstrata para implementações de brokers.

Este módulo define a interface comum para todos os brokers de mensagens,
garantindo consistência na implementação e facilitando a extensibilidade.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..core.logger import Logger
from ..core.metrics import MetricsCollector


class BaseBroker(ABC):
    """Classe base abstrata para brokers de mensagens."""

    def __init__(self, tech: str, run_id: Optional[str] = None):
        """Inicializa o broker base."""
        self.tech = tech
        self.logger = Logger.get_logger(f"broker.{tech}")
        self.metrics = MetricsCollector(tech, run_id=run_id)

    @abstractmethod
    def send_messages(
        self, count: int, message_size: int, rps: Optional[int] = None
    ) -> bool:
        """
        Envia mensagens para o broker.

        Args:
            count: Número de mensagens
            message_size: Tamanho de cada mensagem em bytes
            rps: Rate limiting (mensagens por segundo)

        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def consume_messages(self, expected_count: int) -> bool:
        """
        Consome mensagens do broker.

        Args:
            expected_count: Número esperado de mensagens

        Returns:
            bool: True se bem-sucedido, False caso contrário
        """
        pass

    @abstractmethod
    def get_leader(self) -> Optional[str]:
        """
        Identifica o nó líder do cluster.

        Returns:
            str: Nome do contêiner líder ou None se não encontrado
        """
        pass

    def get_metrics(self) -> MetricsCollector:
        """Retorna o coletor de métricas."""
        return self.metrics

    def save_metrics(self, additional_metrics: Dict[str, Any] = None):
        """Salva todas as métricas coletadas."""
        # Só salvar send_times se houver dados
        if self.metrics.send_times:
            self.metrics.save_send_times()
        else:
            self.logger.debug("Nenhum send_time para salvar")
            
        # Só salvar latências se houver dados
        if self.metrics.latencies:
            self.metrics.save_latencies()
        else:
            self.logger.debug("Nenhuma latência para salvar")
            
        # Sempre salvar summary (pode ter informações mesmo sem latências)
        self.metrics.save_summary(additional_metrics)
