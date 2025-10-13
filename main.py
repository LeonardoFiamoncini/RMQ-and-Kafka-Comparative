"""
Ponto de entrada principal do sistema de benchmark
"""
import argparse
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.logger import Logger
from src.orchestration.benchmark import BenchmarkOrchestrator
from src.orchestration.chaos import ChaosEngineer
from src.brokers.baseline.server import BaselineServer
import threading

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Sistema de Benchmark RabbitMQ vs Kafka')
    
    # Argumentos principais
    parser.add_argument("--count", type=int, default=1000, help="Quantidade de mensagens")
    parser.add_argument("--size", type=int, default=200, help="Tamanho de cada mensagem (bytes)")
    parser.add_argument("--producers", type=int, default=1, help="Número de produtores concorrentes")
    parser.add_argument("--consumers", type=int, default=1, help="Número de consumidores concorrentes")
    parser.add_argument("--rps", type=int, default=None, help="Rate Limiting (Requests Per Second)")
    parser.add_argument("--only", choices=["kafka", "rabbitmq", "baseline", "both"], default="both", 
                       help="Executar apenas para uma tecnologia")
    
    # Argumentos de Chaos Engineering
    parser.add_argument("--chaos", action="store_true", 
                       help="Executar experimento de tolerância a falhas (Chaos Engineering)")
    parser.add_argument("--chaos-delay", type=int, default=10, 
                       help="Delay em segundos antes de causar falha (padrão: 10)")
    
    # Argumentos de servidor
    parser.add_argument("--server", action="store_true", 
                       help="Executar servidor baseline HTTP")
    parser.add_argument("--port", type=int, default=5000, 
                       help="Porta do servidor baseline (padrão: 5000)")
    
    args = parser.parse_args()
    
    # Inicializar logger
    logger = Logger.get_logger("main")
    
    # Modo servidor
    if args.server:
        logger.info("🚀 Iniciando servidor baseline HTTP...")
        server = BaselineServer()
        try:
            server.run(port=args.port)
        except KeyboardInterrupt:
            logger.info("Servidor interrompido pelo usuário")
        return
    
    # Modo Chaos Engineering
    if args.chaos:
        logger.info(f"🔥 Iniciando experimento de tolerância a falhas (Chaos Engineering):")
        logger.info(f"   • Tecnologias: {args.only}")
        logger.info(f"   • Mensagens: {args.count}")
        logger.info(f"   • Tamanho: {args.size} bytes")
        logger.info(f"   • Rate Limiting: {args.rps or 'unlimited'} RPS")
        logger.info(f"   • Delay para falha: {args.chaos_delay}s")
        
        chaos_engineer = ChaosEngineer()
        
        if args.only == "both":
            # Executar experimento de chaos para Kafka e RabbitMQ
            for tech in ["kafka", "rabbitmq"]:
                logger.info(f"\n{'='*60}")
                chaos_engineer.run_chaos_experiment(
                    tech, args.count, args.size, args.rps, args.chaos_delay
                )
        else:
            if args.only in ["kafka", "rabbitmq"]:
                chaos_engineer.run_chaos_experiment(
                    args.only, args.count, args.size, args.rps, args.chaos_delay
                )
            else:
                logger.error(f"❌ Tecnologia {args.only} não suportada para experimento de chaos")
        return
    
    # Modo benchmark normal
    logger.info(f"🚀 Iniciando benchmark com configuração:")
    logger.info(f"   • Tecnologias: {args.only}")
    logger.info(f"   • Mensagens: {args.count}")
    logger.info(f"   • Tamanho: {args.size} bytes")
    logger.info(f"   • Produtores: {args.producers}")
    logger.info(f"   • Consumidores: {args.consumers}")
    if args.rps:
        logger.info(f"   • Rate Limiting: {args.rps} RPS")

    orchestrator = BenchmarkOrchestrator()
    
    if args.only == "both":
        orchestrator.run_all_benchmarks(
            count=args.count, size=args.size, 
            num_producers=args.producers, num_consumers=args.consumers, rps=args.rps
        )
    else:
        orchestrator.run_benchmark(
            args.only, count=args.count, size=args.size, 
            num_producers=args.producers, num_consumers=args.consumers, rps=args.rps
        )

    logger.info("\n📊 Resultados salvos em logs/<tech>/benchmark_results.csv")

if __name__ == "__main__":
    main()
