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
    
    # Habilitar confirmação de entrega
    channel.confirm_delivery()
    logging.info("Confirmação de entrega habilitada")

    message_content = 'x' * (message_size - 10)
    start_send = time.time()
    successful_deliveries = 0
    failed_deliveries = 0
    
    # Calcular intervalo de sleep para Rate Limiting
    sleep_interval = 0
    if rps and rps > 0:
        sleep_interval = 1.0 / rps
        logging.info(f"Rate Limiting ativado: {rps} RPS (intervalo: {sleep_interval:.6f}s)")

    for i in range(count):
        msg_id = str(i)
        payload = {"id": msg_id, "body": message_content}
        body = json.dumps(payload)
        
        try:
            # Publicar mensagem com confirmação de entrega
            channel.basic_publish(
                exchange='', 
                routing_key='bcc-tcc', 
                body=body, 
                mandatory=True,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Tornar mensagem persistente
                    timestamp=int(time.time())
                )
            )
            
            # Com confirm_delivery() habilitado, se chegou até aqui, a mensagem foi confirmada
            # Capturar timestamp T1 APÓS a confirmação (precisão melhorada)
            send_times[msg_id] = time.time()
            successful_deliveries += 1
            logging.info(f"Mensagem {msg_id} enviada e confirmada com {message_size} bytes")
                
        except pika.exceptions.UnroutableError:
            failed_deliveries += 1
            logging.error(f"Mensagem {msg_id} não pôde ser roteada (UnroutableError)")
        except pika.exceptions.NackError:
            failed_deliveries += 1
            logging.error(f"Mensagem {msg_id} foi rejeitada pelo broker (NackError)")
        except Exception as e:
            failed_deliveries += 1
            logging.error(f"Erro inesperado ao enviar mensagem {msg_id}: {e}")
            # Não registrar timestamp para mensagens que falharam
        
        # Rate Limiting: aguardar o intervalo calculado
        if sleep_interval > 0:
            time.sleep(sleep_interval)

    connection.close()
    end_send = time.time()
    
    # Log de estatísticas de entrega
    logging.info(f"Entrega finalizada: {successful_deliveries} sucessos, {failed_deliveries} falhas")

    with open(SEND_TIMES_FILE, 'w') as f:
        json.dump(send_times, f)

    with open(SUMMARY_FILE, 'w', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['total_sent', count])
        writer.writerow(['successful_deliveries', successful_deliveries])
        writer.writerow(['failed_deliveries', failed_deliveries])
        writer.writerow(['delivery_success_rate', (successful_deliveries / count * 100) if count > 0 else 0])
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