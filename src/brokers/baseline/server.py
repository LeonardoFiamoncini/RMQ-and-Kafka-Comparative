"""
Implementação simplificada do servidor Baseline HTTP para TCC
"""

import time
from typing import Optional
from flask import Flask, request, jsonify

from ...core.config import BROKER_CONFIGS
from ...core.logger import Logger


class BaselineServer:
    """Servidor HTTP simplificado - processa requisições síncronas"""

    def __init__(self, port: int = 5000):
        self.app = Flask(__name__)
        self.logger = Logger.get_logger("baseline.server")
        self.config = BROKER_CONFIGS["baseline"]
        self.port = port
        self.messages_received = 0
        
        # Configurar rotas
        self._setup_routes()

    def _setup_routes(self):
        """Configura as rotas do servidor Flask"""
        
        @self.app.route("/health", methods=["GET"])
        def health():
            """Endpoint de health check"""
            return jsonify({"status": "healthy", "messages_received": self.messages_received})
        
        @self.app.route("/message", methods=["POST"])
        def receive_message():
            """Recebe e processa mensagem síncrona"""
            try:
                # Simular processamento mínimo (1ms)
                time.sleep(0.001)
                
                self.messages_received += 1
                
                # Log a cada 1000 mensagens
                if self.messages_received % 1000 == 0:
                    self.logger.info(f"Processadas {self.messages_received} mensagens")
                
                return jsonify({"status": "ok", "processed": True}), 200
                
            except Exception as e:
                self.logger.error(f"Erro ao processar mensagem: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

    def run(self, host: str = "0.0.0.0", port: Optional[int] = None):
        """Inicia o servidor Flask"""
        if port is None:
            port = self.port
            
        self.logger.info(f"Servidor Baseline HTTP iniciando na porta {port}...")
        
        # Configurar Flask para modo produção
        self.app.run(
            host=host,
            port=port,
            debug=False,
            threaded=True  # Permitir múltiplas requisições simultâneas
        )