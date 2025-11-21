#!/bin/bash
#
# Script para executar todos os 9 cenários do benchmark TCC
# Baseline, RabbitMQ e Kafka nos 3 portes: pequeno, médio e grande
#

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}🚀 EXECUTANDO TODOS OS CENÁRIOS DO TCC${NC}"
echo -e "${BLUE}================================================${NC}"

# Limpar logs antigos
echo -e "${YELLOW}Limpando logs antigos...${NC}"
rm -rf logs/*

# Parar e reiniciar containers
echo -e "${YELLOW}Reiniciando containers Docker...${NC}"
docker compose down
docker compose up -d

# Aguardar containers iniciarem
echo -e "${YELLOW}Aguardando containers ficarem saudáveis...${NC}"
sleep 10

# Verificar se containers estão rodando
docker ps

# Ativar ambiente virtual
source venv/bin/activate

# Array de sistemas e portes
systems=("baseline" "rabbitmq" "kafka")
portes=("pequeno" "medio" "grande")

# Iniciar servidor baseline em background
echo -e "${GREEN}Iniciando servidor Baseline...${NC}"
pkill -f "python3 main.py --server" || true
python3 main.py --server --port 5000 &
SERVER_PID=$!
sleep 3

# Executar benchmarks
for system in "${systems[@]}"; do
    echo -e "\n${BLUE}================================================${NC}"
    echo -e "${BLUE}Sistema: ${system^^}${NC}"
    echo -e "${BLUE}================================================${NC}"
    
    for porte in "${portes[@]}"; do
        echo -e "\n${GREEN}▶ Executando ${system} - Porte ${porte}${NC}"
        python3 main.py --system $system --porte $porte || true
        
        # Pequena pausa entre execuções
        sleep 2
    done
done

# Parar servidor baseline
echo -e "\n${YELLOW}Parando servidor Baseline...${NC}"
kill $SERVER_PID || true

# Gerar gráficos
echo -e "\n${BLUE}================================================${NC}"
echo -e "${BLUE}📊 GERANDO GRÁFICOS${NC}"
echo -e "${BLUE}================================================${NC}"
python3 gerar_graficos_tcc.py

echo -e "\n${GREEN}✅ EXECUÇÃO COMPLETA!${NC}"
echo -e "${GREEN}Resultados salvos em:${NC}"
echo -e "  • Logs: logs/"
echo -e "  • Gráficos: logs/plots/"

# Mostrar resumo final
if [ -f logs/plots/summary_table_*.txt ]; then
    echo -e "\n${BLUE}📋 RESUMO DOS RESULTADOS:${NC}"
    cat logs/plots/summary_table_*.txt | head -40
fi
