from flask import Flask, request, jsonify
import time
import logging
import os
from datetime import datetime

# Configuração de logging
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
LOG_DIR = os.path.join(BASE_DIR, 'logs', 'baseline')
os.makedirs(LOG_DIR, exist_ok=True)

DATE_STR = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
SERVER_LOG = os.path.join(LOG_DIR, f'{DATE_STR}_server.log')

logging.basicConfig(
    filename=SERVER_LOG,
    filemode="a",
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

app = Flask(__name__)

# Contadores para métricas
request_count = 0
start_time = None
request_times = []

@app.route('/notify', methods=['POST'])
def notify():
    """
    Endpoint para receber notificações HTTP (baseline síncrona)
    Simula o comportamento de um sistema de notificação
    """
    global request_count, start_time, request_times
    
    # Inicializar contadores na primeira requisição
    if start_time is None:
        start_time = time.time()
    
    # Incrementar contador
    request_count += 1
    request_time = time.time()
    
    try:
        # Obter dados da requisição
        data = request.get_json() or {}
        message_id = data.get('id', f'msg_{request_count}')
        message_body = data.get('body', '')
        
        # Simular processamento mínimo (baseline)
        # Em um sistema real, aqui seria feita a lógica de notificação
        time.sleep(0.001)  # 1ms de processamento simulado
        
        # Registrar tempo de processamento
        processing_time = time.time() - request_time
        request_times.append(processing_time)
        
        # Log da requisição
        logging.info(f"Requisição {request_count} processada - ID: {message_id}, Tempo: {processing_time:.6f}s")
        
        # Resposta de sucesso
        return jsonify({
            'status': 'success',
            'message_id': message_id,
            'processing_time': processing_time,
            'request_count': request_count
        }), 200
        
    except Exception as e:
        logging.error(f"Erro ao processar requisição {request_count}: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e),
            'request_count': request_count
        }), 500

@app.route('/stats', methods=['GET'])
def stats():
    """
    Endpoint para obter estatísticas do servidor
    """
    global request_count, start_time, request_times
    
    if not request_times:
        return jsonify({
            'total_requests': request_count,
            'uptime': 0,
            'avg_processing_time': 0,
            'min_processing_time': 0,
            'max_processing_time': 0
        })
    
    uptime = time.time() - start_time if start_time else 0
    avg_time = sum(request_times) / len(request_times)
    min_time = min(request_times)
    max_time = max(request_times)
    
    return jsonify({
        'total_requests': request_count,
        'uptime': uptime,
        'avg_processing_time': avg_time,
        'min_processing_time': min_time,
        'max_processing_time': max_time,
        'requests_per_second': request_count / uptime if uptime > 0 else 0
    })

@app.route('/health', methods=['GET'])
def health():
    """
    Endpoint de health check
    """
    return jsonify({'status': 'healthy', 'timestamp': time.time()}), 200

@app.route('/reset', methods=['POST'])
def reset():
    """
    Endpoint para resetar contadores (útil para testes)
    """
    global request_count, start_time, request_times
    request_count = 0
    start_time = None
    request_times = []
    logging.info("Contadores resetados")
    return jsonify({'status': 'reset'}), 200

if __name__ == '__main__':
    print("🚀 Iniciando servidor HTTP baseline...")
    print(f"📊 Logs salvos em: {SERVER_LOG}")
    print("🔗 Endpoints disponíveis:")
    print("   • POST /notify - Receber notificações")
    print("   • GET /stats - Estatísticas do servidor")
    print("   • GET /health - Health check")
    print("   • POST /reset - Resetar contadores")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
