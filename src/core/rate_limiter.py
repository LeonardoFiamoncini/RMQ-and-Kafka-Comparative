"""
Rate Limiter para controlar taxa de envio de mensagens (RPS).

Baseado em:
- Token Bucket Algorithm (Tanenbaum & Wetherall, 2010)
- Jain, R. (1991). The Art of Computer Systems Performance Analysis

Este módulo implementa um limitador de taxa preciso para garantir
que as mensagens sejam enviadas na taxa especificada (RPS).
"""

import time
from typing import Optional


class RateLimiter:
    """
    Implementa um limitador de taxa usando Token Bucket Algorithm.
    
    Referências:
        Tanenbaum, A.S.; Wetherall, D.J. (2010). Computer Networks (5th ed).
    """
    
    def __init__(self, rate: float):
        """
        Inicializa o rate limiter.
        
        Args:
            rate: Taxa desejada em mensagens por segundo (RPS)
        """
        self.rate = rate
        self.interval = 1.0 / rate if rate > 0 else 0  # Intervalo entre mensagens
        self.last_call = 0.0
    
    def acquire(self, tokens: int = 1) -> float:
        """
        Aguarda até poder enviar a próxima mensagem.
        
        Retorna o tempo que esperou (em segundos).
        """
        if self.rate <= 0:
            return 0.0
        
        current_time = time.perf_counter()
        
        if self.last_call == 0:
            self.last_call = current_time
            return 0.0
        
        # Calcular tempo necessário para respeitar a taxa
        expected_time = self.last_call + (self.interval * tokens)
        
        # Se ainda não é hora, aguardar
        if expected_time > current_time:
            wait_time = expected_time - current_time
            time.sleep(wait_time)
            self.last_call = expected_time
            return wait_time
        else:
            self.last_call = current_time
            return 0.0
    
    def reset(self):
        """Reseta o rate limiter."""
        self.last_call = 0.0


class AdaptiveRateLimiter:
    """
    Rate limiter adaptativo que ajusta a taxa baseado no desempenho.
    
    Útil para encontrar o throughput máximo sustentável.
    """
    
    def __init__(self, initial_rate: float, target_latency_ms: float = 100):
        """
        Args:
            initial_rate: Taxa inicial em RPS
            target_latency_ms: Latência alvo em milissegundos
        """
        self.current_rate = initial_rate
        self.target_latency = target_latency_ms / 1000.0  # Converter para segundos
        self.rate_limiter = RateLimiter(initial_rate)
        self.latencies = []
        self.adjustment_interval = 100  # Ajustar a cada N mensagens
        
    def acquire(self) -> float:
        """Aguarda respeitando a taxa atual."""
        return self.rate_limiter.acquire()
    
    def record_latency(self, latency: float):
        """
        Registra uma latência e ajusta a taxa se necessário.
        
        Args:
            latency: Latência observada em segundos
        """
        self.latencies.append(latency)
        
        # Ajustar taxa a cada N mensagens
        if len(self.latencies) >= self.adjustment_interval:
            avg_latency = sum(self.latencies) / len(self.latencies)
            
            if avg_latency > self.target_latency * 1.2:
                # Latência muito alta, reduzir taxa
                self.current_rate *= 0.9
            elif avg_latency < self.target_latency * 0.8:
                # Latência baixa, aumentar taxa
                self.current_rate *= 1.1
            
            # Aplicar nova taxa
            self.rate_limiter = RateLimiter(self.current_rate)
            self.latencies.clear()
    
    def get_current_rate(self) -> float:
        """Retorna a taxa atual em RPS."""
        return self.current_rate


def calculate_messages_for_duration(rps: float, duration_seconds: float) -> int:
    """
    Calcula quantas mensagens enviar para uma taxa e duração.
    
    Args:
        rps: Taxa em requisições por segundo
        duration_seconds: Duração do teste em segundos
        
    Returns:
        Número total de mensagens a enviar
    """
    return int(rps * duration_seconds)


def calculate_actual_rps(messages_sent: int, duration_seconds: float) -> float:
    """
    Calcula o RPS real alcançado.
    
    Args:
        messages_sent: Número de mensagens enviadas
        duration_seconds: Duração real do teste
        
    Returns:
        RPS efetivo alcançado
    """
    if duration_seconds <= 0:
        return 0.0
    return messages_sent / duration_seconds
