from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import ConfigResource, ConfigResourceType, NewTopic
import sys
import time
import logging
from datetime import datetime
import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(BASE_DIR, 'logs', 'kafka')
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

def create_topic_for_queue_mode(topic_name='bcc-tcc', num_partitions=3, replication_factor=1):
    """
    Cria um tópico configurado para Queue Mode (Share Groups) do Kafka 4.0
    """
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers='localhost:9092',
            client_id='queue_mode_admin'
        )
        
        # Verificar se o tópico já existe
        existing_topics = admin_client.list_topics()
        if topic_name in existing_topics:
            logging.info(f"Tópico {topic_name} já existe")
            admin_client.close()
            return True
        
        # Criar novo tópico com configurações para Queue Mode
        topic = NewTopic(
            name=topic_name,
            num_partitions=num_partitions,
            replication_factor=replication_factor,
            topic_configs={
                # Configurações específicas para Queue Mode/Share Groups
                'cleanup.policy': 'delete',
                'retention.ms': '604800000',  # 7 dias
                'segment.ms': '604800000',    # 7 dias
                'compression.type': 'gzip'
            }
        )
        
        # Criar o tópico
        fs = admin_client.create_topics([topic])
        try:
            # Aguardar a criação do tópico
            for topic_name, f in fs.items():
                f.result()  # Aguardar a criação
                logging.info(f"Tópico {topic_name} criado com sucesso para Queue Mode")
        except Exception as e:
            logging.error(f"Erro ao criar tópico {topic_name}: {e}")
            return False
        
        admin_client.close()
        return True
        
    except Exception as e:
        logging.error(f"Erro na criação do tópico: {e}")
        return False

def send_messages(count=1000, message_size=100, rps=None):
    from collections import OrderedDict

    # Criar tópico para Queue Mode antes de enviar mensagens
    if not create_topic_for_queue_mode():
        logging.error("Falha ao criar tópico para Queue Mode")
        return

    send_times = OrderedDict()
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        acks='all',  # Confirmação de todos os brokers
        # Configurações específicas para Queue Mode
        retries=3,
        retry_backoff_ms=100,
        max_in_flight_requests_per_connection=1  # Garantir ordenação
    )

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
        
        # Enviar mensagem e aguardar confirmação
        future = producer.send('bcc-tcc', value=payload)
        try:
            # Aguardar confirmação do broker
            future.get(timeout=10)
            
            # Capturar timestamp T1 APÓS a confirmação (precisão melhorada)
            send_times[msg_id] = time.time()
            logging.info(f"Mensagem {msg_id} enviada e confirmada com {message_size} bytes")
        except Exception as e:
            logging.error(f"Falha ao enviar mensagem {msg_id}: {e}")
            # Não registrar timestamp para mensagens que falharam
        
        # Rate Limiting: aguardar o intervalo calculado
        if sleep_interval > 0:
            time.sleep(sleep_interval)

    producer.flush()
    end_send = time.time()

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

    json.dump(send_times, open(SEND_TIMES_FILE, 'w'))

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    rps = int(sys.argv[3]) if len(sys.argv) > 3 else None
    send_messages(count, size, rps)