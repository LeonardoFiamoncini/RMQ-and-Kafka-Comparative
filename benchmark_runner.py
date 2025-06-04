import subprocess
import time
import csv
import os
from datetime import datetime
import argparse
import psutil
from statistics import mean, median, quantiles

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

def run_benchmark(tech, count=1000, size=200):
    print(f"\n▶️ Iniciando benchmark para {tech.upper()}...")
    tech_dir = os.path.join(LOG_DIR, tech)
    os.makedirs(tech_dir, exist_ok=True)

    consumer_proc = subprocess.Popen(["python", TECHS[tech]["consumer"], str(count)])
    time.sleep(2)

    start_time = time.time()
    producer_proc = subprocess.Popen(["python", TECHS[tech]["producer"], str(count), str(size)])
    cpu_usage, mem_usage = monitor_resources(producer_proc)
    producer_proc.wait()
    end_time = time.time()

    consumer_proc.terminate()
    consumer_proc.wait()

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
                latencies.append(float(row["latency_seconds"]))

    latency_avg = mean(latencies) if latencies else 0
    latency_50 = median(latencies) if latencies else 0
    latency_95 = quantiles(latencies, n=100)[94] if latencies else 0
    latency_99 = quantiles(latencies, n=100)[98] if latencies else 0
    duration = end_time - start_time
    throughput = count / duration if duration > 0 else 0

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
            round(throughput, 2), round(cpu_usage, 2), round(mem_usage, 2)
        ])

    print(f"✅ Benchmark {tech.upper()} finalizado:")
    print(f"   • Latência média: {latency_avg:.4f}s")
    print(f"   • Throughput: {throughput:.2f} msgs/s")
    print(f"   • CPU: {cpu_usage:.1f}% | RAM: {mem_usage:.2f} MB")

def run_all_benchmarks(count, size):
    for tech in TECHS:
        run_benchmark(tech, count=count, size=size)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa benchmark comparativo RabbitMQ vs Kafka")
    parser.add_argument("--count", type=int, default=1000, help="Quantidade de mensagens")
    parser.add_argument("--size", type=int, default=200, help="Tamanho de cada mensagem (bytes)")
    parser.add_argument("--only", choices=["kafka", "rabbitmq", "both"], default="both", help="Executar apenas para uma fila")
    args = parser.parse_args()

    if args.only == "both":
        run_all_benchmarks(count=args.count, size=args.size)
    else:
        run_benchmark(args.only, count=args.count, size=args.size)

    print("\n📊 Resultados salvos em logs/<tech>/benchmark_results.csv")