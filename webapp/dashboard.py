from flask import Flask, render_template
import os
import csv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'webapp', 'templates'),
            static_folder=os.path.join(BASE_DIR, 'webapp', 'static'))

LOG_DIR_RABBIT = os.path.join(BASE_DIR, "logs", "rabbitmq")
LOG_DIR_KAFKA = os.path.join(BASE_DIR, "logs", "kafka")

def read_benchmark_file(filepath):
    metrics = {
        "timestamps": [],
        "latency_avg": [],
        "latency_50": [],
        "latency_95": [],
        "latency_99": [],
        "throughput": [],
        "cpu": [],
        "memory": []
    }

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

    return metrics

@app.route("/dashboard")
def dashboard():
    rabbit_file = os.path.join(LOG_DIR_RABBIT, "benchmark_results.csv")
    kafka_file = os.path.join(LOG_DIR_KAFKA, "benchmark_results.csv")

    rabbit_metrics = read_benchmark_file(rabbit_file)
    kafka_metrics = read_benchmark_file(kafka_file)

    return render_template("dashboard.html",
                           rabbit=rabbit_metrics,
                           kafka=kafka_metrics)

if __name__ == "__main__":
    app.run(port=5001, debug=True)
