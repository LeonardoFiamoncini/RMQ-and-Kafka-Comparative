#!/bin/bash

echo "🎨 EXECUTANDO BENCHMARKS PARA GERAÇÃO DE GRÁFICOS"
echo "=================================================="
echo ""

source venv/bin/activate

# Baseline
echo "1/3: Executando Baseline..."
python main.py --server --port 5000 > /tmp/server.log 2>&1 &
SERVER_PID=$!
sleep 5
python main.py --count 10 --producers 1 --consumers 4 --system baseline
kill $SERVER_PID 2>/dev/null || true

# RabbitMQ (várias configurações)
echo "2/3: Executando RabbitMQ..."
python main.py --count 100 --producers 1 --consumers 4 --system rabbitmq
python main.py --count 1000 --producers 4 --consumers 4 --system rabbitmq

# Kafka (várias configurações)
echo "3/3: Executando Kafka..."
python main.py --count 100 --producers 1 --consumers 4 --system kafka
python main.py --count 1000 --producers 4 --consumers 4 --system kafka

echo ""
echo "✅ Benchmarks concluídos!"
echo "📊 Gerando gráficos consolidados..."

chmod +x generate_plots.py
python generate_plots.py --system all

echo ""
echo "🎨 GRÁFICOS GERADOS COM SUCESSO!"
echo "📁 Localização: logs/plots/"
ls -lh logs/plots/*.png | awk '{print "   •", $NF, "("$5")"}'
echo ""
