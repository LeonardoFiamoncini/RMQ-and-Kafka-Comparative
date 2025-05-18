import pika
import logging
from datetime import datetime
import os

def setup_logger():
    date_str = datetime.now().strftime("%Y-%m-%d")
    log_dir = os.path.join("..", "logs", "rabbitmq")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{date_str}_consumer-queue.txt")

    logging.basicConfig(
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

def callback(ch, method, properties, body):
    logging.info(f"Mensagem recebida com {len(body)} bytes")

def start_consumer():
    credentials = pika.PlainCredentials('user', 'password')
    parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue='bcc-tcc')

    channel.basic_consume(queue='bcc-tcc', on_message_callback=callback, auto_ack=True)
    print('[*] Aguardando mensagens. Pressione CTRL+C para sair')
    channel.start_consuming()

if __name__ == "__main__":
    setup_logger()
    start_consumer()