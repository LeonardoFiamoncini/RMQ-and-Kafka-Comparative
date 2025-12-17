#!/bin/bash
#
# Script para executar todos os 30 cenários do benchmark TCC
# Baseline, RabbitMQ e Kafka nos 5 sizes × 2 message-sizes
# Sizes: size1, size2, size3, size4, size5
# Message Sizes: 0.1KB, 1KB
#

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}EXECUTANDO TODOS OS CENÁRIOS DO TCC${NC}"
echo -e "${BLUE}================================================${NC}"

# Limpar logs antigos
echo -e "${YELLOW}Limpando logs antigos...${NC}"
rm -rf logs/*

# Parar e reiniciar containers
echo -e "${YELLOW}Reiniciando containers Docker...${NC}"
docker compose down --remove-orphans
docker compose up -d

# Aguardar containers iniciarem
echo -e "${YELLOW}Aguardando containers ficarem saudáveis...${NC}"
sleep 10

# Verificar se containers estão rodando
docker ps

# Limpar tópico Kafka para evitar mensagens antigas
echo -e "${YELLOW}Limpando tópico Kafka...${NC}"
chmod +x scripts/clear_kafka_topic.sh
./scripts/clear_kafka_topic.sh

# Ativar ambiente virtual
source venv/bin/activate

# Array de sistemas, sizes e message sizes
systems=("baseline" "rabbitmq" "kafka")
sizes=("size1" "size2" "size3" "size4" "size5")
message_sizes=(100 1000)  # 0.1KB, 1KB

# Iniciar servidor baseline em background
echo -e "${GREEN}Iniciando servidor Baseline...${NC}"
pkill -f "python3 main.py --server" || true
python3 main.py --server --port 5000 &
SERVER_PID=$!
sleep 3

# Executar benchmarks
total_scenarios=$((${#systems[@]} * ${#sizes[@]} * ${#message_sizes[@]}))
current_scenario=0

for system in "${systems[@]}"; do
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}Sistema: ${system^^}${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    for size in "${sizes[@]}"; do
        for msg_size in "${message_sizes[@]}"; do
            current_scenario=$((current_scenario + 1))
            echo -e "\n${GREEN}▶ [${current_scenario}/${total_scenarios}] Executando ${system} - Size ${size} - Message Size ${msg_size} bytes${NC}"
            python3 main.py --system $system --size $size --message-size $msg_size || true

            # Limpando tópico Kafka - apenas se o sistema for "kafka", de fato
            if [ "$system" == "kafka" ]; then
                echo -e "${YELLOW}Limpando tópico Kafka...${NC}"
                ./scripts/clear_kafka_topic.sh
            fi
            
            # Pequena pausa entre execuções
            sleep 2
        done
    done
done

# Parar servidor baseline
echo -e "\n${YELLOW}Parando servidor Baseline...${NC}"
kill $SERVER_PID || true

# Gerar gráficos
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}GERANDO GRÁFICOS${NC}"
echo -e "${BLUE}================================================${NC}"
python3 generate_plots.py

echo -e "\n${GREEN}EXECUÇÃO COMPLETA!${NC}"
echo -e "${GREEN}Resultados salvos em:${NC}"
echo -e "  • Logs: logs/"
echo -e "  • Gráficos: logs/plots/"

# Mostrar resumo final
if [ -f logs/plots/summary_table_*.txt ]; then
    echo -e "\n${BLUE}RESUMO DOS RESULTADOS:${NC}"
    cat logs/plots/summary_table_*.txt | head -40
fi
