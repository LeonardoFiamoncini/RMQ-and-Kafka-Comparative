#!/bin/bash
#
# Script para limpar o tópico Kafka antes dos testes
#

echo "Limpando tópico Kafka..."

# Usa o path completo do Kafka no container
KAFKA_BIN="/opt/kafka/bin"

# Deleta o tópico se existir
docker exec kafka ${KAFKA_BIN}/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --delete \
    --topic bcc-tcc \
    2>/dev/null || true

sleep 2

# Recria o tópico
docker exec kafka ${KAFKA_BIN}/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --topic bcc-tcc \
    --partitions 1 \
    --replication-factor 1 \
    2>/dev/null || true

echo "Tópico Kafka limpo e recriado"