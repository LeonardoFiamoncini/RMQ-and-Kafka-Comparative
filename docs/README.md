# 🎓 Benchmark Comparativo para TCC

**Trabalho de Conclusão de Curso (TCC) - Bacharelado em Ciência da Computação**

Este projeto implementa um sistema completo de benchmark comparativo entre **RabbitMQ**, **Apache Kafka** e **HTTP Síncrono**, desenvolvido para análise de performance, tolerância a falhas e escalabilidade de sistemas de mensageria. O sistema foi projetado seguindo rigorosos padrões acadêmicos e de engenharia de software.

## 📋 Índice

1. [Visão Geral do Projeto](#-visão-geral-do-projeto)
2. [Pré-requisitos do Sistema](#-pré-requisitos-do-sistema)
3. [Instalação Completa](#-instalação-completa)
4. [Configuração do Ambiente](#-configuração-do-ambiente)
5. [Execução de Todos os Testes](#-execução-de-todos-os-testes)
6. [Análise e Visualização dos Resultados](#-análise-e-visualização-dos-resultados)
7. [Interpretação dos Resultados](#-interpretação-dos-resultados)
8. [Solução de Problemas](#-solução-de-problemas)
9. [Documentação Técnica](#-documentação-técnica)

---

## 🎯 Visão Geral do Projeto

### Objetivos Acadêmicos
- **Comparação Quantitativa**: Análise estatística de performance entre RabbitMQ, Kafka e HTTP
- **Tolerância a Falhas**: Avaliação de recuperação e disponibilidade em cenários de falha
- **Escalabilidade**: Teste de comportamento com múltiplos clientes concorrentes
- **Reprodutibilidade**: Metodologia científica rigorosa para replicação dos resultados

### 🔬 Garantia de Reprodutibilidade Total

Este projeto foi desenvolvido com **foco total em reprodutibilidade científica**, garantindo que os resultados possam ser replicados em **qualquer hardware e sistema operacional**:

✅ **Versões Fixas e Obrigatórias**:
- RabbitMQ: `4.1.1` (imagem: `rabbitmq:4.1.1-management`)
- Apache Kafka: `4.0.0` (imagem: `apache/kafka:4.0.0`)
- Python: `3.12+` (com versões fixas em `requirements.txt`)

✅ **Configurações Padronizadas**:
- Arquivo `docker-compose.yml` com versões fixas
- Configuração KRaft em `config/kraft-server.properties`
- Cluster IDs fixos para consistência

✅ **Ambiente Containerizado**:
- Docker e Docker Compose para isolamento completo
- Scripts de setup automatizados (`scripts/setup_dev_environment.sh`)
- Compatibilidade multi-plataforma (Linux, macOS, Windows/WSL2)

✅ **Documentação Completa**:
- Instruções detalhadas para cada sistema operacional
- Troubleshooting para problemas comuns
- Exemplos de execução e análise

### Tecnologias Implementadas
- **RabbitMQ 4.1.1** (imagem: `rabbitmq:4.1.1-management`): Com Quorum Queues e cluster de 3 nós
- **Apache Kafka 4.0** (imagem: `apache/kafka:4.0.0`): Com KRaft mode e Queue Mode (KIP-932)
- **HTTP Síncrono**: Baseline para comparação de latência (Flask)
- **Docker**: Containerização completa da infraestrutura
- **Python 3.12+**: Implementação dos clientes e orquestração
- **Kafdrop 3.30.0**: Interface web para monitoramento do Kafka

### Métricas Coletadas
- **Latência End-to-End**: Tempo total de envio até processamento
- **Throughput**: Mensagens processadas por segundo
- **Taxa de Sucesso**: Percentual de entrega garantida
- **Uso de Recursos**: CPU e memória dos brokers
- **Tempo de Recuperação**: Após falhas simuladas

---

## 🖥️ Pré-requisitos do Sistema

### Especificações Mínimas
- **Sistema Operacional**: 
  - **Linux**: Ubuntu 22.04 LTS ou superior, Debian 11+, Fedora 36+, ou qualquer distribuição com suporte a Docker
  - **macOS**: macOS 11 (Big Sur) ou superior
  - **Windows**: Windows 10/11 com WSL2 ou Docker Desktop
- **RAM**: Mínimo 4GB (recomendado 8GB)
- **CPU**: Mínimo 2 cores (recomendado 4 cores)
- **Armazenamento**: Mínimo 10GB livres
- **Rede**: Conexão com internet para download de dependências

### Software Necessário
- **Docker**: Versão 20.10 ou superior
- **Docker Compose**: Versão 2.0 ou superior (plugin ou standalone)
- **Python**: Versão 3.10 ou superior (3.12 recomendado)
- **Git**: Para clonagem do repositório
- **Curl**: Para testes de conectividade
- **Bash**: Para execução dos scripts de setup (Linux/macOS) ou Git Bash/WSL (Windows)

### Verificação dos Pré-requisitos

#### Linux (Ubuntu/Debian/Fedora)
```bash
# Verificar versão do sistema
lsb_release -a 2>/dev/null || cat /etc/os-release

# Verificar RAM disponível
free -h

# Verificar CPU
lscpu | grep "CPU(s):"

# Verificar espaço em disco
df -h

# Verificar Docker
docker --version
docker compose version

# Verificar Python
python3 --version
pip3 --version
```

#### macOS
```bash
# Verificar versão do macOS
sw_vers

# Verificar RAM disponível
sysctl hw.memsize | awk '{print $2/1024/1024/1024 " GB"}'

# Verificar CPU
sysctl -n hw.ncpu

# Verificar espaço em disco
df -h

# Verificar Docker
docker --version
docker compose version

# Verificar Python
python3 --version
pip3 --version
```

#### Windows (WSL2 ou Docker Desktop)
```powershell
# No PowerShell ou WSL
# Verificar versão do Windows
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"

# Verificar Docker
docker --version
docker compose version

# Verificar Python (no WSL)
python3 --version
pip3 --version
```

---

## 🚀 Instalação Completa

### Passo 1: Clonagem do Repositório
```bash
# Clonar o repositório
git clone <URL_DO_REPOSITORIO>
cd RMQ-and-Kafka-Comparative

# Verificar estrutura do projeto
ls -la
```

### Passo 2: Configuração Automática do Ambiente

**Compatibilidade Multi-OS**: O script `setup_dev_environment.sh` funciona em Linux e macOS. Para Windows, use WSL2 ou Docker Desktop.

#### Linux/macOS
```bash
# Dar permissões de execução
chmod +x scripts/setup_dev_environment.sh

# Executar configuração automática
./scripts/setup_dev_environment.sh
```

#### Windows (WSL2)
```bash
# No terminal WSL2
chmod +x scripts/setup_dev_environment.sh
./scripts/setup_dev_environment.sh
```

#### Windows (Docker Desktop)
```powershell
# Instalar Docker Desktop manualmente:
# https://www.docker.com/products/docker-desktop

# No PowerShell ou WSL2, instalar Python e dependências:
python -m venv venv
.\venv\Scripts\activate  # PowerShell
# ou
source venv/bin/activate  # WSL2

pip install -r requirements.txt
```

**⚠️ IMPORTANTE**: Durante a execução do script:
- Digite sua senha quando solicitado (Linux/macOS)
- Aguarde a instalação do Docker (pode demorar alguns minutos)
- **REINICIE O TERMINAL** após a conclusão para aplicar permissões do Docker (Linux)

### Passo 3: Verificação da Instalação
```bash
# Verificar se o usuário está no grupo docker
groups | grep docker

# Se não aparecer "docker", reinicie o terminal e tente novamente

# Ativar ambiente virtual
source venv/bin/activate

# Verificar instalação das dependências
pip list | grep -E -i "(flask|werkzeug|pika|kafka-python|requests|matplotlib|seaborn|pandas|numpy|scipy|black|isort|flake8|pytest)"
```

### Passo 4: Inicialização da Infraestrutura
```bash
# Iniciar todos os serviços
docker compose up -d

# Aguardar inicialização (30-60 segundos)
sleep 60

# Verificar status dos containers
docker compose ps
```

**Resultado esperado**: Todos os containers devem estar com status "Up"

---

## ⚙️ Configuração do Ambiente

### Verificação dos Serviços

#### 1. RabbitMQ Cluster (3 nós)
```bash
# Verificar cluster RabbitMQ
docker exec rabbitmq-1 rabbitmqctl cluster_status

# Verificar filas
docker exec rabbitmq-1 rabbitmqctl list_queues

# Acessar interface web
echo "RabbitMQ Management: http://localhost:15672"
echo "Usuário: user | Senha: password"
```

#### 2. Apache Kafka
```bash
# Verificar tópicos Kafka
docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Verificar brokers
docker exec kafka kafka-broker-api-versions.sh --bootstrap-server localhost:9092

# Acessar interface web
echo "Kafdrop: http://localhost:9000"
```

#### 3. Teste de Conectividade
```bash
# Testar RabbitMQ
curl -u user:password http://localhost:15672/api/overview

# Testar Kafka (via Kafdrop)
curl -s http://localhost:9000 | grep -i kafdrop

# Testar baseline HTTP (será iniciado nos testes)
```

---

## 🧪 Execução de Todos os Testes

### 📋 Parâmetros de Entrada (Obrigatórios)

Para garantir medições assertivas, o sistema utiliza parâmetros específicos passados via linha de comando:

#### **a) Número de Mensagens (`--count`)**
- **Valores válidos**: `5`, `10`, `15`, `100`, `1000`, `10000`, `100000`
- **Descrição**: Quantidade total de mensagens a serem enviadas e processadas

#### **b) Número de Produtores (`--producers`)**
- **Valores válidos**: `1`, `4`, `16`, `64`
- **Descrição**: Número de clientes/produtores simultâneos enviando mensagens

#### **c) Número de Consumidores (`--consumers`)**
- **Valores válidos**: `4`, `64`
- **Descrição**: Número de consumidores processando mensagens da fila

#### **d) Sistema (`--system`)**
- **Valores válidos**: `rabbitmq`, `kafka`, `baseline`
- **Descrição**: Sistema de mensageria a ser testado

#### **Parâmetros Opcionais**
- `--size`: Tamanho de cada mensagem em bytes (padrão: 200)
- `--rps`: Rate Limiting - mensagens por segundo (opcional)

### 📊 Métricas de Saída Coletadas

O sistema coleta e exibe as seguintes métricas:

#### **i) T (Tempo de Permanência na Fila)**
- **Definição**: Latência média de uma mensagem desde o envio até o processamento
- **Unidade**: Segundos (com precisão de microssegundos)
- **Arquivo**: `logs/<system>/<run_id>/*_latency.csv`

#### **ii) V (Throughput / Vazão)**
- **Definição**: Número de mensagens processadas por unidade de tempo
- **Unidade**: Mensagens por segundo
- **Cálculo**: `V = mensagens_processadas / duração_total`

> 💡 **Importante:** Cada execução gera um identificador exclusivo `run_id`
> (por exemplo, `kafka-1732070501-a1b2c3`) e salva todos os arquivos dessa
> execução em `logs/<system>/<run_id>/`. O arquivo consolidado
> `benchmark_results.csv` continua em `logs/<system>/`.

### 📝 Exemplos de Uso

#### **Exemplo 1: Teste Comparativo Justo - Porte Pequeno (100 RPS)**
```bash
# Testar os 3 sistemas com MESMOS parâmetros para comparação justa
python main.py --server --port 5000 &
sleep 3
python main.py --count 100 --producers 1 --consumers 4 --system baseline --rps 100
pkill -f "python main.py --server"

python main.py --count 100 --producers 1 --consumers 4 --system rabbitmq --rps 100
python main.py --count 100 --producers 1 --consumers 4 --system kafka --rps 100
```

#### **Exemplo 2: Teste Comparativo Justo - Porte Médio (1.000 RPS)**
```bash
# Testar os 3 sistemas com MESMOS parâmetros
python main.py --server --port 5000 &
sleep 3
python main.py --count 1000 --producers 4 --consumers 4 --system baseline --rps 1000
pkill -f "python main.py --server"

python main.py --count 1000 --producers 4 --consumers 4 --system rabbitmq --rps 1000
python main.py --count 1000 --producers 4 --consumers 4 --system kafka --rps 1000
```

#### **Exemplo 3: Teste Comparativo Justo - Porte Grande (10.000 RPS)**
```bash
# Testar os 3 sistemas com MESMOS parâmetros
python main.py --server --port 5000 &
sleep 3
python main.py --count 10000 --producers 16 --consumers 64 --system baseline --rps 10000
pkill -f "python main.py --server"

python main.py --count 10000 --producers 16 --consumers 64 --system rabbitmq --rps 10000
python main.py --count 10000 --producers 16 --consumers 64 --system kafka --rps 10000
```

#### **Exemplo 4: Teste de Chaos Engineering**
```bash
python main.py --chaos --count 5 --size 100 --system rabbitmq
```

#### **Exemplo 5: Gerar Gráficos Comparativos**
```bash
python generate_plots.py --system all
```

### ⚠️ Preparação Importante

**ANTES de executar qualquer teste, execute estes comandos:**

```bash
# 1. Ativar ambiente virtual
source venv/bin/activate

# 2. Verificar se containers estão rodando
docker compose ps

# 3. Se não estiverem, iniciar
docker compose up -d
sleep 60

# 4. Limpar logs antigos (IMPORTANTE!)
./scripts/clear_logs.sh

# 5. Verificar conectividade
echo "Testando RabbitMQ..."
curl -u user:password http://localhost:15672/api/overview | head -1

echo "Testando Kafka..."
curl -s http://localhost:9000 | grep -i kafdrop | head -1
```

### 🎯 Metodologia de Comparação Justa

**IMPORTANTE**: Para uma comparação científica válida, os três sistemas (Baseline, RabbitMQ, Kafka) são testados com **EXATAMENTE OS MESMOS PARÂMETROS** em cada porte. Isso garante que as diferenças de performance sejam atribuídas às tecnologias, não a configurações diferentes.

#### Portes Definidos

| Porte | RPS | Mensagens | Produtores | Consumidores | Caracterização |
|-------|-----|-----------|------------|--------------|----------------|
| **Pequeno** | 100 | 100 | 1 | 4 | Aplicações corporativas internas, MVPs |
| **Médio** | 1.000 | 1.000 | 4 | 4 | Plataformas de comércio eletrônico estabelecidas |
| **Grande** | 10.000 | 10.000 | 16 | 64 | Serviços globais, redes sociais, mercados financeiros |

**Proporção geométrica**: 1:10:100 (fundamentada em Jain, 1991)

### Estrutura dos Testes

O sistema executa **testes comparativos justos por porte** e **testes adicionais de recursos**:

#### **Testes Comparativos por Porte (Comparação Justa)**
1. **Porte Pequeno (100 RPS)**: Baseline, RabbitMQ, Kafka com mesmos parâmetros
2. **Porte Médio (1.000 RPS)**: Baseline, RabbitMQ, Kafka com mesmos parâmetros
3. **Porte Grande (10.000 RPS)**: Baseline, RabbitMQ, Kafka com mesmos parâmetros

#### **Testes Adicionais de Recursos**
4. **Chaos Engineering**: Tolerância a falhas
5. **Rate Limiting**: Validação de controle de taxa
6. **Monitoramento**: Coleta de métricas de recursos
7. **Visualização**: Geração de gráficos comparativos

### Execução de Testes Comparativos Justos

#### **TESTE COMPARATIVO: Porte Pequeno (100 RPS)**

**Parâmetros idênticos para os 3 sistemas**: 100 mensagens, 1 produtor, 4 consumidores, RPS=100

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Baseline - Pequeno Porte
python main.py --server --port 5000 &
sleep 3
python main.py --count 100 --producers 1 --consumers 4 --system baseline --rps 100
pkill -f "python main.py --server"

# RabbitMQ - Pequeno Porte (MESMOS PARÂMETROS)
python main.py --count 100 --producers 1 --consumers 4 --system rabbitmq --rps 100

# Kafka - Pequeno Porte (MESMOS PARÂMETROS)
python main.py --count 100 --producers 1 --consumers 4 --system kafka --rps 100
```

**✅ Critério de Sucesso**: Comparação justa com mesmos parâmetros permite identificar qual tecnologia tem melhor performance.

#### **TESTE COMPARATIVO: Porte Médio (1.000 RPS)**

**Parâmetros idênticos para os 3 sistemas**: 1.000 mensagens, 4 produtores, 4 consumidores, RPS=1000

```bash
# Baseline - Médio Porte
python main.py --server --port 5000 &
sleep 3
python main.py --count 1000 --producers 4 --consumers 4 --system baseline --rps 1000
pkill -f "python main.py --server"

# RabbitMQ - Médio Porte (MESMOS PARÂMETROS)
python main.py --count 1000 --producers 4 --consumers 4 --system rabbitmq --rps 1000

# Kafka - Médio Porte (MESMOS PARÂMETROS)
python main.py --count 1000 --producers 4 --consumers 4 --system kafka --rps 1000
```

#### **TESTE COMPARATIVO: Porte Grande (10.000 RPS)**

**Parâmetros idênticos para os 3 sistemas**: 10.000 mensagens, 16 produtores, 64 consumidores, RPS=10000

```bash
# Baseline - Grande Porte
python main.py --server --port 5000 &
sleep 3
python main.py --count 10000 --producers 16 --consumers 64 --system baseline --rps 10000
pkill -f "python main.py --server"

# RabbitMQ - Grande Porte (MESMOS PARÂMETROS)
python main.py --count 10000 --producers 16 --consumers 64 --system rabbitmq --rps 10000

# Kafka - Grande Porte (MESMOS PARÂMETROS)
python main.py --count 10000 --producers 16 --consumers 64 --system kafka --rps 10000
```

**✅ Critério de Sucesso**: Comparação justa permite identificar qual tecnologia escala melhor em alta carga.

#### **TESTE ADICIONAL: Chaos Engineering (Tolerância a Falhas)**

```bash
# Teste Chaos Engineering - RabbitMQ
echo "=== TESTE: Chaos Engineering - RabbitMQ ==="
python main.py --chaos --count 5 --size 100 --system rabbitmq

# Aguardar recuperação
sleep 30

# Teste Chaos Engineering - Kafka
echo "=== TESTE: Chaos Engineering - Kafka ==="
python main.py --chaos --count 5 --size 100 --system kafka

# Aguardar recuperação
sleep 30
```

**✅ Critério de Sucesso**: Sistema deve se recuperar automaticamente após falhas.

#### **TESTE ADICIONAL: Geração de Gráficos Comparativos**

```bash
# Gerar todos os gráficos comparativos
echo "=== TESTE: Geração de Gráficos ==="
python generate_plots.py --system all
```

**✅ Critério de Sucesso**: Gráficos devem ser gerados em `logs/plots/` com comparações visuais entre os sistemas.

### Script de Execução Automática - Testes Comparativos Justos

Para executar todos os testes comparativos justos automaticamente:

```bash
# Executar script de testes comparativos por porte
./test_comparativo_justo_por_porte.sh
```

Este script executa:
1. **Porte Pequeno (100 RPS)**: Baseline, RabbitMQ, Kafka com mesmos parâmetros
2. **Porte Médio (1.000 RPS)**: Baseline, RabbitMQ, Kafka com mesmos parâmetros
3. **Porte Grande (10.000 RPS)**: Baseline, RabbitMQ, Kafka com mesmos parâmetros
4. **Chaos Engineering**: Testes de tolerância a falhas
5. **Geração de Gráficos**: Gráficos comparativos automáticos

**✅ Vantagem**: Comparação científica justa com mesmos parâmetros permite identificar qual tecnologia tem melhor performance em cada porte.

---

## 📊 Análise e Visualização dos Resultados

### Estrutura dos Logs Gerados

```
logs/
├── baseline/
│   ├── benchmark_results.csv          # Resultados consolidados
│   └── <run_id>/
│       ├── [timestamp]_send_times.json    # Timestamps de envio
│       ├── [timestamp]_latency.csv        # Medições de latência
│       └── [timestamp]_summary.csv        # Resumo estatístico
├── kafka/
│   ├── benchmark_results.csv          # Resultados consolidados
│   └── <run_id>/
│       ├── [timestamp]_send_times.json    # Timestamps de envio
│       ├── [timestamp]_latency.csv        # Medições de latência
│       ├── [timestamp]_summary.csv        # Resumo estatístico
│       └── resource_monitoring.csv        # Monitoramento de recursos
└── rabbitmq/
    ├── benchmark_results.csv          # Resultados consolidados
    └── <run_id>/
        ├── [timestamp]_send_times.json    # Timestamps de envio
        ├── [timestamp]_latency.csv        # Medições de latência
        ├── [timestamp]_summary.csv        # Resumo estatístico
        └── resource_monitoring.csv        # Monitoramento de recursos
```

### Análise dos Resultados

#### 1. Visualização dos Resultados Consolidados
```bash
# Ver resultados consolidados de cada broker
# O arquivo benchmark_results.csv contém todas as execuções com as métricas T e V
echo "=== RESULTADOS BASELINE ==="
echo "Colunas: timestamp, tech, messages, message_size, num_producers, num_consumers, rps, latency_avg (T), latency_50, latency_95, latency_99, throughput (V), successful_producers, successful_consumers"
cat logs/baseline/benchmark_results.csv

echo "=== RESULTADOS RABBITMQ ==="
cat logs/rabbitmq/benchmark_results.csv

echo "=== RESULTADOS KAFKA ==="
cat logs/kafka/benchmark_results.csv
```

#### 2. Análise de Latência (T - Tempo de Permanência na Fila)
```bash
# Analisar latências mais recentes
# Cada arquivo contém: msg_id, latency_seconds (T)
echo "=== LATÊNCIAS BASELINE (T) ==="
ls -la logs/baseline/*latency.csv | tail -1 | xargs cat | head -20

echo "=== LATÊNCIAS RABBITMQ (T) ==="
ls -la logs/rabbitmq/*latency.csv | tail -1 | xargs cat | head -20

echo "=== LATÊNCIAS KAFKA (T) ==="
ls -la logs/kafka/*latency.csv | tail -1 | xargs cat | head -20

# Calcular estatísticas de latência
echo "=== ESTATÍSTICAS DE LATÊNCIA ==="
for system in baseline rabbitmq kafka; do
    echo "--- $system ---"
    latest=$(ls -la logs/$system/*latency.csv 2>/dev/null | tail -1 | awk '{print $NF}')
    if [ -n "$latest" ]; then
        awk -F',' 'NR>1 {sum+=$2; count++; if(count==1 || $2<min) min=$2; if($2>max) max=$2} END {if(count>0) print "Média (T): " sum/count "s | Min: " min "s | Max: " max "s | Total: " count}' "$latest"
    fi
done
```

#### 3. Análise de Throughput (V - Vazão)
```bash
# Extrair throughput dos summaries e dos resultados consolidados
# V (Throughput) = mensagens por segundo
echo "=== THROUGHPUT BASELINE (V) ==="
ls -la logs/baseline/*summary.csv | tail -1 | xargs grep "throughput_msgs_per_sec"

echo "=== THROUGHPUT RABBITMQ (V) ==="
ls -la logs/rabbitmq/*summary.csv | tail -1 | xargs grep "throughput_msgs_per_sec"

echo "=== THROUGHPUT KAFKA (V) ==="
ls -la logs/kafka/*summary.csv | tail -1 | xargs grep "throughput_msgs_per_sec"

# Extrair throughput dos resultados consolidados (última linha)
echo "=== THROUGHPUT DOS RESULTADOS CONSOLIDADOS ==="
for system in baseline rabbitmq kafka; do
    echo "--- $system ---"
    if [ -f "logs/$system/benchmark_results.csv" ]; then
        tail -1 "logs/$system/benchmark_results.csv" | awk -F',' '{print "Throughput (V): " $12 " mensagens/segundo"}'
    fi
done
```

#### 4. Monitoramento de Recursos
```bash
# Verificar monitoramento de recursos
echo "=== RECURSOS RABBITMQ ==="
ls -la logs/rabbitmq/*resource_monitoring.csv | tail -1 | xargs head -10

echo "=== RECURSOS KAFKA ==="
ls -la logs/kafka/*resource_monitoring.csv | tail -1 | xargs head -10
```

### Visualização Gráfica Automática

O sistema gera **automaticamente gráficos comparativos** após cada execução de benchmark. Os gráficos são salvos em `logs/plots/`.

#### Geração Automática

Os gráficos são gerados **automaticamente** após cada execução de benchmark. Não é necessário executar comandos adicionais.

#### Geração Manual de Gráficos

Para gerar gráficos manualmente ou atualizar gráficos existentes:

```bash
# Gerar todos os gráficos disponíveis
python generate_plots.py --system all

# Gerar gráficos de um sistema específico
python generate_plots.py --system rabbitmq
python generate_plots.py --system kafka
python generate_plots.py --system baseline

# Gerar gráficos de uma execução específica
python generate_plots.py --system rabbitmq --run-id rabbitmq-1763656609-ee18d8
```

#### Tipos de Gráficos Gerados

1. **Comparação de Latência**: Compara latência média (T) entre sistemas
2. **Comparação de Throughput**: Compara throughput (V) entre sistemas
3. **Resumo Comparativo**: Gráfico completo com múltiplas métricas (T, V, percentis)
4. **Distribuição de Latências**: Histograma de latências por sistema

**Localização**: Todos os gráficos são salvos em `logs/plots/`

**Dependências**: As bibliotecas de visualização (matplotlib==3.10.7, seaborn==0.13.2, pandas==2.3.3, numpy==2.3.5, scipy==1.16.3) já estão incluídas no `requirements.txt` e são instaladas automaticamente.

---

## 📈 Interpretação dos Resultados

### Métricas Principais

#### 1. **T (Tempo de Permanência na Fila) - Latência**
- **Definição**: Tempo médio que uma mensagem permanece na fila desde o envio até o processamento
- **Unidade**: Segundos (com precisão de microssegundos)
- **Valores Esperados**:
  - **Baseline HTTP**: 0.001-0.010s
  - **RabbitMQ**: 0.001-0.005s
  - **Apache Kafka**: 0.001-0.003s
- **Arquivo**: `logs/<system>/<run_id>/*_latency.csv` (coluna `latency_seconds`)

#### 2. **V (Throughput / Vazão)**
- **Definição**: Número de mensagens processadas por unidade de tempo
- **Unidade**: Mensagens por segundo
- **Cálculo**: `V = mensagens_processadas / duração_total`
- **Valores Esperados**:
  - **Baseline HTTP**: 50-200 msgs/s
  - **RabbitMQ**: 1,000-5,000 msgs/s
  - **Apache Kafka**: 5,000-20,000 msgs/s
- **Arquivo**: `logs/<system>/*_summary.csv` (métrica `throughput_msgs_per_sec`) e `benchmark_results.csv` (coluna `throughput`)

#### 3. **Taxa de Sucesso (%)**
- **Todos os brokers**: Esperado 95-100%

#### 4. **Uso de Recursos**
- **CPU**: Varia conforme carga
- **Memória**: RabbitMQ ~200MB, Kafka ~300MB

### Análise Comparativa

#### Cenário 1: Teste Comparativo Justo - Porte Pequeno (100 RPS)
```bash
# Executar teste comparativo justo (MESMOS parâmetros para os 3 sistemas)
python main.py --server --port 5000 &
sleep 3
python main.py --count 100 --producers 1 --consumers 4 --system baseline --rps 100
pkill -f "python main.py --server"

python main.py --count 100 --producers 1 --consumers 4 --system rabbitmq --rps 100
python main.py --count 100 --producers 1 --consumers 4 --system kafka --rps 100

# Analisar resultados
echo "=== COMPARAÇÃO JUSTA - PORTE PEQUENO (100 RPS) ==="
echo "Baseline - T (Latência): $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f12) msgs/s"
echo "RabbitMQ - T (Latência): $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f12) msgs/s"
echo "Kafka    - T (Latência): $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f12) msgs/s"
```

#### Cenário 2: Teste Comparativo Justo - Porte Médio (1.000 RPS)
```bash
# Executar teste comparativo justo (MESMOS parâmetros para os 3 sistemas)
python main.py --server --port 5000 &
sleep 3
python main.py --count 1000 --producers 4 --consumers 4 --system baseline --rps 1000
pkill -f "python main.py --server"

python main.py --count 1000 --producers 4 --consumers 4 --system rabbitmq --rps 1000
python main.py --count 1000 --producers 4 --consumers 4 --system kafka --rps 1000

# Analisar resultados
echo "=== COMPARAÇÃO JUSTA - PORTE MÉDIO (1.000 RPS) ==="
echo "Baseline - T (Latência): $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f12) msgs/s"
echo "RabbitMQ - T (Latência): $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f12) msgs/s"
echo "Kafka    - T (Latência): $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f12) msgs/s"
```

#### Cenário 3: Teste Comparativo Justo - Porte Grande (10.000 RPS)
```bash
# Executar teste comparativo justo (MESMOS parâmetros para os 3 sistemas)
python main.py --server --port 5000 &
sleep 3
python main.py --count 10000 --producers 16 --consumers 64 --system baseline --rps 10000
pkill -f "python main.py --server"

python main.py --count 10000 --producers 16 --consumers 64 --system rabbitmq --rps 10000
python main.py --count 10000 --producers 16 --consumers 64 --system kafka --rps 10000

# Analisar resultados
echo "=== COMPARAÇÃO JUSTA - PORTE GRANDE (10.000 RPS) ==="
echo "Baseline - T (Latência): $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f12) msgs/s"
echo "RabbitMQ - T (Latência): $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f12) msgs/s"
echo "Kafka    - T (Latência): $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f8) segundos | V (Throughput): $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f12) msgs/s"
```

### Relatório de Análise

#### Gerar Relatório Automático
```bash
# Criar script de relatório
cat > gerar_relatorio.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
import glob
import os
from datetime import datetime

def gerar_relatorio():
    """Gerar relatório completo dos resultados"""
    
    print("📊 RELATÓRIO DE ANÁLISE DE PERFORMANCE")
    print("=" * 50)
    print(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Analisar cada broker
    brokers = ['baseline', 'rabbitmq', 'kafka']
    
    for broker in brokers:
        print(f"🔍 ANÁLISE DO {broker.upper()}")
        print("-" * 30)
        
        # Carregar dados
        try:
            data = pd.read_csv(f'logs/{broker}/benchmark_results.csv')
            
            # Estatísticas básicas
            print(f"Total de testes: {len(data)}")
            print(f"V (Throughput médio): {data['throughput'].mean():.2f} mensagens/segundo")
            print(f"T (Latência média): {data['latency_avg'].mean():.6f} segundos")
            print(f"Throughput máximo (V): {data['throughput'].max():.2f} msgs/s")
            print(f"Throughput mínimo (V): {data['throughput'].min():.2f} msgs/s")
            print(f"Latência mínima (T): {data['latency_avg'].min():.6f}s")
            print(f"Latência máxima (T): {data['latency_avg'].max():.6f}s")
            
        except FileNotFoundError:
            print(f"❌ Dados não encontrados para {broker}")
        
        print()
    
    # Comparação entre brokers
    print("📈 COMPARAÇÃO ENTRE BROKERS")
    print("-" * 30)
    
    try:
        baseline_data = pd.read_csv('logs/baseline/benchmark_results.csv')
        rabbitmq_data = pd.read_csv('logs/rabbitmq/benchmark_results.csv')
        kafka_data = pd.read_csv('logs/kafka/benchmark_results.csv')
        
        print(f"Baseline - V (Throughput médio): {baseline_data['throughput'].mean():.2f} mensagens/segundo")
        print(f"Baseline - T (Latência média): {baseline_data['latency_avg'].mean():.6f} segundos")
        print(f"RabbitMQ - V (Throughput médio): {rabbitmq_data['throughput'].mean():.2f} mensagens/segundo")
        print(f"RabbitMQ - T (Latência média): {rabbitmq_data['latency_avg'].mean():.6f} segundos")
        print(f"Kafka    - V (Throughput médio): {kafka_data['throughput'].mean():.2f} mensagens/segundo")
        print(f"Kafka    - T (Latência média): {kafka_data['latency_avg'].mean():.6f} segundos")
        
        print()
        print("🏆 RANKING DE PERFORMANCE - THROUGHPUT (V):")
        throughputs = {
            'Baseline': baseline_data['throughput'].mean(),
            'RabbitMQ': rabbitmq_data['throughput'].mean(),
            'Kafka': kafka_data['throughput'].mean()
        }
        
        ranking = sorted(throughputs.items(), key=lambda x: x[1], reverse=True)
        for i, (broker, throughput) in enumerate(ranking, 1):
            print(f"{i}º lugar: {broker} - {throughput:.2f} mensagens/segundo")
        
        print()
        print("🏆 RANKING DE PERFORMANCE - LATÊNCIA (T) - Menor é melhor:")
        latencies = {
            'Baseline': baseline_data['latency_avg'].mean(),
            'RabbitMQ': rabbitmq_data['latency_avg'].mean(),
            'Kafka': kafka_data['latency_avg'].mean()
        }
        
        ranking_lat = sorted(latencies.items(), key=lambda x: x[1])
        for i, (broker, latency) in enumerate(ranking_lat, 1):
            print(f"{i}º lugar: {broker} - {latency:.6f} segundos")
            
    except FileNotFoundError as e:
        print(f"❌ Erro ao carregar dados: {e}")
    
    print()
    print("✅ Relatório gerado com sucesso!")

if __name__ == "__main__":
    gerar_relatorio()
EOF

# Executar relatório
python gerar_relatorio.py
```

---

## 🔧 Solução de Problemas

### Problemas Comuns e Soluções

#### 1. **Erro: "Permission denied" no Docker**
```bash
# Verificar se usuário está no grupo docker
groups | grep docker

# Se não estiver, adicionar usuário ao grupo
sudo usermod -aG docker $USER

# REINICIAR O TERMINAL e tentar novamente
```

#### 2. **Erro: "Connection refused" nos brokers**
```bash
# Verificar se containers estão rodando
docker compose ps

# Se não estiverem, reiniciar
docker compose down
docker compose up -d

# Aguardar inicialização
sleep 60

# Verificar logs
docker compose logs
```

#### 3. **Erro: "No module named 'pika'" ou similar**
```bash
# Verificar se ambiente virtual está ativo
which python

# Se não estiver, ativar
source venv/bin/activate

# Reinstalar dependências
pip install -r requirements.txt
```

#### 4. **Erro: "Port already in use"**
```bash
# Verificar portas em uso
sudo netstat -tlnp | grep -E ":(5672|9092|15672|9000)"

# Parar serviços conflitantes
sudo systemctl stop rabbitmq-server
sudo systemctl stop kafka

# Ou usar portas diferentes no docker-compose.yml
```

#### 5. **Erro: "Container failed to start"**
```bash
# Verificar logs do container
docker compose logs [nome-do-container]

# Verificar recursos do sistema
free -h
df -h

# Limpar containers antigos
docker system prune -a
```

#### 6. **Erro: "RabbitMQ cluster not working"**
```bash
# Verificar status do cluster
docker exec rabbitmq-1 rabbitmqctl cluster_status

# Reinicializar cluster
docker compose restart rabbitmq-1 rabbitmq-2 rabbitmq-3

# Aguardar e verificar novamente
sleep 30
docker exec rabbitmq-1 rabbitmqctl cluster_status
```

#### 7. **Erro: "Kafka topics not created"**
```bash
# Verificar se Kafka está funcionando
docker exec kafka kafka-topics.sh --list --bootstrap-server localhost:9092

# Criar tópico manualmente se necessário
docker exec kafka kafka-topics.sh --create --topic bcc-tcc --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1
```

#### 8. **Erro: "Baseline server not responding"**
```bash
# Verificar se servidor está rodando
ps aux | grep "python main.py --server"

# Se não estiver, iniciar manualmente
python main.py --server --port 5000 &

# Testar conectividade
curl -X POST http://localhost:5000/notify -H "Content-Type: application/json" -d '{"message": "test"}'
```

#### 9. **Erro: "Arquivo de tempos de envio não encontrado"**
```bash
# Limpar logs antigos que podem estar causando confusão
./scripts/clear_logs.sh

# Executar teste novamente
python main.py --count 5 --size 100 --system rabbitmq
```

#### 10. **Erro: "Mensagem recebida sem timestamp correspondente"**
```bash
# Este erro indica que o consumidor está lendo mensagens antigas
# Limpar logs e executar teste limpo
./scripts/clear_logs.sh
python main.py --count 5 --size 100 --system kafka
```

### Logs de Debug

#### Verificar Logs da Aplicação
```bash
# Logs gerais
tail -f logs/application.log

# Logs específicos de cada broker
tail -f logs/baseline/benchmark_results.csv
tail -f logs/rabbitmq/benchmark_results.csv
tail -f logs/kafka/benchmark_results.csv
```

#### Verificar Logs do Docker
```bash
# Logs de todos os containers
docker compose logs -f

# Logs de um container específico
docker compose logs -f rabbitmq-1
docker compose logs -f kafka
```

### Reset Completo do Ambiente

Se nada funcionar, execute um reset completo:

```bash
# Parar tudo
docker compose down -v
deactivate

# Remover ambiente virtual
rm -rf venv

# Limpar Docker
docker system prune -a

# Reconfigurar tudo
./scripts/setup_dev_environment.sh
source venv/bin/activate
docker compose up -d
```

---

## 📚 Documentação Técnica

### Arquitetura do Sistema

#### Componentes Principais
1. **Orquestrador**: `main.py` - Ponto de entrada único
2. **Brokers**: Implementações modulares em `src/brokers/`
3. **Core**: Configurações e utilitários em `src/core/`
4. **Orquestração**: Lógica de testes em `src/orchestration/`

#### Fluxo de Execução
```
main.py → BenchmarkOrchestrator → Broker Classes → Metrics Collection → Logs
```

### Configurações Técnicas

#### RabbitMQ
- **Versão**: 4.1.1 (imagem: `rabbitmq:4.1.1-management`)
- **Cluster**: 3 nós com Quorum Queues
- **Portas**: 5672 (AMQP), 15672 (Management)
- **Configurações**: Confirmação de entrega, mensagens persistentes

#### Apache Kafka
- **Versão**: 4.0.0 (imagem Docker: `apache/kafka:4.0.0`)
- **Modo**: KRaft (sem Zookeeper)
- **Queue Mode**: Simulação de KIP-932
- **Portas**: 9092 (Broker), 9000 (Kafdrop)
- **Nota**: A imagem oficial do Apache Kafka 4.0.0 é usada com configuração KRaft personalizada. O arquivo de configuração está em `config/kraft-server.properties`.

#### Baseline HTTP
- **Framework**: Flask 3.1.1
- **Porta**: 5000 (configurável via `--port`)
- **Processamento**: 1ms simulado por requisição

### Recursos da Aplicação

#### 1. **Benchmark Comparativo Justo**
- Testes comparativos com mesmos parâmetros para cada porte
- Comparação científica válida entre Baseline, RabbitMQ e Kafka
- Script automatizado: `test_comparativo_justo_por_porte.sh`

#### 2. **Geração Automática de Gráficos**
- Gráficos comparativos gerados automaticamente após cada benchmark
- Script manual: `python generate_plots.py --system all`
- Tipos de gráficos:
  - Comparação de Latência
  - Comparação de Throughput
  - Resumo Comparativo
  - Distribuição de Latências

#### 3. **Chaos Engineering**
- Testes de tolerância a falhas
- Simulação de falhas e recuperação automática
- Comando: `python main.py --chaos --count 5 --size 100 --system rabbitmq`
- **Nota**: Para chaos engineering, os parâmetros `--producers` e `--consumers` são opcionais (padrão: 1 produtor, 4 consumidores)

#### 4. **Rate Limiting (RPS)**
- Controle de taxa de mensagens por segundo
- Parâmetro: `--rps <valor>`
- Validação de throughput controlado

#### 5. **Monitoramento de Recursos**
- Coleta automática de CPU e memória
- Arquivos de monitoramento em `logs/<system>/`

#### 6. **Métricas Precisas**
- Latência (T) com precisão de microssegundos
- Throughput (V) em mensagens por segundo
- Percentis: P50, P95, P99
- Arquivos CSV e JSON para análise posterior

### Métricas Coletadas

#### Latência
- **T1**: Timestamp após confirmação do broker
- **T2**: Timestamp após processamento
- **Latência**: T2 - T1

#### Throughput
- **Cálculo**: Mensagens processadas / Tempo total
- **Unidade**: Mensagens por segundo

#### Recursos
- **CPU**: Percentual de uso
- **Memória**: Uso em MB
- **Coleta**: A cada 5 segundos durante testes

### Validação Científica

#### Reprodutibilidade
- **Ambiente**: Docker containerizado
- **Versões**: Fixas e documentadas
- **Configurações**: Padronizadas e versionadas

#### Métricas
- **Precisão**: Timestamps com precisão de microssegundos
- **Consistência**: Mesmo ambiente para todos os testes
- **Comparabilidade**: Mesmas condições para todos os brokers

---

## 🎯 Conclusão

Este sistema de benchmark foi desenvolvido seguindo rigorosos padrões acadêmicos para garantir:

1. **Reprodutibilidade**: Qualquer pesquisador pode replicar os resultados
2. **Precisão**: Métricas coletadas com alta precisão
3. **Completude**: Todos os aspectos relevantes são testados
4. **Documentação**: Processo completamente documentado

### Contato e Suporte

Para dúvidas sobre a implementação ou análise dos resultados:
- **E-mail**: leonardosfiamoncini@gmail.com