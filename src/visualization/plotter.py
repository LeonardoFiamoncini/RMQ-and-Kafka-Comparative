"""
Módulo de geração de gráficos para análise de benchmarks

Este módulo fornece funcionalidades para criar visualizações científicas
dos resultados coletados durante os benchmarks.
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib
matplotlib.use('Agg')  # Backend não-interativo para servidor
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

from ..core.logger import Logger
from ..core.config import LOGS_DIR


class BenchmarkPlotter:
    """Gerador de gráficos para resultados de benchmark"""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Inicializa o gerador de gráficos
        
        Args:
            output_dir: Diretório para salvar gráficos (padrão: logs/plots)
        """
        self.logger = Logger.get_logger("visualization.plotter")
        self.output_dir = output_dir or LOGS_DIR / "plots"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar estilo dos gráficos
        sns.set_theme(style="whitegrid", palette="husl")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['figure.dpi'] = 300
        plt.rcParams['savefig.dpi'] = 300
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.labelsize'] = 12
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['xtick.labelsize'] = 10
        plt.rcParams['ytick.labelsize'] = 10
        plt.rcParams['legend.fontsize'] = 10
        
        self.logger.info(f"Gerador de gráficos inicializado. Output: {self.output_dir}")
    
    def load_benchmark_results(self, systems: List[str] = None) -> pd.DataFrame:
        """
        Carrega resultados consolidados de benchmark
        
        Args:
            systems: Lista de sistemas a carregar (padrão: baseline, rabbitmq, kafka)
            
        Returns:
            DataFrame com todos os resultados
        """
        if systems is None:
            systems = ["baseline", "rabbitmq", "kafka"]
        
        all_data = []
        
        for system in systems:
            benchmark_file = LOGS_DIR / system / "benchmark_results.csv"
            
            if benchmark_file.exists():
                try:
                    df = pd.read_csv(benchmark_file)
                    df['system'] = system
                    all_data.append(df)
                    self.logger.info(f"Carregados {len(df)} resultados de {system}")
                except Exception as e:
                    self.logger.error(f"Erro ao carregar {benchmark_file}: {e}")
        
        if all_data:
            combined = pd.concat(all_data, ignore_index=True)
            self.logger.info(f"Total de {len(combined)} resultados carregados")
            return combined
        else:
            self.logger.warning("Nenhum resultado encontrado")
            return pd.DataFrame()
    
    def load_latency_distribution(self, system: str, run_id: Optional[str] = None) -> pd.DataFrame:
        """
        Carrega distribuição de latências de uma execução específica
        
        Args:
            system: Sistema (baseline, rabbitmq, kafka)
            run_id: ID da execução (padrão: mais recente)
            
        Returns:
            DataFrame com latências individuais
        """
        system_dir = LOGS_DIR / system
        
        if not system_dir.exists():
            self.logger.error(f"Diretório {system_dir} não encontrado")
            return pd.DataFrame()
        
        # Encontrar run_id mais recente se não especificado
        if run_id is None:
            run_dirs = sorted(
                [d for d in system_dir.iterdir() if d.is_dir()],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            if not run_dirs:
                # Não é um erro crítico, apenas não há dados disponíveis
                self.logger.debug(f"Nenhum run_id encontrado em {system_dir} (pode ser normal se não houver dados)")
                return pd.DataFrame()
            run_dir = run_dirs[0]
        else:
            run_dir = system_dir / run_id
        
        # Carregar todos os arquivos de latência
        latency_files = list(run_dir.glob("*_latency.csv"))
        
        if not latency_files:
            # Não é um erro crítico, apenas não há dados disponíveis
            self.logger.debug(f"Nenhum arquivo de latência em {run_dir} (pode ser normal se não houver dados)")
            return pd.DataFrame()
        
        all_latencies = []
        for lat_file in latency_files:
            try:
                df = pd.read_csv(lat_file)
                all_latencies.append(df)
            except Exception as e:
                self.logger.error(f"Erro ao ler {lat_file}: {e}")
        
        if all_latencies:
            combined = pd.concat(all_latencies, ignore_index=True)
            combined['system'] = system
            self.logger.info(f"Carregadas {len(combined)} latências de {system}/{run_dir.name}")
            return combined
        else:
            return pd.DataFrame()
    
    def plot_latency_comparison(self, save_as: str = "latency_comparison.png") -> Path:
        """
        Gráfico de comparação de latências entre sistemas
        
        Args:
            save_as: Nome do arquivo de saída
            
        Returns:
            Path do arquivo salvo
        """
        self.logger.info("Gerando gráfico de comparação de latências...")
        
        df = self.load_benchmark_results()
        
        if df.empty:
            self.logger.error("Sem dados para plotar")
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Comparação de Latências entre Sistemas', fontsize=16, fontweight='bold')
        
        # 1. Latência média por sistema
        ax1 = axes[0, 0]
        sns.barplot(data=df, x='system', y='latency_avg', ax=ax1, errorbar='sd')
        ax1.set_title('T (Latência Média) por Sistema')
        ax1.set_xlabel('Sistema')
        ax1.set_ylabel('Latência Média (segundos)')
        # Definir ticks antes de definir labels
        ax1.set_xticks(range(len(df)))
        ax1.set_xticklabels(df['system'].values)
        
        # 2. Percentis de latência
        ax2 = axes[0, 1]
        percentil_data = df[['system', 'latency_50', 'latency_95', 'latency_99']].melt(
            id_vars='system', var_name='Percentil', value_name='Latência'
        )
        sns.barplot(data=percentil_data, x='system', y='Latência', hue='Percentil', ax=ax2)
        ax2.set_title('Percentis de Latência (P50, P95, P99)')
        ax2.set_xlabel('Sistema')
        ax2.set_ylabel('Latência (segundos)')
        ax2.legend(title='Percentil', labels=['P50', 'P95', 'P99'])
        
        # 3. Latência por volume de mensagens
        ax3 = axes[1, 0]
        if 'messages' in df.columns and len(df['messages'].unique()) > 1:
            sns.lineplot(data=df, x='messages', y='latency_avg', hue='system', 
                        marker='o', ax=ax3, markersize=8)
            ax3.set_title('Latência vs Volume de Mensagens')
            ax3.set_xlabel('Número de Mensagens')
            ax3.set_ylabel('Latência Média (segundos)')
            ax3.set_xscale('log')
            ax3.legend(title='Sistema')
        else:
            ax3.text(0.5, 0.5, 'Dados insuficientes\npara este gráfico', 
                    ha='center', va='center', fontsize=12)
            ax3.set_title('Latência vs Volume (dados insuficientes)')
        
        # 4. Box plot de latências
        ax4 = axes[1, 1]
        # Criar dados para box plot usando percentis
        box_data = []
        for system in df['system'].unique():
            sys_data = df[df['system'] == system]
            for _, row in sys_data.iterrows():
                # Aproximar distribuição usando percentis
                box_data.extend([
                    {'system': system, 'latency': row['latency_50']},
                    {'system': system, 'latency': row['latency_95']},
                    {'system': system, 'latency': row['latency_99']},
                ])
        
        if box_data:
            box_df = pd.DataFrame(box_data)
            sns.boxplot(data=box_df, x='system', y='latency', ax=ax4)
            ax4.set_title('Distribuição de Latências')
            ax4.set_xlabel('Sistema')
            ax4.set_ylabel('Latência (segundos)')
        
        plt.tight_layout()
        
        output_path = self.output_dir / save_as
        plt.savefig(output_path, bbox_inches='tight', facecolor='white')
        plt.close()
        
        self.logger.info(f"Gráfico salvo em: {output_path}")
        return output_path
    
    def plot_throughput_comparison(self, save_as: str = "throughput_comparison.png") -> Path:
        """
        Gráfico de comparação de throughput entre sistemas
        
        Args:
            save_as: Nome do arquivo de saída
            
        Returns:
            Path do arquivo salvo
        """
        self.logger.info("Gerando gráfico de comparação de throughput...")
        
        df = self.load_benchmark_results()
        
        if df.empty:
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Comparação de Throughput (V) entre Sistemas', fontsize=16, fontweight='bold')
        
        # 1. Throughput médio por sistema
        ax1 = axes[0, 0]
        sns.barplot(data=df, x='system', y='throughput', ax=ax1, errorbar='sd')
        ax1.set_title('V (Throughput) por Sistema')
        ax1.set_xlabel('Sistema')
        ax1.set_ylabel('Throughput (mensagens/segundo)')
        # Definir ticks antes de definir labels
        ax1.set_xticks(range(len(df)))
        ax1.set_xticklabels(df['system'].values)
        
        # 2. Throughput vs Número de Produtores
        ax2 = axes[0, 1]
        if 'num_producers' in df.columns:
            sns.lineplot(data=df, x='num_producers', y='throughput', hue='system',
                        marker='o', ax=ax2, markersize=8)
            ax2.set_title('Throughput vs Número de Produtores')
            ax2.set_xlabel('Número de Produtores')
            ax2.set_ylabel('Throughput (msg/s)')
            ax2.legend(title='Sistema')
        
        # 3. Throughput vs Número de Mensagens
        ax3 = axes[1, 0]
        if 'messages' in df.columns and len(df['messages'].unique()) > 1:
            sns.lineplot(data=df, x='messages', y='throughput', hue='system',
                        marker='o', ax=ax3, markersize=8)
            ax3.set_title('Throughput vs Volume de Mensagens')
            ax3.set_xlabel('Número de Mensagens')
            ax3.set_ylabel('Throughput (msg/s)')
            ax3.set_xscale('log')
            ax3.legend(title='Sistema')
        else:
            ax3.text(0.5, 0.5, 'Dados insuficientes\npara este gráfico',
                    ha='center', va='center', fontsize=12)
        
        # 4. Eficiência (throughput / latência)
        ax4 = axes[1, 1]
        df_copy = df.copy()
        df_copy['efficiency'] = df_copy['throughput'] / (df_copy['latency_avg'] + 0.001)  # Evitar divisão por zero
        sns.barplot(data=df_copy, x='system', y='efficiency', ax=ax4, errorbar='sd')
        ax4.set_title('Eficiência (Throughput / Latência)')
        ax4.set_xlabel('Sistema')
        ax4.set_ylabel('Eficiência (msg/s²)')
        
        plt.tight_layout()
        
        output_path = self.output_dir / save_as
        plt.savefig(output_path, bbox_inches='tight', facecolor='white')
        plt.close()
        
        self.logger.info(f"Gráfico salvo em: {output_path}")
        return output_path
    
    def plot_latency_distribution(self, system: str, run_id: Optional[str] = None,
                                  save_as: Optional[str] = None) -> Path:
        """
        Gráfico de distribuição de latências de uma execução
        
        Args:
            system: Sistema a plotar
            run_id: ID da execução (padrão: mais recente)
            save_as: Nome do arquivo (padrão: auto-gerado)
            
        Returns:
            Path do arquivo salvo
        """
        self.logger.info(f"Gerando distribuição de latências para {system}...")
        
        df = self.load_latency_distribution(system, run_id)
        
        if df.empty:
            return None
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle(f'Distribuição de Latências - {system.upper()}', 
                     fontsize=16, fontweight='bold')
        
        latencies = df['latency_seconds'].values
        
        # 1. Histograma
        ax1 = axes[0, 0]
        ax1.hist(latencies, bins=50, edgecolor='black', alpha=0.7)
        ax1.set_title('Histograma de Latências')
        ax1.set_xlabel('Latência (segundos)')
        ax1.set_ylabel('Frequência')
        ax1.axvline(np.mean(latencies), color='r', linestyle='--', label=f'Média: {np.mean(latencies):.6f}s')
        ax1.axvline(np.median(latencies), color='g', linestyle='--', label=f'Mediana: {np.median(latencies):.6f}s')
        ax1.legend()
        
        # 2. Box plot
        ax2 = axes[0, 1]
        ax2.boxplot(latencies, vert=True)
        ax2.set_title('Box Plot de Latências')
        ax2.set_ylabel('Latência (segundos)')
        ax2.set_xticklabels([system.capitalize()])
        
        # Adicionar estatísticas no gráfico
        stats_text = f"n = {len(latencies)}\n"
        stats_text += f"μ = {np.mean(latencies):.6f}s\n"
        stats_text += f"σ = {np.std(latencies):.6f}s\n"
        stats_text += f"Min = {np.min(latencies):.6f}s\n"
        stats_text += f"Max = {np.max(latencies):.6f}s"
        ax2.text(1.15, np.median(latencies), stats_text,
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=9)
        
        # 3. CDF (Cumulative Distribution Function)
        ax3 = axes[1, 0]
        sorted_lat = np.sort(latencies)
        cdf = np.arange(1, len(sorted_lat) + 1) / len(sorted_lat)
        ax3.plot(sorted_lat, cdf, linewidth=2)
        ax3.set_title('CDF - Função de Distribuição Acumulada')
        ax3.set_xlabel('Latência (segundos)')
        ax3.set_ylabel('Probabilidade Acumulada')
        ax3.grid(True, alpha=0.3)
        
        # Marcar percentis importantes
        p50_val = np.percentile(latencies, 50)
        p95_val = np.percentile(latencies, 95)
        p99_val = np.percentile(latencies, 99)
        
        ax3.axhline(y=0.50, color='g', linestyle='--', alpha=0.5)
        ax3.axhline(y=0.95, color='orange', linestyle='--', alpha=0.5)
        ax3.axhline(y=0.99, color='r', linestyle='--', alpha=0.5)
        ax3.axvline(x=p50_val, color='g', linestyle='--', alpha=0.5, label=f'P50={p50_val:.6f}s')
        ax3.axvline(x=p95_val, color='orange', linestyle='--', alpha=0.5, label=f'P95={p95_val:.6f}s')
        ax3.axvline(x=p99_val, color='r', linestyle='--', alpha=0.5, label=f'P99={p99_val:.6f}s')
        ax3.legend(loc='lower right')
        
        # 4. Série temporal (latência ao longo do tempo)
        ax4 = axes[1, 1]
        ax4.plot(range(len(latencies)), latencies, alpha=0.6, linewidth=1)
        ax4.set_title('Latências ao Longo do Tempo')
        ax4.set_xlabel('Índice da Mensagem')
        ax4.set_ylabel('Latência (segundos)')
        ax4.axhline(y=np.mean(latencies), color='r', linestyle='--', 
                   label=f'Média: {np.mean(latencies):.6f}s')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_as is None:
            save_as = f"latency_distribution_{system}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        output_path = self.output_dir / save_as
        plt.savefig(output_path, bbox_inches='tight', facecolor='white')
        plt.close()
        
        self.logger.info(f"Gráfico salvo em: {output_path}")
        return output_path
    
    def plot_comparative_summary(self, save_as: str = "comparative_summary.png") -> Path:
        """
        Gráfico resumo comparativo com todas as métricas principais
        
        Args:
            save_as: Nome do arquivo de saída
            
        Returns:
            Path do arquivo salvo
        """
        self.logger.info("Gerando gráfico resumo comparativo...")
        
        df = self.load_benchmark_results()
        
        if df.empty:
            return None
        
        # Pegar última execução de cada sistema
        latest_data = df.groupby('system').tail(1)
        
        fig = plt.figure(figsize=(16, 10))
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        fig.suptitle('Resumo Comparativo - RabbitMQ vs Kafka vs HTTP Baseline',
                     fontsize=18, fontweight='bold')
        
        # 1. Latência Média (grande, destaque)
        ax1 = fig.add_subplot(gs[0, :2])
        systems = latest_data['system'].values
        latencies = latest_data['latency_avg'].values
        colors = ['#3498db', '#e74c3c', '#2ecc71']
        bars = ax1.bar(systems, latencies, color=colors, edgecolor='black', linewidth=1.5)
        ax1.set_title('T (Tempo de Permanência na Fila) - Latência Média', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Latência (segundos)', fontsize=12)
        
        # Adicionar valores nas barras
        for bar, val in zip(bars, latencies):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.6f}s',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 2. Throughput (grande, destaque)
        ax2 = fig.add_subplot(gs[0, 2])
        throughputs = latest_data['throughput'].values
        bars2 = ax2.bar(systems, throughputs, color=colors, edgecolor='black', linewidth=1.5)
        ax2.set_title('V (Vazão) - Throughput', fontsize=14, fontweight='bold')
        ax2.set_ylabel('Throughput (msg/s)', fontsize=12)
        
        for bar, val in zip(bars2, throughputs):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:.2f}',
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
        
        # 3. Trade-off Latência vs Throughput
        ax3 = fig.add_subplot(gs[1, :])
        # Ajustar cores para número de sistemas
        scatter_colors = colors[:len(latest_data)]
        scatter = ax3.scatter(latest_data['latency_avg'], latest_data['throughput'],
                            s=500, c=scatter_colors, alpha=0.6, edgecolors='black', linewidth=2)
        ax3.set_title('Trade-off: Latência vs Throughput', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Latência (segundos)', fontsize=12)
        ax3.set_ylabel('Throughput (msg/s)', fontsize=12)
        ax3.grid(True, alpha=0.3)
        
        # Anotar pontos
        for idx, row in latest_data.iterrows():
            ax3.annotate(row['system'].capitalize(),
                        (row['latency_avg'], row['throughput']),
                        xytext=(10, 10), textcoords='offset points',
                        fontsize=11, fontweight='bold',
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='yellow', alpha=0.3))
        
        # 4. Percentis comparativos
        ax4 = fig.add_subplot(gs[2, 0])
        percentis = ['latency_50', 'latency_95', 'latency_99']
        x = np.arange(len(systems))
        width = 0.25
        
        for i, p in enumerate(percentis):
            values = latest_data[p].values
            ax4.bar(x + i*width, values, width, label=p.replace('latency_', 'P'),
                   edgecolor='black')
        
        ax4.set_title('Percentis de Latência (P50, P95, P99)', fontsize=12)
        ax4.set_ylabel('Latência (segundos)')
        ax4.set_xticks(x + width)
        ax4.set_xticklabels(systems)
        ax4.legend()
        
        # 5. Tabela de métricas
        ax5 = fig.add_subplot(gs[2, 1:])
        ax5.axis('off')
        
        table_data = []
        table_headers = ['Sistema', 'T Médio', 'P95', 'V (msg/s)', 'Mensagens']
        
        for _, row in latest_data.iterrows():
            table_data.append([
                row['system'].capitalize(),
                f"{row['latency_avg']:.6f}s",
                f"{row['latency_95']:.6f}s",
                f"{row['throughput']:.2f}",
                f"{int(row['messages'])}"
            ])
        
        table = ax5.table(cellText=table_data, colLabels=table_headers,
                         cellLoc='center', loc='center',
                         bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Estilizar cabeçalho
        for (i, j), cell in table.get_celld().items():
            if i == 0:
                cell.set_facecolor('#3498db')
                cell.set_text_props(weight='bold', color='white')
            else:
                cell.set_facecolor('#ecf0f1' if i % 2 == 0 else 'white')
        
        ax5.set_title('Resumo de Métricas', fontsize=12, fontweight='bold', pad=20)
        
        # Usar subplots_adjust para evitar warning com tabelas
        # tight_layout pode causar problemas com tabelas, então usamos ajuste manual
        plt.subplots_adjust(left=0.1, right=0.95, top=0.93, bottom=0.1, hspace=0.3, wspace=0.3)
        
        output_path = self.output_dir / save_as
        plt.savefig(output_path, bbox_inches='tight', facecolor='white')
        plt.close()
        
        self.logger.info(f"Gráfico salvo em: {output_path}")
        return output_path
    
    def plot_all_for_system(self, system: str, run_id: Optional[str] = None) -> List[Path]:
        """
        Gera todos os gráficos para um sistema específico
        
        Args:
            system: Sistema a plotar
            run_id: ID da execução (padrão: mais recente)
            
        Returns:
            Lista de paths dos gráficos gerados
        """
        self.logger.info(f"Gerando todos os gráficos para {system}...")
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        plots = []
        
        # Distribuição de latências
        plot_path = self.plot_latency_distribution(
            system, run_id,
            save_as=f"{system}_latency_dist_{timestamp}.png"
        )
        if plot_path:
            plots.append(plot_path)
        
        return plots
    
    def generate_all_plots(self) -> Dict[str, List[Path]]:
        """
        Gera todos os gráficos possíveis para todos os sistemas
        
        Returns:
            Dicionário com paths dos gráficos gerados
        """
        self.logger.info("Gerando todos os gráficos...")
        
        plots = {
            'comparative': [],
            'baseline': [],
            'rabbitmq': [],
            'kafka': []
        }
        
        # Gráficos comparativos
        lat_comp = self.plot_latency_comparison()
        if lat_comp:
            plots['comparative'].append(lat_comp)
        
        thr_comp = self.plot_throughput_comparison()
        if thr_comp:
            plots['comparative'].append(thr_comp)
        
        summary = self.plot_comparative_summary()
        if summary:
            plots['comparative'].append(summary)
        
        # Gráficos individuais por sistema
        for system in ['baseline', 'rabbitmq', 'kafka']:
            system_plots = self.plot_all_for_system(system)
            plots[system].extend(system_plots)
        
        # Contar total
        total = sum(len(v) for v in plots.values())
        self.logger.info(f"Total de {total} gráficos gerados")
        
        return plots


def main():
    """Função principal para execução standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Gerador de gráficos para benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--system", choices=["baseline", "rabbitmq", "kafka", "all"],
                       default="all", help="Sistema a plotar")
    parser.add_argument("--output", type=str, default=None,
                       help="Diretório de saída para gráficos")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output) if args.output else None
    plotter = BenchmarkPlotter(output_dir=output_dir)
    
    if args.system == "all":
        plots = plotter.generate_all_plots()
        
        print("\n" + "="*70)
        print("  📊 GRÁFICOS GERADOS")
        print("="*70)
        
        for category, paths in plots.items():
            if paths:
                print(f"\n{category.upper()}:")
                for path in paths:
                    print(f"  ✅ {path.name}")
        
        print(f"\n📁 Todos os gráficos salvos em: {plotter.output_dir}")
        print("="*70)
    else:
        plotter.plot_all_for_system(args.system)
        print(f"✅ Gráficos de {args.system} gerados em {plotter.output_dir}")


if __name__ == "__main__":
    main()

