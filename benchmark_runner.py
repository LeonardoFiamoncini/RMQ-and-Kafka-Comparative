import subprocess
import time
import csv
import os
from datetime import datetime
import argparse
import psutil
from statistics import mean, median, quantiles
import multiprocessing
from multiprocessing import Pool, Queue, Process
import json
import glob

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

TECHS = {
    "rabbitmq": {
        "producer": os.path.join(BASE_DIR, "rabbitmq", "producer.py"),
        "consumer": os.path.join(BASE_DIR, "rabbitmq", "consumer.py"),
    },
    "kafka": {
        "producer": os.path.join(BASE_DIR, "kafka", "producer.py"),
        "consumer": os.path.join(BASE_DIR, "kafka", "consumer.py"),
    },
    "baseline": {
        "producer": os.path.join(BASE_DIR, "baseline", "producer.py"),
        "consumer": None,  # Baseline não tem consumidor separado
    },
}

def monitor_resources(process):
    cpu_total = 0
    mem_total = 0
    samples = 0
    while process.poll() is None:
        try:
            p = psutil.Process(process.pid)
            cpu_total += p.cpu_percent(interval=0.1)
            mem_total += p.memory_info().rss / (1024 * 1024)
            samples += 1
        except psutil.NoSuchProcess:
            break
    return cpu_total / samples if samples > 0 else 0, mem_total / samples if samples > 0 else 0

def run_producer_process(tech, producer_id, messages_per_producer, message_size, rps=None):
    """Executa um processo produtor individual"""
    try:
        cmd = ["python", TECHS[tech]["producer"], str(messages_per_producer), str(message_size)]
        if rps:
            cmd.append(str(rps))
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {
            "producer_id": producer_id,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "producer_id": producer_id,
            "success": False,
            "stdout": "",
            "stderr": "Timeout expired"
        }
    except Exception as e:
        return {
            "producer_id": producer_id,
            "success": False,
            "stdout": "",
            "stderr": str(e)
        }

