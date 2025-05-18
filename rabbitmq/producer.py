import pika
import sys
import time

def send_messages(count=1000, message_size=100):
    credentials = pika.PlainCredentials('user', 'password')  # <-- credenciais corretas
    parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='bcc-tcc')

    message = 'x' * message_size

    for i in range(count):
        channel.basic_publish(exchange='',
                              routing_key='bcc-tcc',
                              body=message)
        print(f"[{i+1}] Mensagem enviada")
        time.sleep(0.001)

    connection.close()

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    send_messages(count, size)
