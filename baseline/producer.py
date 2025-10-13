import requests
import sys
import time
import logging
from datetime import datetime
import os
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(BASE_DIR, 'logs', 'baseline')
os.makedirs(LOG_DIR, exist_ok=True)

DATE_STR = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
PRODUCER_LOG = os.path.join(LOG_DIR, f'{DATE_STR}_producer-queue.txt')
SEND_TIMES_FILE = os.path.join(LOG_DIR, f'{DATE_STR}_send_times.json')
SUMMARY_FILE = os.path.join(LOG_DIR, f'{DATE_STR}_summary.csv')

logging.basicConfig(
    filename=PRODUCER_LOG,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

def send_messages(count=1000, message_size=100, rps=None, server_url='http://localhost:5000'):
    """
    Envia mensagens HTTP para o servidor baseline
    
    Args:
        count: Número de mensagens a enviar
        message_size: Tamanho da mensagem em bytes
        rps: Rate limiting (Requests Per Second)
        server_url: URL do servidor baseline
    """
    from collections import OrderedDict
    
    send_times = OrderedDict()
    message_content = 'x' * (message_size - 10)
    
    # Calcular intervalo de sleep para Rate Limiting
    sleep_interval = 0
    if rps and rps > 0:
        sleep_interval = 1.0 / rps
        logging.info(f"Rate Limiting ativado: {rps} RPS (intervalo: {sleep_interval:.6f}s)")
    
    # Verificar se o servidor está rodando
    try:
        health_response = requests.get(f"{server_url}/health", timeout=5)
        if health_response.status_code != 200:
            logging.error(f"Servidor não está saudável: {health_response.status_code}")
            return
        logging.info("Servidor baseline está rodando")
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao conectar com o servidor: {e}")
        return
    
    # Resetar contadores do servidor
    try:
        requests.post(f"{server_url}/reset", timeout=5)
        logging.info("Contadores do servidor resetados")
    except requests.exceptions.RequestException as e:
        logging.warning(f"Erro ao resetar contadores: {e}")
    
    start_send = time.time()
    successful_requests = 0
    failed_requests = 0
    
    for i in range(count):
        msg_id = str(i)
        payload = {"id": msg_id, "body": message_content}
        send_times[msg_id] = time.time()
        
        try:
            # Enviar requisição HTTP POST
            response = requests.post(
                f"{server_url}/notify",
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                successful_requests += 1
                response_data = response.json()
                processing_time = response_data.get('processing_time', 0)
                logging.info(f"Mensagem {msg_id} enviada com sucesso - Tempo de processamento: {processing_time:.6f}s")
            else:
                failed_requests += 1
                logging.error(f"Falha ao enviar mensagem {msg_id}: HTTP {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            failed_requests += 1
            logging.error(f"Erro ao enviar mensagem {msg_id}: {e}")
        
        # Rate Limiting: aguardar o intervalo calculado
        if sleep_interval > 0:
            time.sleep(sleep_interval)
    
    end_send = time.time()
    
    # Obter estatísticas finais do servidor
    try:
        stats_response = requests.get(f"{server_url}/stats", timeout=5)
        if stats_response.status_code == 200:
            stats = stats_response.json()
            logging.info(f"Estatísticas do servidor: {stats}")
    except requests.exceptions.RequestException as e:
        logging.warning(f"Erro ao obter estatísticas: {e}")
    
    # Salvar summary
    with open(SUMMARY_FILE, 'w', newline='') as f:
        import csv
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['total_sent', count])
        writer.writerow(['successful_requests', successful_requests])
        writer.writerow(['failed_requests', failed_requests])
        writer.writerow(['send_duration_sec', end_send - start_send])
        if rps:
            writer.writerow(['target_rps', rps])
            actual_rps = count / (end_send - start_send)
            writer.writerow(['actual_rps', actual_rps])
    
    # Salvar tempos de envio
    with open(SEND_TIMES_FILE, 'w') as f:
        json.dump(send_times, f)
    
    logging.info(f"Envio finalizado: {successful_requests} sucessos, {failed_requests} falhas")

if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    rps = int(sys.argv[3]) if len(sys.argv) > 3 else None
    server_url = sys.argv[4] if len(sys.argv) > 4 else 'http://localhost:5000'
    
    send_messages(count, size, rps, server_url)
