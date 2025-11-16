#!/bin/bash
# Script de inicialização do Kafka em modo KRaft

set -e

KAFKA_HOME="/opt/kafka"
CLUSTER_ID="${CLUSTER_ID:-MkU3OEVBNTcwNTJENDM2Qk}"
LOG_DIRS="${KAFKA_LOG_DIRS:-/tmp/kraft-combined-logs}"

# Criar diretório de logs se não existir
mkdir -p "$LOG_DIRS"

# Formatar o diretório de logs para KRaft (apenas na primeira execução)
if [ ! -f "$LOG_DIRS/meta.properties" ]; then
    echo "Formatando diretório de logs para KRaft..."
    "$KAFKA_HOME/bin/kafka-storage.sh" format \
        -t "$CLUSTER_ID" \
        -c "$KAFKA_HOME/config/kraft/server.properties"
fi

# Iniciar Kafka
exec "$KAFKA_HOME/bin/kafka-server-start.sh" "$KAFKA_HOME/config/kraft/server.properties"

