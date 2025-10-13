"""
Servidor HTTP baseline para comparação síncrona
"""
from flask import Flask, request, jsonify
import time
import threading
from datetime import datetime
from ...core.config import BROKER_CONFIGS
from ...core.logger import Logger

class BaselineServer:
    """Servidor HTTP baseline para comparação síncrona"""
    
    def __init__(self):
        self.config = BROKER_CONFIGS["baseline"]
        self.logger = Logger.get_logger("baseline.server")
        self.app = Flask(__name__)
        self._setup_routes()
        
        # Contadores para métricas
        self.request_count = 0
        self.total_processing_time = 0.0
        self.start_time = time.time()
        self.lock = threading.Lock()
        
    def _setup_routes(self):
        """Configura as rotas da aplicação"""
        
        @self.app.route("/notify", methods=["POST"])
        def notify():
            """Endpoint para receber notificações HTTP (baseline síncrona)"""
            # Simular tempo de processamento
            processing_start = time.time()
            time.sleep(0.001)  # 1ms de processamento
            processing_end = time.time()
            processing_time = processing_end - processing_start

            with self.lock:
                self.request_count += 1
                self.total_processing_time += processing_time
                
                current_uptime = time.time() - self.start_time
                current_rps = self.request_count / current_uptime if current_uptime > 0 else 0
                avg_processing_time = self.total_processing_time / self.request_count if self.request_count > 0 else 0

                self.logger.info(f"Mensagem recebida. Total: {self.request_count}, Avg Proc Time: {avg_processing_time:.6f}s, RPS: {current_rps:.2f}")

            return jsonify({"status": "success", "processing_time": processing_time}), 200

        @self.app.route("/stats", methods=["GET"])
        def stats():
            """Endpoint para obter estatísticas do servidor"""
            with self.lock:
                current_uptime = time.time() - self.start_time
                current_rps = self.request_count / current_uptime if current_uptime > 0 else 0
                avg_processing_time = self.total_processing_time / self.request_count if self.request_count > 0 else 0
                
                stats_data = {
                    "total_requests": self.request_count,
                    "total_processing_time": self.total_processing_time,
                    "avg_processing_time": avg_processing_time,
                    "uptime": current_uptime,
                    "requests_per_second": current_rps
                }
            return jsonify(stats_data), 200

        @self.app.route("/health", methods=["GET"])
        def health():
            """Endpoint de health check"""
            return jsonify({"status": "healthy", "timestamp": time.time()}), 200

        @self.app.route("/reset", methods=["POST"])
        def reset_counters():
            """Endpoint para resetar contadores"""
            with self.lock:
                self.request_count = 0
                self.total_processing_time = 0.0
                self.start_time = time.time()
            self.logger.info("Contadores do servidor resetados")
            return jsonify({"status": "counters reset"}), 200

    def run(self, host: str = None, port: int = None, debug: bool = False):
        """Executa o servidor"""
        if host is None:
            host = self.config["host"]
        if port is None:
            port = self.config["port"]
            
        self.logger.info("Servidor baseline está rodando")
        self.logger.info(f"🔗 Endpoints disponíveis:")
        self.logger.info(f"   • POST /notify - Receber notificações")
        self.logger.info(f"   • GET /stats - Estatísticas do servidor")
        self.logger.info(f"   • GET /health - Health check")
        self.logger.info(f"   • POST /reset - Resetar contadores")
        
        self.app.run(host=host, port=port, debug=debug)

def main():
    """Função principal para execução standalone"""
    server = BaselineServer()
    try:
        server.run()
    except KeyboardInterrupt:
        print("\n[!] Servidor interrompido pelo usuário")

if __name__ == "__main__":
    main()
