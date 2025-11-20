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
    parser = argparse.ArgumentParser(
        description='Sistema de Benchmark RabbitMQ vs Kafka',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Parâmetros de entrada válidos:
  --count: 5, 10, 15, 100, 1000, 10000, 100000
  --producers: 1, 4, 16, 64
  --consumers: 4, 64
  --system: rabbitmq, kafka, baseline

Métricas de saída:
  T (Tempo de permanência na fila): Latência em segundos
  V (Throughput): Mensagens por segundo
        """
    )
    
    # Valores válidos conforme especificação do orientador
    VALID_MESSAGE_COUNTS = [5, 10, 15, 100, 1000, 10000, 100000]
    VALID_PRODUCERS = [1, 4, 16, 64]
    VALID_CONSUMERS = [4, 64]
    
    # Argumentos principais
    parser.add_argument(
        "--count", 
        type=int, 
        default=None,
        choices=VALID_MESSAGE_COUNTS,
        help=f"Quantidade de mensagens. Valores válidos: {', '.join(map(str, VALID_MESSAGE_COUNTS))}"
    )
    parser.add_argument(
        "--size", 
        type=int, 
        default=200, 
        help="Tamanho de cada mensagem (bytes)"
    )
    parser.add_argument(
        "--producers", 
        type=int, 
        default=None,
        choices=VALID_PRODUCERS,
        help=f"Número de produtores simultâneos. Valores válidos: {', '.join(map(str, VALID_PRODUCERS))}"
    )
    parser.add_argument(
        "--consumers", 
        type=int, 
        default=None,
        choices=VALID_CONSUMERS,
        help=f"Número de consumidores. Valores válidos: {', '.join(map(str, VALID_CONSUMERS))}"
    )
    parser.add_argument(
        "--system", 
        choices=["kafka", "rabbitmq", "baseline"], 
        default=None,
        help="Sistema a ser testado: rabbitmq, kafka ou baseline"
    )
    parser.add_argument(
        "--rps", 
        type=int, 
        default=None, 
        help="Rate Limiting (Requests Per Second) - Opcional"
    )
    
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
    
    # Modo Chaos Engineering (não precisa validar todos os parâmetros)
    if args.chaos:
        # Para chaos, apenas count, size e system são necessários
        if args.count is None or args.system is None:
            parser.error(
                "Os parâmetros --count e --system são obrigatórios em modo de chaos."
            )
        # Usar valores padrão se não fornecidos
        if args.producers is None:
            args.producers = 1
        if args.consumers is None:
            args.consumers = 4
        logger.info(f"🔥 Iniciando experimento de tolerância a falhas (Chaos Engineering):")
        logger.info(f"   • Sistema: {args.system}")
        logger.info(f"   • Mensagens: {args.count}")
        logger.info(f"   • Tamanho: {args.size} bytes")
        logger.info(f"   • Produtores: {args.producers}")
        logger.info(f"   • Consumidores: {args.consumers}")
        logger.info(f"   • Rate Limiting: {args.rps or 'unlimited'} RPS")
        logger.info(f"   • Delay para falha: {args.chaos_delay}s")
        
        chaos_engineer = ChaosEngineer()
        
        if args.system in ["kafka", "rabbitmq"]:
            chaos_engineer.run_chaos_experiment(
                args.system, args.count, args.size, args.rps, args.chaos_delay
            )
        else:
            logger.error(f"❌ Tecnologia {args.system} não suportada para experimento de chaos")
        return
    
    # Validar obrigatoriedade dos parâmetros de benchmark (após verificar chaos)
    required_values = {
        "--count": args.count,
        "--producers": args.producers,
        "--consumers": args.consumers,
        "--system": args.system,
    }
    missing_args = [flag for flag, value in required_values.items() if value is None]
    if missing_args:
        parser.error(
            f"Os parâmetros {', '.join(missing_args)} são obrigatórios em modo de benchmark."
        )
    
    # Modo benchmark normal
    logger.info(f"🚀 Iniciando benchmark com configuração:")
    logger.info(f"   • Sistema: {args.system}")
    logger.info(f"   • Mensagens: {args.count:,}")
    logger.info(f"   • Tamanho: {args.size} bytes")
    logger.info(f"   • Produtores simultâneos: {args.producers}")
    logger.info(f"   • Consumidores: {args.consumers}")
    if args.rps:
        logger.info(f"   • Rate Limiting: {args.rps} RPS")
    logger.info(f"\n📊 Métricas que serão coletadas:")
    logger.info(f"   • T (Tempo de permanência na fila): Latência em segundos")
    logger.info(f"   • V (Throughput): Mensagens por segundo")

    orchestrator = BenchmarkOrchestrator()
    
    # Executar benchmark para o sistema especificado
    try:
        results = orchestrator.run_benchmark(
            args.system, 
            count=args.count, 
            size=args.size, 
            num_producers=args.producers, 
            num_consumers=args.consumers, 
            rps=args.rps
        )
    except Exception as exc:
        logger.error(f"❌ Falha na execução do benchmark: {exc}")
        sys.exit(1)
    
    # Exibir métricas principais
    logger.info(f"\n{'='*60}")
    logger.info(f"📊 RESULTADOS DO BENCHMARK - {args.system.upper()}")
    logger.info(f"{'='*60}")
    if results:
        avg_latency = results.get("avg_latency", 0)
        throughput = results.get("throughput", 0)
        messages_processed = results.get("messages_sent", 0)
        duration = results.get("duration", 0)
        
        logger.info(f"   • T (Latência média): {avg_latency:.6f} segundos")
        logger.info(f"   • V (Throughput): {throughput:.2f} mensagens/segundo")
        logger.info(f"   • Mensagens processadas: {messages_processed:,}")
        logger.info(f"   • Duração total: {duration:.2f} segundos")
    
    run_id = results.get("run_id") if results else None
    run_path = f"logs/{args.system}/{run_id}/" if run_id else f"logs/{args.system}/"
    logger.info(f"\n📁 Resultados detalhados salvos em: {run_path}")
    logger.info("   • *_latency.csv - Latências individuais (T)")
    logger.info("   • *_summary.csv - Resumo com throughput (V)")
    logger.info(f"   • benchmark_results.csv - Resultados consolidados em logs/{args.system}/")

if __name__ == "__main__":
    main()
