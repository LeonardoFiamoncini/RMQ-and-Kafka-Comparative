from kafka import KafkaProducer
import sys
import time
import logging
from datetime import datetime
import os

# Definir o diretório base absoluto
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def setup_logger():
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join(BASE_DIR, "logs", "kafka")
    try:
        os.makedirs(log_dir, exist_ok=True)
    except Exception as e:
        print(f"Erro ao criar diretório de log: {e}")
        sys.exit(1)
    log_file = os.path.join(log_dir, f"{date_str}_producer-queue.txt")

    logging.basicConfig(
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

def send_messages(count=1000, message_size=100):
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    message = b'x' * message_size

    for i in range(count):
        producer.send('bcc-tcc', message)
        logging.info(f"Mensagem {i+1} enviada com {message_size} bytes")
        time.sleep(0.001)

    producer.flush()

if __name__ == "__main__":
    setup_logger()
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    send_messages(count, size)