from flask import Flask, render_template, send_from_directory, request
import os
from subprocess import Popen

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send-rabbitmq")
def send_rabbitmq():
    rabbitmq_producer = os.path.join(BASE_DIR, "rabbitmq", "producer.py")
    count = request.args.get("count", default="1000")
    size = request.args.get("size", default="200")
    Popen(["python", rabbitmq_producer, count, size])
    return f"RabbitMQ: Envio de {count} mensagens com {size} bytes iniciado."

@app.route("/send-kafka")
def send_kafka():
    kafka_producer = os.path.join(BASE_DIR, "kafka", "producer.py")
    count = request.args.get("count", default="1000")
    size = request.args.get("size", default="200")
    Popen(["python", kafka_producer, count, size])
    return f"Kafka: Envio de {count} mensagens com {size} bytes iniciado."

@app.route("/run-benchmark")
def run_benchmark():
    benchmark_script = os.path.join(BASE_DIR, "benchmark_runner.py")
    Popen(["python", benchmark_script, "--count", "1000", "--size", "200"])
    return "🏁 Benchmark comparativo iniciado em background"

@app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory('media', filename)

if __name__ == "__main__":
    app.run(debug=True)
