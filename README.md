# Benchmark TCC - Apache Kafka vs RabbitMQ

## Descrição

Implementação prática para o Trabalho de Conclusão de Curso (TCC) cujo tema é **"Apache Kafka e RabbitMQ: Uma análise comparativa entre Sistemas de Mensageria em aplicações de diferentes portes"**.

Este projeto compara o desempenho de:
- **Baseline**: Comunicação HTTP síncrona (Flask)
- **RabbitMQ 4.1.1**: Com Quorum Queues
- **Apache Kafka 4.0**: Com KRaft mode (sem Zookeeper)

## Objetivos

1. Avaliar latência (P95/P99) e throughput
2. Comparar desempenho em 5 sizes de carga:
   - **Size 1**: 100 mensagens
   - **Size 2**: 1.000 mensagens
   - **Size 3**: 10.000 mensagens
   - **Size 4**: 100.000 mensagens
   - **Size 5**: 1.000.000 mensagens
3. Avaliar impacto do tamanho das mensagens em 2 configurações:
   - **100 bytes**: Equivalente a 0.1 KB
   - **1.000 bytes**: Equivalente a 1 KB 
4. Fornecer dados objetivos para escolha de tecnologia

## Pré-requisitos

- Docker e Docker Compose
- Python 3.10+
- 4GB RAM mínimo
- 10GB espaço em disco

## Instalação

### 1. Clone o repositório

```bash
git clone https://github.com/LeonardoFiamoncini/RMQ-and-Kafka-Comparative.git
cd RMQ-and-Kafka-Comparative
```

### 2. Configure o ambiente Python

```bash
# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

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

## Executando os Testes

### Opção 1: Executar todos os cenários (Recomendado)

```bash
# Executa todos os 45 cenários e gera gráficos automaticamente
./execute_all.sh
```

Este script:
1. Limpa logs antigos
2. Reinicia containers
3. Executa os 45 cenários (3 tecnologias × 5 sizes × 2 message-sizes)
4. Gera gráficos comparativos (separados por message-size)
5. Exibe resumo dos resultados

### Opção 2: Executar cenários individuais

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Iniciar servidor baseline (necessário apenas para testes baseline)
python3 main.py --server --port 5000 &

# Executar benchmark individual
python3 main.py --system <baseline|rabbitmq|kafka> --size <size1|size2|size3|size4|size5> [--message-size <bytes>]

# Exemplos:
python3 main.py --system kafka --size size1 --message-size 100
python3 main.py --system rabbitmq --size size2 --message-size 1000
```

### Gerar gráficos

Após executar os testes, gere os gráficos:

```bash
python3 generate_plots.py
```

## Resultados

Os resultados são salvos em:

- **Logs detalhados**: `logs/<tecnologia>/<run-id>/`
- **Resultados consolidados**: `logs/<tecnologia>/benchmark_results.csv` (inclui coluna `message_size`)
- **Gráficos**: `logs/plots/`
  - `throughput_comparison_*bytes_*.png` - Comparação de throughput por message-size
  - `latency_comparison_*bytes_*.png` - Comparação de latências por message-size
  - `summary_matrix_*bytes_*.png` - Matriz resumo por message-size
  - `summary_table_*.txt` - Tabela consolidada com todos os resultados

## Métricas Coletadas

Para cada cenário, são coletadas:

- **Throughput**: Mensagens processadas por segundo
- **Latência P95**: 95% das mensagens com latência menor que este valor
- **Latência P99**: 99% das mensagens com latência menor que este valor
- **Message Size**: Tamanho de cada mensagem em bytes (100, 1.000)

## Estrutura do Projeto

```
.
├── src/
│   ├── brokers/            # Implementações de cada tecnologia
│   │   ├── baseline/       # Cliente/Servidor HTTP
│   │   ├── kafka/          # Produtor/Consumidor Kafka
│   │   └── rabbitmq/       # Produtor/Consumidor RabbitMQ
│   ├── core/               # Configurações e métricas
│   └── orchestration/      # Orquestração dos benchmarks
├── logs/                   # Resultados dos testes
├── config/                 # Configurações
├── docker-compose.yml      # Definição dos containers
├── main.py                 # Entry point principal
├── generate_plots.py       # Gerador de gráficos
└── execute_all.sh          # Script de execução completa
```

## Serviços Docker

- **RabbitMQ**: Porta 5672 (AMQP)
- **Kafka**: Porta 9092 (Broker)
- **Baseline**: Porta 5000 (HTTP)

## Configurações

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
        "username": "user",
        "password": "password",
    },
    "kafka": {
        "bootstrap_servers": "localhost:9092",
        "topic": "bcc-tcc",
        "group_id": "tcc-queue-mode-group",
    }
}
```

## Troubleshooting

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

## Referências

- **RabbitMQ**: https://www.rabbitmq.com/docs
- **Apache Kafka**: https://kafka.apache.org/documentation/
- **Docker Compose**: https://docs.docker.com/compose/

## Contribuições

Este projeto foi desenvolvido como parte de um Trabalho de Conclusão de Curso (TCC) para a obtenção do título de Bacharel em Ciência da Computação.

## Contato

Para dúvidas ou sugestões sobre este p
- **E-mail**: leonardosfiamoncini@gmail.com