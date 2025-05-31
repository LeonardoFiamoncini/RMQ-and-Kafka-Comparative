from flask import Flask, render_template, send_from_directory
import os
from subprocess import Popen
import subprocess

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/send-rabbitmq")
def send_rabbitmq():
    rabbitmq_producer = os.path.join(BASE_DIR, "rabbitmq", "producer.py")
    Popen(["python", rabbitmq_producer, "1000", "200"])
    return "RabbitMQ: Envio de mensagens iniciado em background"

@app.route("/send-kafka")
def send_kafka():
    kafka_producer = os.path.join(BASE_DIR, "kafka", "producer.py")
    Popen(["python", kafka_producer, "1000", "200"])
    return "Kafka: Envio de mensagens iniciado em background"

@app.route("/benchmark/<tech>/<int:count>/<int:size>")
def run_benchmark(tech, count, size):
    benchmark_script = os.path.join(BASE_DIR, "benchmark_runner.py")
    try:
        subprocess.run(["python", benchmark_script, tech, str(count), str(size)], check=True)
        return f"Benchmark com {tech} executado com sucesso!"
    except subprocess.CalledProcessError:
        return f"Erro ao executar benchmark com {tech}"

@app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory('media', filename)

if __name__ == "__main__":
    app.run(debug=True)