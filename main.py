"""
Ponto de entrada principal do sistema de benchmark TCC
Objetivo: Comparar Baseline HTTP, RabbitMQ e Kafka em 3 portes
"""
import argparse
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.logger import Logger
from src.orchestration.benchmark import BenchmarkOrchestrator
from src.brokers.baseline.server import BaselineServer

def main():
    """Função principal - Benchmark TCC"""
    parser = argparse.ArgumentParser(
        description='TCC - Análise Comparativa: Apache Kafka vs RabbitMQ',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
PORTES DE APLICAÇÃO (RPS):
  pequeno:  100 requisições (aplicações corporativas internas, MVPs)
  medio:    1.000 requisições (e-commerce estabelecido)
  grande:   10.000 requisições (serviços globais)

MÉTRICAS COLETADAS:
  • Latência: P50, P95, P99 (em segundos)
  • Throughput: Mensagens por segundo
        """
    )
    
    # Argumentos simplificados para o TCC
    parser.add_argument(
        "--porte", 
        choices=["pequeno", "medio", "grande"],
        required=False,
        help="Porte da aplicação (pequeno=100, medio=1000, grande=10000 mensagens)"
    )
    parser.add_argument(
        "--system", 
        choices=["kafka", "rabbitmq", "baseline"], 
        required=False,
        help="Sistema a ser testado: rabbitmq, kafka ou baseline"
    )
    parser.add_argument(
        "--size", 
        type=int, 
        default=200, 
        help="Tamanho de cada mensagem em bytes (padrão: 200)"
    )
    
    # Modo servidor para baseline
    parser.add_argument("--server", action="store_true", 
                       help="Executar servidor baseline HTTP")
    parser.add_argument("--port", type=int, default=5000, 
                       help="Porta do servidor baseline (padrão: 5000)")
    
    args = parser.parse_args()
    
    # Inicializar logger
    logger = Logger.get_logger("main")
    
    # Modo servidor baseline
    if args.server:
        logger.info("🚀 Iniciando servidor baseline HTTP na porta {}...".format(args.port))
        server = BaselineServer()
        try:
            server.run(port=args.port)
        except KeyboardInterrupt:
            logger.info("Servidor interrompido pelo usuário")
        return
    
    # Validar argumentos obrigatórios para benchmark
    if not args.porte or not args.system:
        parser.error("Os parâmetros --porte e --system são obrigatórios para executar o benchmark.")
    
    # Mapear porte para número de mensagens
    PORTE_MESSAGES = {
        "pequeno": 100,
        "medio": 1000,
        "grande": 10000
    }
    
    message_count = PORTE_MESSAGES[args.porte]
    
    # Log da configuração do benchmark
    logger.info(f"\n🎯 BENCHMARK TCC - ANÁLISE COMPARATIVA")
    logger.info(f"{'='*60}")
    logger.info(f"   • Sistema: {args.system.upper()}")
    logger.info(f"   • Porte: {args.porte.upper()} ({message_count:,} mensagens)")
    logger.info(f"   • Tamanho da mensagem: {args.size} bytes")
    logger.info(f"\n📊 Métricas a serem coletadas:")
    logger.info(f"   • Latência: P50, P95, P99")
    logger.info(f"   • Throughput: Mensagens/segundo")
    logger.info(f"{'='*60}\n")

    # Executar benchmark
    orchestrator = BenchmarkOrchestrator()
    
    try:
        results = orchestrator.run_benchmark(
            tech=args.system, 
            count=message_count,
            size=args.size,
            porte=args.porte  # Passar o porte para facilitar identificação
        )
    except Exception as exc:
        logger.error(f"❌ Falha na execução do benchmark: {exc}")
        sys.exit(1)
    
    # Exibir resultados
    if results:
        logger.info(f"\n{'='*60}")
        logger.info(f"📊 RESULTADOS - {args.system.upper()} - PORTE {args.porte.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"   • Throughput: {results.get('throughput', 0):.2f} msg/s")
        logger.info(f"   • Latência P50: {results.get('latency_50', 0):.6f} segundos")
        logger.info(f"   • Latência P95: {results.get('latency_95', 0):.6f} segundos")
        logger.info(f"   • Latência P99: {results.get('latency_99', 0):.6f} segundos")
        logger.info(f"   • Mensagens processadas: {results.get('messages_processed', 0):,}")
        logger.info(f"   • Duração total: {results.get('duration', 0):.2f} segundos")
        logger.info(f"{'='*60}\n")
        
        run_id = results.get("run_id")
        if run_id:
            logger.info(f"📁 Logs salvos em: logs/{args.system}/{run_id}/")

if __name__ == "__main__":
    main()
