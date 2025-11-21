"""
Cálculo correto de percentis segundo as melhores práticas.

Baseado em:
- Hyndman, R.J. & Fan, Y. (1996). Sample Quantiles in Statistical Packages.
- Jain, R. (1991). The Art of Computer Systems Performance Analysis.

Este módulo implementa o método 7 de Hyndman & Fan, que é o padrão
usado pelo NumPy, R e outras ferramentas estatísticas.
"""

from typing import List, Union


def calculate_percentile(sorted_data: List[float], percentile: float) -> float:
    """
    Calcula o percentil de uma lista ordenada de valores.
    
    Implementa o método 7 de Hyndman & Fan (1996), que é o método
    padrão usado pelo NumPy (numpy.percentile com interpolation='linear').
    
    Args:
        sorted_data: Lista de valores já ordenados
        percentile: Percentil desejado (0-100)
        
    Returns:
        Valor do percentil calculado
        
    Referências:
        Hyndman, R.J. & Fan, Y. (1996). Sample Quantiles in Statistical Packages.
        The American Statistician, 50(4), 361-365.
    """
    n = len(sorted_data)
    
    # Casos especiais
    if n == 0:
        return 0.0
    if n == 1:
        return sorted_data[0]
    if percentile <= 0:
        return sorted_data[0]
    if percentile >= 100:
        return sorted_data[-1]
    
    # Método 7 de Hyndman & Fan (padrão do NumPy)
    # Posição no array (indexado de 0)
    h = (n - 1) * (percentile / 100.0)
    
    # Índice inferior
    i = int(h)
    
    # Fração para interpolação
    f = h - i
    
    # Se estamos no último elemento
    if i >= n - 1:
        return sorted_data[-1]
    
    # Interpolação linear entre valores adjacentes
    lower = sorted_data[i]
    upper = sorted_data[i + 1]
    
    return lower + f * (upper - lower)


def calculate_metrics_statistics(latencies: List[float], duration: float) -> dict:
    """
    Calcula todas as métricas estatísticas de latência e throughput.
    
    Args:
        latencies: Lista de latências em segundos
        duration: Duração total em segundos
        
    Returns:
        Dicionário com todas as métricas calculadas
        
    Referências:
        Jain, R. (1991). The Art of Computer Systems Performance Analysis, p. 72.
    """
    if not latencies or duration <= 0:
        return {
            'throughput': 0.0,
            'p50': 0.0,
            'p95': 0.0,
            'p99': 0.0,
            'p99_9': 0.0,
            'avg': 0.0,
            'min': 0.0,
            'max': 0.0,
            'count': 0
        }
    
    # Ordenar latências (necessário para percentis)
    sorted_latencies = sorted(latencies)
    n = len(sorted_latencies)
    
    # Throughput (Jain, 1991, p. 72)
    # X = C / T onde X = throughput, C = count, T = time
    throughput = n / duration
    
    # Percentis usando o método correto
    p50 = calculate_percentile(sorted_latencies, 50)    # Mediana
    p95 = calculate_percentile(sorted_latencies, 95)    # 95º percentil
    p99 = calculate_percentile(sorted_latencies, 99)    # 99º percentil
    p99_9 = calculate_percentile(sorted_latencies, 99.9) # 99.9º percentil (tail latency)
    
    # Estatísticas adicionais
    avg = sum(sorted_latencies) / n
    min_val = sorted_latencies[0]
    max_val = sorted_latencies[-1]
    
    return {
        'throughput': throughput,
        'p50': p50,
        'p95': p95,
        'p99': p99,
        'p99_9': p99_9,
        'avg': avg,
        'min': min_val,
        'max': max_val,
        'count': n
    }


def validate_sample_size(n: int, percentile: float) -> bool:
    """
    Valida se o tamanho da amostra é suficiente para o percentil desejado.
    
    Segundo Jain (1991) e Gregg (2013), são necessárias pelo menos
    100/(100-p) observações para estimar o percentil p com confiança.
    
    Args:
        n: Número de amostras
        percentile: Percentil desejado (0-100)
        
    Returns:
        True se o tamanho é adequado, False caso contrário
        
    Referências:
        Gregg, B. (2013). Systems Performance, p. 68.
    """
    if percentile >= 100:
        return False
    
    # Mínimo recomendado de observações
    min_required = 100 / (100 - percentile)
    
    # Para P99 precisa de pelo menos 100 observações
    # Para P99.9 precisa de pelo menos 1000 observações
    # Para P99.99 precisa de pelo menos 10000 observações
    
    return n >= min_required
