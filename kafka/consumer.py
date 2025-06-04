from kafka import KafkaConsumer
import logging
from datetime import datetime
import os
import json
import time
import csv
import signal
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(BASE_DIR, "logs", "kafka")
os.makedirs(LOG_DIR, exist_ok=True)

DATE_STR = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
CONSUMER_LOG = os.path.join(LOG_DIR, f"{DATE_STR}_consumer-queue.txt")
LATENCY_FILE = os.path.join(LOG_DIR, f"{DATE_STR}_latency.csv")
SUMMARY_FILE = os.path.join(LOG_DIR, f"{DATE_STR}_summary.csv")
SEND_TIMES_FILE = os.path.join(LOG_DIR, f"{DATE_STR}_send_times.json")

logging.basicConfig(
    filename=CONSUMER_LOG,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

latencies = []
total_received = 0
start_consume = None
end_consume = None

try:
    with open(SEND_TIMES_FILE, 'r') as f:
        send_times = json.load(f)
except FileNotFoundError:
    logging.error("Arquivo de tempos de envio não encontrado.")
    send_times = {}

def save_results():
    global latencies, total_received, start_consume, end_consume
    with open(LATENCY_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['msg_id', 'latency_seconds'])
        writer.writerows(latencies)

    duration = end_consume - start_consume if end_consume and start_consume else 0
    throughput = total_received / duration if duration > 0 else 0
    avg_latency = sum(lat for _, lat in latencies) / len(latencies) if latencies else 0

    with open(SUMMARY_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['total_received', total_received])
        writer.writerow(['consume_duration_sec', duration])
        writer.writerow(['avg_latency_sec', avg_latency])
        writer.writerow(['throughput_msgs_per_sec', throughput])

def signal_handler(sig, frame):
    print('\n[!] Interrompido pelo usuário. Salvando resultados...')
    save_results()
    sys.exit(0)

def start_consumer(expected_count=1000):
    global start_consume, end_consume, latencies, total_received
    signal.signal(signal.SIGINT, signal_handler)
    consumer = KafkaConsumer(
        'bcc-tcc',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='tcc-consumer-group',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    print(f'[*] Aguardando até {expected_count} mensagens. Pressione CTRL+C para sair')
    timeout = time.time() + 60  # Timeout de 60 segundos

    for message in consumer:
        recv_time = time.time()
        if start_consume is None:
            start_consume = recv_time

        msg_id = message.value.get("id")
        if msg_id in send_times:
            latency = recv_time - float(send_times[msg_id])
            latencies.append((msg_id, latency))
            logging.info(f"Mensagem {msg_id} recebida com latência de {latency:.6f} segundos")
        else:
            logging.warning(f"Mensagem {msg_id} recebida sem timestamp de envio")

        total_received += 1
        end_consume = recv_time

        if total_received >= expected_count or time.time() > timeout:
            break

    consumer.close()
    save_results()

if __name__ == "__main__":
    expected_count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    start_consumer(expected_count)