def run_consumer_process(tech, consumer_id, expected_messages):
    """Executa um processo consumidor individual"""
    try:
        cmd = ["python", TECHS[tech]["consumer"], str(expected_messages)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {
            "consumer_id": consumer_id,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "consumer_id": consumer_id,
            "success": False,
            "stdout": "",
            "stderr": "Timeout expired"
        }
    except Exception as e:
        return {
            "consumer_id": consumer_id,
            "success": False,
            "stdout": "",
            "stderr": str(e)
        }

def run_benchmark(tech, count=1000, size=200, num_producers=1, num_consumers=1, rps=None):
    print(f"\n▶️ Iniciando benchmark para {tech.upper()}...")
    print(f"   • Produtores: {num_producers}")
    print(f"   • Consumidores: {num_consumers}")
    print(f"   • Mensagens totais: {count}")
    print(f"   • Tamanho da mensagem: {size} bytes")
    if rps:
        print(f"   • Rate Limiting: {rps} RPS")
    
    tech_dir = os.path.join(LOG_DIR, tech)
    os.makedirs(tech_dir, exist_ok=True)

    # Calcular mensagens por produtor
    messages_per_producer = count // num_producers
    remaining_messages = count % num_producers
    
    # Iniciar consumidores (exceto para baseline)
    if tech != "baseline":
        print(f"   • Iniciando {num_consumers} consumidor(es)...")
        consumer_processes = []
        with Pool(processes=num_consumers) as pool:
            consumer_args = [(tech, i, count) for i in range(num_consumers)]
            consumer_results = pool.starmap(run_consumer_process, consumer_args)
        
        # Aguardar um pouco para os consumidores se conectarem
        time.sleep(3)
    else:
        print(f"   • Baseline HTTP - sem consumidor separado")
        consumer_results = [{"success": True, "consumer_id": 0}]  # Mock para baseline
    
    # Iniciar produtores
    print(f"   • Iniciando {num_producers} produtor(es)...")
    start_time = time.time()
    
    with Pool(processes=num_producers) as pool:
        producer_args = []
        for i in range(num_producers):
            # Distribuir mensagens restantes entre os primeiros produtores
            messages_for_this_producer = messages_per_producer + (1 if i < remaining_messages else 0)
            producer_args.append((tech, i, messages_for_this_producer, size, rps))
        
        producer_results = pool.starmap(run_producer_process, producer_args)
    
    end_time = time.time()
    
    # Verificar resultados dos produtores
    successful_producers = sum(1 for result in producer_results if result["success"])
    print(f"   • Produtores bem-sucedidos: {successful_producers}/{num_producers}")
    
    # Verificar resultados dos consumidores
    successful_consumers = sum(1 for result in consumer_results if result["success"])
    print(f"   • Consumidores bem-sucedidos: {successful_consumers}/{num_consumers}")

    # Coletar métricas de latência de todos os arquivos de log
    latency_files = glob.glob(os.path.join(tech_dir, "*_latency.csv"))
    latencies = []
    
    for latency_file in latency_files:
        try:
            with open(latency_file, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    latencies.append(float(row["latency_seconds"]))
        except Exception as e:
            print(f"   • Erro ao ler arquivo de latência {latency_file}: {e}")

    # Coletar métricas de throughput dos summaries
    summary_files = glob.glob(os.path.join(tech_dir, "*_summary.csv"))
    total_throughput = 0
    total_messages_sent = 0
    
    for summary_file in summary_files:
        try:
            with open(summary_file, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["metric"] == "total_sent":
                        total_messages_sent += int(row["value"])
                    elif row["metric"] == "actual_rps" and rps:
                        total_throughput += float(row["value"])
        except Exception as e:
            print(f"   • Erro ao ler arquivo de summary {summary_file}: {e}")

    # Calcular métricas
    latency_avg = mean(latencies) if latencies else 0
    latency_50 = median(latencies) if latencies else 0
    latency_95 = quantiles(latencies, n=100)[94] if len(latencies) >= 100 else 0
    latency_99 = quantiles(latencies, n=100)[98] if len(latencies) >= 100 else 0
    
    duration = end_time - start_time
    if not rps:
        throughput = total_messages_sent / duration if duration > 0 else 0
    else:
        throughput = total_throughput

    # Salvar resultados
    csv_path = os.path.join(tech_dir, "benchmark_results.csv")
    write_header = not os.path.exists(csv_path)

    with open(csv_path, mode="a", newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow([
                "timestamp", "messages", "message_size", "num_producers", "num_consumers",
                "rps", "latency_avg", "latency_50", "latency_95", "latency_99", 
                "throughput", "successful_producers", "successful_consumers"
            ])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            count, size, num_producers, num_consumers,
            rps or "unlimited", round(latency_avg, 6),
            round(latency_50, 6), round(latency_95, 6), round(latency_99, 6),
            round(throughput, 2), successful_producers, successful_consumers
        ])

    print(f"✅ Benchmark {tech.upper()} finalizado:")
    print(f"   • Latência média: {latency_avg:.4f}s")
    print(f"   • Throughput: {throughput:.2f} msgs/s")
    print(f"   • Mensagens processadas: {len(latencies)}")
    print(f"   • Duração total: {duration:.2f}s")

def run_all_benchmarks(count, size, num_producers=1, num_consumers=1, rps=None):
    # Executar para RabbitMQ, Kafka e Baseline
    for tech in ["rabbitmq", "kafka", "baseline"]:
        run_benchmark(tech, count=count, size=size, num_producers=num_producers, 
                     num_consumers=num_consumers, rps=rps)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa benchmark comparativo RabbitMQ vs Kafka")
    parser.add_argument("--count", type=int, default=1000, help="Quantidade de mensagens")
    parser.add_argument("--size", type=int, default=200, help="Tamanho de cada mensagem (bytes)")
    parser.add_argument("--producers", type=int, default=1, help="Número de produtores concorrentes")
    parser.add_argument("--consumers", type=int, default=1, help="Número de consumidores concorrentes")
    parser.add_argument("--rps", type=int, default=None, help="Rate Limiting (Requests Per Second)")
    parser.add_argument("--only", choices=["kafka", "rabbitmq", "baseline", "both"], default="both", help="Executar apenas para uma tecnologia")
    args = parser.parse_args()

    print(f"🚀 Iniciando benchmark com configuração:")
    print(f"   • Tecnologias: {args.only}")
    print(f"   • Mensagens: {args.count}")
    print(f"   • Tamanho: {args.size} bytes")
    print(f"   • Produtores: {args.producers}")
    print(f"   • Consumidores: {args.consumers}")
    if args.rps:
        print(f"   • Rate Limiting: {args.rps} RPS")

    if args.only == "both":
        run_all_benchmarks(count=args.count, size=args.size, 
                          num_producers=args.producers, num_consumers=args.consumers, rps=args.rps)
    else:
        run_benchmark(args.only, count=args.count, size=args.size, 
                     num_producers=args.producers, num_consumers=args.consumers, rps=args.rps)

    print("\n📊 Resultados salvos em logs/<tech>/benchmark_results.csv")