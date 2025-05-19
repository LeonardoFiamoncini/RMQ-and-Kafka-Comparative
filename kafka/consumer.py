from kafka import KafkaConsumer
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
    log_file = os.path.join(log_dir, f"{date_str}_consumer-queue.txt")

    logging.basicConfig(
        filename=log_file,
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
        group_id='tcc-consumer-group'
    )

    print('[*] Aguardando mensagens. Pressione CTRL+C para sair')
    for message in consumer:
        logging.info(f"Mensagem recebida com {len(message.value)} bytes")

if __name__ == "__main__":
    setup_logger()
    start_consumer()