import pika

def callback(ch, method, properties, body):
    print(f"[x] Mensagem recebida: {len(body)} bytes")

def start_consumer():
    credentials = pika.PlainCredentials('user', 'password')
    parameters = pika.ConnectionParameters('localhost', 5672, '/', credentials)

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()

    channel.queue_declare(queue='teste')
    channel.basic_consume(queue='teste', on_message_callback=callback, auto_ack=True)

    print('[*] Aguardando mensagens. Pressione CTRL+C para sair')
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()
