from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import csv
from subprocess import Popen
import time

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR_RABBIT = os.path.join(BASE_DIR, "logs", "rabbitmq")
LOG_DIR_KAFKA = os.path.join(BASE_DIR, "logs", "kafka")

# Armazena processos de benchmark em andamento
benchmarks = {}

def read_benchmark_file(filepath):
    metrics = {
        "timestamps": [], "latency_avg": [], "latency_50": [], "latency_95": [],
        "latency_99": [], "throughput": [], "cpu": [], "memory": []
    }
    try:
        if not os.path.exists(filepath):
            return metrics
        with open(filepath, newline="") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                metrics["timestamps"].append(row["timestamp"])
                metrics["latency_avg"].append(float(row["latency_avg"]))
                metrics["latency_50"].append(float(row["latency_50"]))
                metrics["latency_95"].append(float(row["latency_95"]))
                metrics["latency_99"].append(float(row["latency_99"]))
                metrics["throughput"].append(float(row["throughput"]))
                metrics["cpu"].append(float(row["cpu_usage_percent"]))
                metrics["memory"].append(float(row["memory_usage_mb"]))
    except Exception as e:
        print(f"Erro ao ler {filepath}: {e}")
    return metrics

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/benchmark-rabbitmq")
def benchmark_rabbitmq():
    script_path = os.path.join(BASE_DIR, "benchmark_runner.py")
    count = request.args.get("count", default="1000")
    size = request.args.get("size", default="200")
    benchmark_id = f"rabbitmq_{int(time.time())}"
    benchmarks[benchmark_id] = Popen(["python", script_path, "--only", "rabbitmq", "--count", count, "--size", size])
    return jsonify({"message": "🏁 Benchmark exclusivo do RabbitMQ iniciado.", "id": benchmark_id})

@app.route("/benchmark-kafka")
def benchmark_kafka():
    script_path = os.path.join(BASE_DIR, "benchmark_runner.py")
    count = request.args.get("count", default="1000")
    size = request.args.get("size", default="200")
    benchmark_id = f"kafka_{int(time.time())}"
    benchmarks[benchmark_id] = Popen(["python", script_path, "--only", "kafka", "--count", count, "--size", size])
    return jsonify({"message": "🏁 Benchmark exclusivo do Apache Kafka iniciado.", "id": benchmark_id})

@app.route("/run-benchmark")
def run_benchmark():
    script_path = os.path.join(BASE_DIR, "benchmark_runner.py")
    count = request.args.get("count", default="1000")
    size = request.args.get("size", default="200")
    benchmark_id = f"both_{int(time.time())}"
    benchmarks[benchmark_id] = Popen(["python", script_path, "--count", count, "--size", size])
    return jsonify({"message": "🏁 Benchmark comparativo iniciado.", "id": benchmark_id})

@app.route("/benchmark-status/<benchmark_id>")
def benchmark_status(benchmark_id):
    if benchmark_id not in benchmarks:
        return jsonify({"status": "not_found", "message": "Benchmark não encontrado."})
    process = benchmarks[benchmark_id]
    if process.poll() is None:
        return jsonify({"status": "running", "message": "Benchmark em execução."})
    else:
        del benchmarks[benchmark_id]
        return jsonify({"status": "completed", "message": "Benchmark concluído."})

@app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory('media', filename)

@app.route("/dashboard")
def dashboard():
    rabbit_file = os.path.join(LOG_DIR_RABBIT, "benchmark_results.csv")
    kafka_file = os.path.join(LOG_DIR_KAFKA, "benchmark_results.csv")
    rabbit_metrics = read_benchmark_file(rabbit_file)
    kafka_metrics = read_benchmark_file(kafka_file)
    return render_template("dashboard.html", rabbit=rabbit_metrics, kafka=kafka_metrics)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)