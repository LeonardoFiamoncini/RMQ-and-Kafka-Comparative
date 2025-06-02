import subprocess
import time
import csv
import os
from datetime import datetime
import argparse
import psutil
from statistics import mean, median, quantiles, StatisticsError

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
}

def run_benchmark(tech, count=1000, size=200):
    print(f"\n▶️ Iniciando benchmark para {tech.upper()}...")
    tech_dir = os.path.join(LOG_DIR, tech)
    os.makedirs(tech_dir, exist_ok=True)

    process = psutil.Process(os.getpid())
    cpu_start = psutil.cpu_percent(interval=None)
    mem_start = process.memory_info().rss / (1024 * 1024)

    consumer_proc = subprocess.Popen(["python", TECHS[tech]["consumer"]])
    time.sleep(2)  # dá tempo para o consumidor se conectar

    start_time = time.time()
    subprocess.run(["python", TECHS[tech]["producer"], str(count), str(size)])
    time.sleep(5)  # tempo para consumidor processar (ajuste conforme necessário)
    end_time = time.time()

    consumer_proc.terminate()
    consumer_proc.wait()

    cpu_end = psutil.cpu_percent(interval=None)
    mem_end = process.memory_info().rss / (1024 * 1024)

    # Carrega dados de latência
    latency_file = None
    for f in sorted(os.listdir(tech_dir), reverse=True):
        if f.endswith("latency.csv"):
            latency_file = os.path.join(tech_dir, f)
            break

    latencies = []
    if latency_file:
        with open(latency_file, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    latencies.append(float(row["latency_seconds"]))
                except:
                    continue

    # Valores default para evitar crash
    latency_avg = latency_50 = latency_95 = latency_99 = 0

    try:
        if latencies:
            latency_avg = mean(latencies)
            latency_50 = median(latencies)
            latency_95 = quantiles(latencies, n=100)[94]
            latency_99 = quantiles(latencies, n=100)[98]
    except StatisticsError:
        print("⚠️ Nenhuma latência registrada para calcular estatísticas.")

    duration = end_time - start_time if end_time > start_time else 1
    throughput = count / duration

    # Grava CSV consolidado
    csv_path = os.path.join(tech_dir, "benchmark_results.csv")
    write_header = not os.path.exists(csv_path)

    with open(csv_path, mode="a", newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow([
                "timestamp", "messages", "message_size", "latency_avg",
                "latency_50", "latency_95", "latency_99", "throughput",
                "cpu_usage_percent", "memory_usage_mb"
            ])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            count, size, round(latency_avg, 6),
            round(latency_50, 6), round(latency_95, 6), round(latency_99, 6),
            round(throughput, 2), cpu_end, round(mem_end - mem_start, 2)
        ])

    print(f"✅ Benchmark {tech.upper()} finalizado:")
    print(f"   • Latência média: {latency_avg:.4f}s")
    print(f"   • Throughput: {throughput:.2f} msgs/s")
    print(f"   • CPU: {cpu_end:.1f}% | RAM usada: {mem_end - mem_start:.2f} MB")

def run_all_benchmarks(count, size):
    for tech in TECHS:
        run_benchmark(tech, count=count, size=size)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa benchmark comparativo RabbitMQ vs Kafka")
    parser.add_argument("--count", type=int, default=1000, help="Quantidade de mensagens")
    parser.add_argument("--size", type=int, default=200, help="Tamanho de cada mensagem (bytes)")
    parser.add_argument("--only", choices=["kafka", "rabbitmq", "both"], default="both", help="Executar benchmark apenas para uma fila")
    args = parser.parse_args()

    if args.only == "both":
        run_all_benchmarks(count=args.count, size=args.size)
    else:
        run_benchmark(args.only, count=args.count, size=args.size)

    print("\n📊 Resultados salvos em logs/<tech>/benchmark_results.csv")
