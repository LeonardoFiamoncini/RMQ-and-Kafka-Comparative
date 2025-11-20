#!/usr/bin/env python3
"""
Script para gerar todos os gráficos de análise do benchmark

Uso:
    python generate_plots.py                    # Gerar todos os gráficos
    python generate_plots.py --system rabbitmq  # Gráficos de um sistema específico
    python generate_plots.py --output plots/    # Especificar diretório de saída
"""

import argparse
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.visualization.plotter import BenchmarkPlotter
from src.core.logger import Logger


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(
        description="Gerador de gráficos para análise de benchmarks",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python generate_plots.py                    # Gerar todos os gráficos
  python generate_plots.py --system rabbitmq  # Apenas RabbitMQ
  python generate_plots.py --output graficos/ # Saída personalizada
        """
    )
    
    parser.add_argument(
        "--system",
        choices=["baseline", "rabbitmq", "kafka", "all"],
        default="all",
        help="Sistema para gerar gráficos"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Diretório de saída (padrão: logs/plots)"
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="ID específico da execução (padrão: mais recente)"
    )
    
    args = parser.parse_args()
    
    logger = Logger.get_logger("generate_plots")
    
    # Inicializar gerador
    output_dir = Path(args.output) if args.output else None
    plotter = BenchmarkPlotter(output_dir=output_dir)
    
    logger.info("="*70)
    logger.info("  📊 GERADOR DE GRÁFICOS DE BENCHMARK")
    logger.info("="*70)
    logger.info(f"Sistema: {args.system}")
    logger.info(f"Saída: {plotter.output_dir}")
    logger.info("")
    
    if args.system == "all":
        # Gerar todos os gráficos
        logger.info("Gerando todos os gráficos disponíveis...")
        plots = plotter.generate_all_plots()
        
        print("\n" + "="*70)
        print("  📊 GRÁFICOS GERADOS")
        print("="*70 + "\n")
        
        total = 0
        for category, paths in plots.items():
            if paths:
                print(f"{category.upper()}:")
                for path in paths:
                    print(f"  ✅ {path.name}")
                    total += 1
                print()
        
        print(f"📁 Total: {total} gráfico(s) salvo(s) em: {plotter.output_dir}")
        print("="*70)
        
    else:
        # Gerar gráficos de um sistema específico
        logger.info(f"Gerando gráficos para {args.system}...")
        plots = plotter.plot_all_for_system(args.system, args.run_id)
        
        print("\n" + "="*70)
        print(f"  📊 GRÁFICOS DE {args.system.upper()}")
        print("="*70 + "\n")
        
        if plots:
            for path in plots:
                print(f"  ✅ {path.name}")
            print(f"\n📁 Salvos em: {plotter.output_dir}")
        else:
            print("  ⚠️  Nenhum gráfico gerado (verificar dados)")
        
        print("="*70)
    
    logger.info("✅ Geração de gráficos concluída")


if __name__ == "__main__":
    main()

