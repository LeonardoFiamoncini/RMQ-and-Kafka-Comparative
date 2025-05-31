from kafka import KafkaProducer
import sys
import time
import logging
from datetime import datetime
import os
import json

# Diretório base absoluto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(BASE_DIR, 'logs', 'kafka')
os.makedirs(LOG_DIR, exist_ok=True)

# Nome dos arquivos de log
DATE_STR = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
LATENCY_FILE = os.path.join(LOG_DIR, f'{DATE_STR}_latency.csv')
SUMMARY_FILE = os.path.join(LOG_DIR, f'{DATE_STR}_summary.csv')
PRODUCER_LOG = os.path.join(LOG_DIR, f'{DATE_STR}_producer-queue.txt')

# Configurar logger
logging.basicConfig(
    filename=PRODUCER_LOG,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def send_messages(count=1000, message_size=100):
    from collections import OrderedDict

    send_times = OrderedDict()
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    message_content = 'x' * (message_size - 10)  # espaço para o JSON overhead
    start_send = time.time()

    for i in range(count):
        msg_id = str(i)
        payload = {"id": msg_id, "body": message_content}
        send_times[msg_id] = time.time()
        producer.send('bcc-tcc', value=payload)
        logging.info(f"Mensagem {msg_id} enviada com {message_size} bytes")
        time.sleep(0.001)

    producer.flush()
    end_send = time.time()

    # Escreve sumário
    with open(SUMMARY_FILE, 'w', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['total_sent', count])
        writer.writerow(['send_duration_sec', end_send - start_send])

    # Salva tempos individuais para uso posterior
    json.dump(send_times, open(os.path.join(LOG_DIR, f'{DATE_STR}_send_times.json'), 'w'))

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    send_messages(count, size)
