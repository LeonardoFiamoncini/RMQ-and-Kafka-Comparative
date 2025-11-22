#!/usr/bin/env python3
"""
Gerador de Gráficos para o TCC
Objetivo: Criar visualizações comparativas entre Baseline, RabbitMQ e Kafka
"""

import csv
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# Configuração de estilo
plt.style.use('seaborn-v0_8-darkgrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11

# Diretórios
LOGS_DIR = Path("logs")
PLOTS_DIR = LOGS_DIR / "plots"
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

# Cores para cada tecnologia
COLORS = {
    'baseline': '#3498db',  # Azul
    'rabbitmq': '#e74c3c',  # Vermelho
    'kafka': '#2ecc71'      # Verde
}

def load_benchmark_data():
    """Carrega dados de benchmark de todos os sistemas"""
    data = {
        'baseline': {'pequeno': [], 'medio': [], 'grande': []},
        'rabbitmq': {'pequeno': [], 'medio': [], 'grande': []},
        'kafka': {'pequeno': [], 'medio': [], 'grande': []}
    }
    
    for tech in ['baseline', 'rabbitmq', 'kafka']:
        csv_file = LOGS_DIR / tech / "benchmark_results.csv"
        if not csv_file.exists():
            print(f"Arquivo não encontrado: {csv_file}")
            continue
        
        with open(csv_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                porte = row.get('porte', '')
                if porte in data[tech]:
                    data[tech][porte].append({
                        'throughput': float(row.get('throughput', 0)),
                        'latency_95': float(row.get('latency_95', 0)),
                        'latency_99': float(row.get('latency_99', 0)),
                        'messages': int(row.get('messages_processed', 0))
                    })
    
    # Calcular médias se houver múltiplas execuções
    aggregated = {}
    for tech in data:
        aggregated[tech] = {}
        for porte in data[tech]:
            if data[tech][porte]:
                metrics = data[tech][porte]
                aggregated[tech][porte] = {
                    'throughput': np.mean([m['throughput'] for m in metrics]),
                    'latency_95': np.mean([m['latency_95'] for m in metrics]),
                    'latency_99': np.mean([m['latency_99'] for m in metrics]),
                    'messages': np.mean([m['messages'] for m in metrics])
                }
            else:
                aggregated[tech][porte] = {
                    'throughput': 0,
                    'latency_95': 0,
                    'latency_99': 0,
                    'messages': 0
                }
    
    return aggregated

def plot_throughput_comparison(data):
    """Gráfico de comparação de throughput por porte"""
    fig, ax = plt.subplots(figsize=(12, 8))
    
    portes = ['pequeno', 'medio', 'grande']
    x = np.arange(len(portes))
    width = 0.25
    
    # Barras para cada tecnologia
    baseline_values = [data['baseline'][p]['throughput'] for p in portes]
    rabbitmq_values = [data['rabbitmq'][p]['throughput'] for p in portes]
    kafka_values = [data['kafka'][p]['throughput'] for p in portes]
    
    bars1 = ax.bar(x - width, baseline_values, width, label='Baseline HTTP', color=COLORS['baseline'])
    bars2 = ax.bar(x, rabbitmq_values, width, label='RabbitMQ', color=COLORS['rabbitmq'])
    bars3 = ax.bar(x + width, kafka_values, width, label='Kafka', color=COLORS['kafka'])
    
    # Adicionar valores nas barras
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}', ha='center', va='bottom', fontsize=10)
    
    ax.set_xlabel('Porte da Aplicação', fontsize=12, fontweight='bold')
    ax.set_ylabel('Throughput (msg/s)', fontsize=12, fontweight='bold')
    ax.set_title('Comparação de Throughput por Porte\n(Maior é melhor)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['Pequeno\n(100 msgs)', 'Médio\n(1.000 msgs)', 'Grande\n(10.000 msgs)'])
    ax.legend(loc='upper left', fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    filename = PLOTS_DIR / f"throughput_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Gráfico salvo: {filename}")
    plt.close()

def plot_latency_comparison(data):
    """Gráfico de comparação de latências por porte"""
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    
    percentiles = ['P95', 'P99']
    portes = ['pequeno', 'medio', 'grande']
    
    for idx, porte in enumerate(portes):
        ax = axes[idx]
        
        # Dados de latência em milissegundos
        baseline_latencies = [
            data['baseline'][porte]['latency_95'] * 1000,
            data['baseline'][porte]['latency_99'] * 1000
        ]
        rabbitmq_latencies = [
            data['rabbitmq'][porte]['latency_95'] * 1000,
            data['rabbitmq'][porte]['latency_99'] * 1000
        ]
        kafka_latencies = [
            data['kafka'][porte]['latency_95'] * 1000,
            data['kafka'][porte]['latency_99'] * 1000
        ]
        
        x = np.arange(len(percentiles))
        width = 0.25
        
        bars1 = ax.bar(x - width, baseline_latencies, width, label='Baseline', color=COLORS['baseline'])
        bars2 = ax.bar(x, rabbitmq_latencies, width, label='RabbitMQ', color=COLORS['rabbitmq'])
        bars3 = ax.bar(x + width, kafka_latencies, width, label='Kafka', color=COLORS['kafka'])
        
        # Adicionar valores nas barras
        for bars in [bars1, bars2, bars3]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{height:.1f}', ha='center', va='bottom', fontsize=9)
        
        ax.set_xlabel('Percentil', fontsize=11)
        ax.set_ylabel('Latência (ms)' if idx == 0 else '', fontsize=11)
        msgs_map = {"pequeno": "100", "medio": "1.000", "grande": "10.000"}
        ax.set_title(f'Porte {porte.capitalize()}\n({msgs_map[porte]} msgs)', 
                    fontsize=12, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(percentiles)
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
    
    fig.suptitle('Comparação de Latências por Porte\n(Menor é melhor)', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    filename = PLOTS_DIR / f"latency_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Gráfico salvo: {filename}")
    plt.close()

def plot_summary_matrix(data):
    """Matriz resumo com todos os resultados"""
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    
    portes = ['pequeno', 'medio', 'grande']
    techs = ['baseline', 'rabbitmq', 'kafka']
    
    # Linha 1: Throughput por porte
    for idx, porte in enumerate(portes):
        ax = axes[0, idx]
        values = [data[tech][porte]['throughput'] for tech in techs]
        bars = ax.bar(techs, values, color=[COLORS[t] for t in techs])
        
        for bar, value in zip(bars, values):
            if value > 0:
                ax.text(bar.get_x() + bar.get_width()/2., value,
                       f'{value:.1f}', ha='center', va='bottom')
        
        ax.set_title(f'Throughput - Porte {porte.capitalize()}', fontweight='bold')
        ax.set_ylabel('msg/s')
        ax.set_xticklabels(['Baseline', 'RabbitMQ', 'Kafka'])
        ax.grid(True, alpha=0.3)
    
    # Linha 2: Latência P99 por porte
    for idx, porte in enumerate(portes):
        ax = axes[1, idx]
        values = [data[tech][porte]['latency_99'] * 1000 for tech in techs]  # Converter para ms
        bars = ax.bar(techs, values, color=[COLORS[t] for t in techs])
        
        for bar, value in zip(bars, values):
            if value > 0:
                ax.text(bar.get_x() + bar.get_width()/2., value,
                       f'{value:.1f}', ha='center', va='bottom')
        
        ax.set_title(f'Latência P99 - Porte {porte.capitalize()}', fontweight='bold')
        ax.set_ylabel('ms')
        ax.set_xticklabels(['Baseline', 'RabbitMQ', 'Kafka'])
        ax.grid(True, alpha=0.3)
    
    fig.suptitle('Matriz de Resultados - TCC Benchmark\nComparação entre Baseline, RabbitMQ e Kafka', 
                fontsize=14, fontweight='bold', y=1.02)
    
    plt.tight_layout()
    filename = PLOTS_DIR / f"summary_matrix_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"Gráfico salvo: {filename}")
    plt.close()

def generate_summary_table(data):
    """Gera tabela resumo em formato texto"""
    filename = PLOTS_DIR / f"summary_table_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(filename, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("RESUMO DOS RESULTADOS - TCC BENCHMARK\n")
        f.write("=" * 80 + "\n\n")
        
        for porte in ['pequeno', 'medio', 'grande']:
            msgs = {'pequeno': '100', 'medio': '1.000', 'grande': '10.000'}[porte]
            f.write(f"PORTE {porte.upper()} ({msgs} mensagens)\n")
            f.write("-" * 40 + "\n")
            
            # Cabeçalho
            f.write(f"{'Tecnologia':<12} {'Throughput':<15} {'P95 (ms)':<12} {'P99 (ms)':<12}\n")
            f.write("-" * 40 + "\n")
            
            # Dados
            for tech in ['baseline', 'rabbitmq', 'kafka']:
                throughput = data[tech][porte]['throughput']
                p95 = data[tech][porte]['latency_95'] * 1000
                p99 = data[tech][porte]['latency_99'] * 1000
                
                f.write(f"{tech.capitalize():<12} {throughput:<15.2f} {p95:<12.2f} {p99:<12.2f}\n")
            
            f.write("\n")
        
        # Análise dos resultados
        f.write("=" * 80 + "\n")
        f.write("ANÁLISE DOS RESULTADOS\n")
        f.write("=" * 80 + "\n\n")
        
        # Melhor throughput por porte
        for porte in ['pequeno', 'medio', 'grande']:
            best_tech = max(['baseline', 'rabbitmq', 'kafka'], 
                          key=lambda t: data[t][porte]['throughput'])
            f.write(f"Melhor throughput em porte {porte}: {best_tech.upper()}\n")
        
        f.write("\n")
        
        # Menor latência P95 por porte
        for porte in ['pequeno', 'medio', 'grande']:
            best_tech = min(['baseline', 'rabbitmq', 'kafka'], 
                          key=lambda t: data[t][porte]['latency_95'] if data[t][porte]['latency_95'] > 0 else float('inf'))
            f.write(f"Menor latência P95 em porte {porte}: {best_tech.upper()}\n")
    
    print(f"Tabela resumo salva: {filename}")

def main():
    """Função principal"""
    print("\nGERADOR DE GRÁFICOS - TCC BENCHMARK")
    print("=" * 50)
    
    # Carregar dados
    print("Carregando dados dos benchmarks...")
    data = load_benchmark_data()
    
    # Verificar se há dados
    has_data = False
    for tech in data:
        for porte in data[tech]:
            if data[tech][porte]['throughput'] > 0:
                has_data = True
                break
    
    if not has_data:
        print("Nenhum dado de benchmark encontrado!")
        print("Execute primeiro: ./execute_all.sh")
        return
    
    # Gerar gráficos
    print("\nGerando visualizações...")
    
    plot_throughput_comparison(data)
    plot_latency_comparison(data)
    plot_summary_matrix(data)
    generate_summary_table(data)
    
    print(f"\nTodos os gráficos foram gerados em: {PLOTS_DIR}")
    print("\nGráficos gerados:")
    print("  • throughput_comparison_*.png - Comparação de throughput")
    print("  • latency_comparison_*.png - Comparação de latências")
    print("  • summary_matrix_*.png - Matriz resumo")
    print("  • summary_table_*.txt - Tabela com todos os resultados")

if __name__ == "__main__":
    main()