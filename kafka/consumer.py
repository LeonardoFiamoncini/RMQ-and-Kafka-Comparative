from kafka import KafkaConsumer
import logging
from datetime import datetime
import os
import json
import time
import csv

# Definir o diretório base absoluto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(BASE_DIR, "logs", "kafka")
os.makedirs(LOG_DIR, exist_ok=True)

# Nome dos arquivos de log
DATE_STR = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
CONSUMER_LOG = os.path.join(LOG_DIR, f"{DATE_STR}_consumer-queue.txt")
LATENCY_FILE = os.path.join(LOG_DIR, f"{DATE_STR}_latency.csv")
SUMMARY_FILE = os.path.join(LOG_DIR, f"{DATE_STR}_summary.csv")
SEND_TIMES_FILE = os.path.join(LOG_DIR, f"{DATE_STR}_send_times.json")

# Setup do logger
logging.basicConfig(
    filename=CONSUMER_LOG,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def start_consumer():
    consumer = KafkaConsumer(
        'bcc-tcc',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='tcc-consumer-group',
        value_deserializer=lambda v: json.loads(v.decode('utf-8'))
    )

    print('[*] Aguardando mensagens. Pressione CTRL+C para sair')

    # Carrega tempos de envio para cálculo de latência
    try:
        with open(SEND_TIMES_FILE, 'r') as f:
            send_times = json.load(f)
    except FileNotFoundError:
        logging.error("Arquivo de tempos de envio não encontrado.")
        return

    latencies = []
    total_received = 0
    start_consume = time.time()

    for message in consumer:
        recv_time = time.time()
        msg_id = message.value.get("id")

        if msg_id in send_times:
            latency = recv_time - float(send_times[msg_id])
            latencies.append((msg_id, latency))
            logging.info(f"Mensagem {msg_id} recebida com latência de {latency:.6f} segundos")
        else:
            logging.warning(f"Mensagem {msg_id} recebida sem timestamp de envio correspondente")

        total_received += 1

        if total_received >= len(send_times):
            break

    end_consume = time.time()

    # Salva latências
    with open(LATENCY_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['msg_id', 'latency_seconds'])
        writer.writerows(latencies)

    # Salva resumo
    with open(SUMMARY_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['total_received', total_received])
        writer.writerow(['consume_duration_sec', end_consume - start_consume])
        avg_latency = sum(lat for _, lat in latencies) / len(latencies) if latencies else 0
        writer.writerow(['avg_latency_sec', avg_latency])
        writer.writerow(['throughput_msgs_per_sec', total_received / (end_consume - start_consume)])

if __name__ == "__main__":
    start_consumer()
