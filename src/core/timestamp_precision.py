"""
Módulo para garantir precisão de timestamps e medição de tempo.

Baseado em:
- Python PEP 418: Add monotonic time, performance counter, and process time functions
- Gregg, B. (2013). Systems Performance, Chapter 6: CPUs

Este módulo fornece funções de alta precisão para medição de tempo,
essenciais para benchmarks confiáveis.
"""

import time
from typing import Tuple


def get_precise_timestamp() -> float:
    """
    Retorna um timestamp de alta precisão em segundos.
    
    Usa time.perf_counter() que:
    - É monotônico (não volta para trás)
    - Tem a maior resolução disponível
    - É ideal para medir intervalos curtos
    
    Returns:
        Timestamp em segundos com precisão de nanossegundos
        
    Referência:
        Python PEP 418 - https://peps.python.org/pep-0418/
    """
    return time.perf_counter()


def get_wall_clock_timestamp() -> float:
    """
    Retorna timestamp de wall-clock (tempo real).
    
    Usa time.time() que representa segundos desde Unix epoch.
    Útil para logging e correlação com eventos externos.
    
    Returns:
        Timestamp em segundos desde 1970-01-01 00:00:00 UTC
    """
    return time.time()


def measure_duration(start: float, end: float) -> float:
    """
    Calcula duração entre dois timestamps.
    
    Args:
        start: Timestamp inicial (de perf_counter ou time)
        end: Timestamp final
        
    Returns:
        Duração em segundos
    """
    duration = end - start
    
    # Validar que a duração é positiva
    if duration < 0:
        raise ValueError(f"Duração negativa detectada: {duration}s. "
                        "Possível problema com relógio do sistema.")
    
    return duration


def get_timestamp_pair() -> Tuple[float, float]:
    """
    Retorna par de timestamps (wall_clock, precise).
    
    Útil quando precisamos tanto do tempo real (para logs)
    quanto de alta precisão (para medições).
    
    Returns:
        Tupla (wall_clock_timestamp, precise_timestamp)
    """
    # Capturar ambos o mais próximo possível
    wall = time.time()
    precise = time.perf_counter()
    return wall, precise


def validate_timestamp(timestamp: float, max_age_seconds: float = 3600) -> bool:
    """
    Valida se um timestamp é razoável.
    
    Args:
        timestamp: Timestamp a validar
        max_age_seconds: Idade máxima aceitável em segundos
        
    Returns:
        True se o timestamp é válido
    """
    current = time.time()
    
    # Verificar se não é do futuro
    if timestamp > current + 1:  # 1 segundo de tolerância
        return False
    
    # Verificar se não é muito antigo
    if timestamp < current - max_age_seconds:
        return False
    
    return True


def format_duration(seconds: float) -> str:
    """
    Formata duração em formato legível.
    
    Args:
        seconds: Duração em segundos
        
    Returns:
        String formatada (ex: "1.234ms", "5.678s", "2m 30s")
    """
    if seconds < 0.001:
        return f"{seconds * 1_000_000:.2f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.3f}ms"
    elif seconds < 60:
        return f"{seconds:.3f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"


class PrecisionTimer:
    """
    Context manager para medição precisa de tempo.
    
    Exemplo:
        with PrecisionTimer() as timer:
            # código a medir
            pass
        print(f"Duração: {timer.duration}")
    """
    
    def __init__(self):
        self.start = 0.0
        self.end = 0.0
        self.duration = 0.0
    
    def __enter__(self):
        self.start = time.perf_counter()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end = time.perf_counter()
        self.duration = self.end - self.start
    
    def get_formatted_duration(self) -> str:
        """Retorna duração formatada."""
        return format_duration(self.duration)


# Constantes para validação
MIN_LATENCY_MS = 0.01  # Latência mínima realista (0.01ms)
MAX_LATENCY_MS = 30000  # Latência máxima aceitável (30s)

def validate_latency(latency_seconds: float) -> bool:
    """
    Valida se uma latência medida é realista.
    
    Args:
        latency_seconds: Latência em segundos
        
    Returns:
        True se a latência é válida
        
    Referência:
        Gregg, B. (2013). Systems Performance, p. 380
        - Network RTT local: 0.01-1ms
        - Network RTT internet: 10-300ms
        - Disk I/O: 0.1-10ms
    """
    latency_ms = latency_seconds * 1000
    
    return MIN_LATENCY_MS <= latency_ms <= MAX_LATENCY_MS
