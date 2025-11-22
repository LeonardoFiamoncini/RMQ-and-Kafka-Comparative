#!/bin/bash
#
# Script para limpar o tópico Kafka antes dos testes
#

echo "Limpando tópico Kafka..."

# Usar o path completo do Kafka no container
KAFKA_BIN="/opt/kafka/bin"

# Deletar o tópico se existir
docker exec kafka ${KAFKA_BIN}/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --delete \
    --topic bcc-tcc \
    2>/dev/null || true

sleep 2

# Recriar o tópico com configurações otimizadas
docker exec kafka ${KAFKA_BIN}/kafka-topics.sh \
    --bootstrap-server localhost:9092 \
    --create \
    --topic bcc-tcc \
    --partitions 16 \
    --replication-factor 1 \
    --config min.insync.replicas=1 \
    --config retention.ms=60000 \
    --config segment.ms=10000 \
    2>/dev/null || true

echo "Tópico Kafka limpo e recriado"