# 🚀 Benchmark TCC - Apache Kafka vs RabbitMQ

## 📖 Descrição

Implementação prática para o TCC **"APACHE KAFKA E RABBITMQ: UMA ANÁLISE COMPARATIVA ENTRE SISTEMAS DE MENSAGERIA EM APLICAÇÕES DE DIFERENTES PORTES"**.

Este projeto compara o desempenho de:
- **Baseline**: Comunicação HTTP síncrona (Flask)
- **RabbitMQ 4.1.1**: Com Quorum Queues
- **Apache Kafka 4.0**: Com KRaft mode (sem Zookeeper)

## 🎯 Objetivos

1. Avaliar latência (P50/P95/P99) e throughput
2. Comparar desempenho em 3 portes de aplicação:
   - **Pequeno**: 100 mensagens (aplicações corporativas internas)
   - **Médio**: 1.000 mensagens (plataformas estabelecidas)
   - **Grande**: 10.000 mensagens (serviços globais)
3. Fornecer dados objetivos para escolha de tecnologia

## 🛠️ Pré-requisitos

- Docker e Docker Compose
- Python 3.10+
- 4GB RAM mínimo
- 10GB espaço em disco

## 📦 Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/LeonardoFiamoncini/RMQ-and-Kafka-Comparative.git
cd RMQ-and-Kafka-Comparative
```

### 2. Configure o ambiente Python

```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Inicie os containers

```bash
docker compose up -d
```

Aguarde os containers ficarem saudáveis:

```bash
docker ps
```

## 🔬 Executando os Testes

### Opção 1: Executar todos os cenários (Recomendado)

```bash
# Executa todos os 9 cenários e gera gráficos automaticamente
./executar_todos_cenarios_tcc.sh
```

Este script:
1. Limpa logs antigos
2. Reinicia containers
3. Executa os 9 cenários (3 tecnologias × 3 portes)
4. Gera gráficos comparativos
5. Exibe resumo dos resultados

### Opção 2: Executar cenários individuais

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Iniciar servidor baseline (necessário apenas para testes baseline)
python3 main.py --server --port 5000 &

# Executar benchmark individual
python3 main.py --system <baseline|rabbitmq|kafka> --porte <pequeno|medio|grande>

# Exemplos:
python3 main.py --system baseline --porte pequeno
python3 main.py --system rabbitmq --porte medio
python3 main.py --system kafka --porte grande
```

### Gerar gráficos

Após executar os testes, gere os gráficos:

```bash
python3 gerar_graficos_tcc.py
```

## 📊 Resultados

Os resultados são salvos em:

- **Logs detalhados**: `logs/<tecnologia>/<run-id>/`
- **Resultados consolidados**: `logs/<tecnologia>/benchmark_results.csv`
- **Gráficos**: `logs/plots/`
  - `throughput_comparison_*.png` - Comparação de throughput
  - `latency_comparison_*.png` - Comparação de latências
  - `summary_matrix_*.png` - Matriz resumo
  - `summary_table_*.txt` - Tabela com todos os resultados

## 📈 Métricas Coletadas

Para cada cenário, são coletadas:

- **Throughput**: Mensagens processadas por segundo
- **Latência P50**: 50% das mensagens com latência menor que este valor
- **Latência P95**: 95% das mensagens com latência menor que este valor
- **Latência P99**: 99% das mensagens com latência menor que este valor

## 🏗️ Estrutura do Projeto

```
.
├── src/
│   ├── brokers/           # Implementações dos brokers
│   │   ├── baseline/       # Cliente/Servidor HTTP
│   │   ├── kafka/          # Produtor/Consumidor Kafka
│   │   └── rabbitmq/       # Produtor/Consumidor RabbitMQ
│   ├── core/              # Configurações e métricas
│   └── orchestration/     # Orquestração dos benchmarks
├── logs/                  # Resultados dos testes
├── config/                # Configurações
├── docker-compose.yml     # Definição dos containers
├── main.py               # Entry point principal
├── gerar_graficos_tcc.py # Gerador de gráficos
└── executar_todos_cenarios_tcc.sh  # Script de execução completa
```

## 🐳 Serviços Docker

- **RabbitMQ**: Porta 5672 (AMQP) e 15672 (Management)
- **Kafka**: Porta 9092 (Broker)
- **Baseline**: Porta 5000 (HTTP)

## ⚙️ Configurações

As configurações dos brokers estão em `src/core/config.py`:

```python
BROKER_CONFIGS = {
    "baseline": {
        "host": "localhost",
        "port": 5000,
    },
    "rabbitmq": {
        "host": "localhost",
        "port": 5672,
        "queue": "bcc-tcc",
        "username": "admin",
        "password": "admin123",
    },
    "kafka": {
        "bootstrap_servers": "localhost:9092",
        "topic": "bcc-tcc",
        "group_id": "tcc-queue-mode-group",
    }
}
```

## 🔍 Troubleshooting

### Containers não iniciam

```bash
# Verificar logs
docker compose logs

# Reiniciar containers
docker compose down
docker compose up -d
```

### Erro de conexão com brokers

```bash
# Verificar se os containers estão rodando
docker ps

# Verificar conectividade
nc -zv localhost 5672  # RabbitMQ
nc -zv localhost 9092  # Kafka
```

### Limpar dados antigos

```bash
# Limpar logs
rm -rf logs/*

# Limpar volumes Docker
docker compose down -v
```

## 📚 Referências

- **RabbitMQ**: https://www.rabbitmq.com/docs
- **Apache Kafka**: https://kafka.apache.org/documentation/
- **Docker Compose**: https://docs.docker.com/compose/

## 🤝 Contribuições

Este projeto foi desenvolvido como parte de um Trabalho de Conclusão de Curso (TCC) em Ciência da Computação.

## ✉️ Contato

Para dúvidas ou sugestões sobre este p
- **E-mail**: leonardosfiamoncini@gmail.com