import pika
import sys
import time
import logging
from datetime import datetime
import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(BASE_DIR, 'logs', 'rabbitmq')
os.makedirs(LOG_DIR, exist_ok=True)

DATE_STR = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
LATENCY_FILE = os.path.join(LOG_DIR, f'{DATE_STR}_latency.csv')
SUMMARY_FILE = os.path.join(LOG_DIR, f'{DATE_STR}_summary.csv')
PRODUCER_LOG = os.path.join(LOG_DIR, f'{DATE_STR}_producer-queue.txt')
SEND_TIMES_FILE = os.path.join(LOG_DIR, f'{DATE_STR}_send_times.json')

logging.basicConfig(
    filename=PRODUCER_LOG,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def send_messages(count=1000, message_size=100, rps=None):
    from collections import OrderedDict

    send_times = OrderedDict()
    credentials = pika.PlainCredentials('user', 'password')
    parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='bcc-tcc', durable=True, arguments={'x-queue-type': 'quorum'})
    channel.confirm_delivery()

    message_content = 'x' * (message_size - 10)
    start_send = time.time()
    
    # Calcular intervalo de sleep para Rate Limiting
    sleep_interval = 0
    if rps and rps > 0:
        sleep_interval = 1.0 / rps
        logging.info(f"Rate Limiting ativado: {rps} RPS (intervalo: {sleep_interval:.6f}s)")

    for i in range(count):
        msg_id = str(i)
        payload = {"id": msg_id, "body": message_content}
        body = json.dumps(payload)
        send_times[msg_id] = time.time()
        try:
            channel.basic_publish(exchange='', routing_key='bcc-tcc', body=body, mandatory=True)
            logging.info(f"Mensagem {msg_id} enviada com {message_size} bytes")
        except pika.exceptions.UnroutableError:
            logging.error(f"Falha ao enviar mensagem {msg_id}")
        
        # Rate Limiting: aguardar o intervalo calculado
        if sleep_interval > 0:
            time.sleep(sleep_interval)

    connection.close()
    end_send = time.time()

    with open(SEND_TIMES_FILE, 'w') as f:
        json.dump(send_times, f)

    with open(SUMMARY_FILE, 'w', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['total_sent', count])
        writer.writerow(['send_duration_sec', end_send - start_send])
        if rps:
            writer.writerow(['target_rps', rps])
            actual_rps = count / (end_send - start_send)
            writer.writerow(['actual_rps', actual_rps])

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    rps = int(sys.argv[3]) if len(sys.argv) > 3 else None
    send_messages(count, size, rps)