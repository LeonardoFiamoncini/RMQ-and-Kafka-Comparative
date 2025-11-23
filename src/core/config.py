"""
Configurações centralizadas do projeto.

Este módulo contém todas as configurações do sistema, incluindo
configurações de brokers, logging, benchmark e chaos engineering.
"""

from pathlib import Path

# Diretórios do projeto
PROJECT_ROOT = Path(__file__).parent.parent.parent
SRC_DIR = PROJECT_ROOT / "src"
LOGS_DIR = PROJECT_ROOT / "logs"
CONFIG_DIR = PROJECT_ROOT / "config"

# Configurações dos brokers
BROKER_CONFIGS = {
    "kafka": {
        "bootstrap_servers": "localhost:9092",
        "topic": "bcc-tcc",
        "group_id": "tcc-queue-mode-group",
        "container_name": "kafka",
        "port": 9092,
    },
    "rabbitmq": {
        "host": "localhost",
        "port": 5672,
        "username": "user",
        "password": "password",
        "queue": "bcc-tcc",
        "container_names": ["rabbitmq-1", "rabbitmq-2", "rabbitmq-3"],
        "management_port": 15672,
    },
    "baseline": {"host": "localhost", "port": 5000, "endpoint": "/notify"},
}

# Configurações de logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
        "detailed": {
            "format": (
                "%(asctime)s - %(name)s - %(levelname)s - "
                "%(funcName)s:%(lineno)d - %(message)s"
            )
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.FileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOGS_DIR / "application.log"),
            "mode": "a",
        },
    },
    "loggers": {
        "": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False}
    },
}

