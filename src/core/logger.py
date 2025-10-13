"""
Sistema de logging centralizado
"""
import logging
import logging.config
from datetime import datetime
from pathlib import Path
from .config import LOGGING_CONFIG, LOGS_DIR

class Logger:
    """Classe para gerenciamento de logs"""
    
    _initialized = False
    
    @classmethod
    def initialize(cls):
        """Inicializa o sistema de logging"""
        if not cls._initialized:
            # Criar diretório de logs se não existir
            LOGS_DIR.mkdir(exist_ok=True)
            
            # Configurar logging
            logging.config.dictConfig(LOGGING_CONFIG)
            cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Obtém um logger configurado"""
        if not cls._initialized:
            cls.initialize()
        return logging.getLogger(name)
    
    @classmethod
    def get_benchmark_logger(cls, tech: str, component: str) -> logging.Logger:
        """Obtém um logger específico para benchmark"""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_file = LOGS_DIR / tech / f"{timestamp}_{component}.log"
        
        # Criar diretório se não existir
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger = logging.getLogger(f"benchmark.{tech}.{component}")
        
        # Remover handlers existentes para evitar duplicação
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Configurar handler específico para arquivo
        file_handler = logging.FileHandler(log_file, mode='a')
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Handler para console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        logger.setLevel(logging.DEBUG)
        return logger
