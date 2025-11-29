"""
Ponto de entrada principal do sistema de benchmark TCC
Objetivo: Comparar Baseline HTTP, RabbitMQ e Kafka em 5 sizes
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
SIZES DE CARGA:
  size1:  100 mensagens
  size2:  1.000 mensagens
  size3:  10.000 mensagens
  size4:  100.000 mensagens
  size5:  1.000.000 mensagens

TAMANHOS DE MENSAGEM:
  --message-size 100   : 0.1 KB
  --message-size 1000  : 1 KB

MÉTRICAS COLETADAS:
  • Latência: P95, P99 (em segundos)
  • Throughput: Mensagens por segundo
        """
    )
    
    # Argumentos simplificados para o TCC
    parser.add_argument(
        "--size", 
        choices=["size1", "size2", "size3", "size4", "size5"],
        required=False,
        help="Size da carga (size1=100, size2=1000, size3=10000, size4=100000, size5=1000000 mensagens)"
    )
    parser.add_argument(
        "--system", 
        choices=["kafka", "rabbitmq", "baseline"], 
        required=False,
        help="Sistema a ser testado: rabbitmq, kafka ou baseline"
    )
    parser.add_argument(
        "--message-size", 
        type=int, 
        default=100,
        help="Tamanho de cada mensagem em bytes (padrão: 100 = 0.1KB). Valores recomendados: 100, 1000, 10000"
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
        logger.info("Iniciando servidor baseline HTTP na porta {}...".format(args.port))
        server = BaselineServer()
        try:
            server.run(port=args.port)
        except KeyboardInterrupt:
            logger.info("Servidor interrompido pelo usuário")
        return
    
    # Validar argumentos obrigatórios para benchmark
    if not args.size or not args.system:
        parser.error("Os parâmetros --size e --system são obrigatórios para executar o benchmark.")
    
    # Mapear size para número de mensagens
    SIZE_MESSAGES = {
        "size1": 100,
        "size2": 1000,
        "size3": 10000,
        "size4": 100000,
        "size5": 1000000
    }
    
    message_count = SIZE_MESSAGES[args.size]
    
    # Log da configuração do benchmark
    logger.info(f"\nBENCHMARK TCC - ANÁLISE COMPARATIVA")
    logger.info(f"{'='*60}")
    logger.info(f"   • Sistema: {args.system.upper()}")
    logger.info(f"   • Size: {args.size.upper()} ({message_count:,} mensagens)")
    logger.info(f"   • Tamanho da mensagem: {args.message_size} bytes")
    logger.info(f"\nMétricas a serem coletadas:")
    logger.info(f"   • Latência: P95, P99")
    logger.info(f"   • Throughput: Mensagens/segundo")
    logger.info(f"{'='*60}\n")

    # Executar benchmark
    orchestrator = BenchmarkOrchestrator()
    
    try:
        results = orchestrator.run_benchmark(
            tech=args.system, 
            count=message_count,
            size=args.message_size,
            size_name=args.size  # Passar o size para facilitar identificação
        )
    except Exception as exc:
        logger.error(f"Falha na execução do benchmark: {exc}")
        sys.exit(1)
    
    # Exibir resultados
    if results:
        logger.info(f"\n{'='*60}")
        logger.info(f"RESULTADOS - {args.system.upper()} - SIZE {args.size.upper()}")
        logger.info(f"{'='*60}")
        logger.info(f"   • Throughput: {results.get('throughput', 0):.2f} msg/s")
        logger.info(f"   • Latência P95: {results.get('latency_95', 0):.6f} segundos")
        logger.info(f"   • Latência P99: {results.get('latency_99', 0):.6f} segundos")
        logger.info(f"   • Mensagens processadas: {results.get('messages_processed', 0):,}")
        logger.info(f"   • Duração total: {results.get('duration', 0):.2f} segundos")
        logger.info(f"{'='*60}\n")
        
        run_id = results.get("run_id")
        if run_id:
            logger.info(f"Logs salvos em: logs/{args.system}/{run_id}/")

if __name__ == "__main__":
    main()
