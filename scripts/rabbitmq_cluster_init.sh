#!/bin/bash

# Script para inicializar o cluster RabbitMQ
# Este script será executado nos nós rabbitmq-2 e rabbitmq-3

set -e

echo "Aguardando RabbitMQ-1 ficar disponível..."
until rabbitmq-diagnostics ping -n rabbit@rabbitmq-1; do
    echo "RabbitMQ-1 não está disponível ainda. Aguardando..."
    sleep 5
done

echo "RabbitMQ-1 está disponível. Configurando cluster..."

# Parar a aplicação RabbitMQ
rabbitmqctl stop_app

# Resetar o nó (apenas se não estiver em cluster)
rabbitmqctl reset

# Juntar ao cluster
rabbitmqctl join_cluster rabbit@rabbitmq-1

# Iniciar a aplicação
rabbitmqctl start_app

echo "Nó juntou-se ao cluster com sucesso!"

# Verificar status do cluster
rabbitmqctl cluster_status
