import pika
import sys
import time
import logging
from datetime import datetime

def setup_logger():
    data_str = datetime.now().strftime("%Y-%m-%d")
    log_file = f"{data_str}_producer-queue.txt"
    logging.basicConfig(
        filename=log_file,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO
    )

def send_messages(count=1000, message_size=100):
    credentials = pika.PlainCredentials('user', 'password')
    parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='bcc-tcc')
    message = 'x' * message_size

    for i in range(count):
        channel.basic_publish(exchange='', routing_key='bcc-tcc', body=message)
        logging.info(f"Mensagem {i+1} enviada com {message_size} bytes")
        time.sleep(0.001)

    connection.close()

if __name__ == "__main__":
    setup_logger()
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    send_messages(count, size)