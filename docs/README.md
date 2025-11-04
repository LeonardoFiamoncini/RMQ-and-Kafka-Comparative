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

### Tecnologias Implementadas
- **RabbitMQ 4.1.1** (imagem: `rabbitmq:4.1.1-management`): Com Quorum Queues e cluster de 3 nós
- **Apache Kafka 4.0** (imagem: `bitnami/kafka:3.6`): Com KRaft mode e Queue Mode (KIP-932)
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
pip list | grep -E -i "(flask|pika|kafka-python|requests|black|isort|flake8)"
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

### Estrutura dos Testes

O sistema executa **8 categorias principais de testes**, cada uma validando aspectos específicos da aplicação:

1. **Testes Básicos de Funcionalidade**
2. **Testes de Rate Limiting (RPS)**
3. **Testes de Múltiplos Clientes**
4. **Testes de Chaos Engineering**
5. **Testes de Monitoramento**
6. **Testes Integrados**
7. **Testes de Baseline HTTP**
8. **Testes de Performance Comparativa**

### Execução Sequencial de Todos os Testes

#### **TESTE 1: Validação Básica dos Brokers**

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Teste 1.1: Baseline HTTP (com servidor)
echo "=== TESTE 1.1: Baseline HTTP ==="
# Iniciar servidor em background
python main.py --server --port 5000 &
sleep 3
# Executar teste
python main.py --count 10 --size 200 --only baseline
# Parar servidor
pkill -f "python main.py --server"

# Teste 1.2: RabbitMQ
echo "=== TESTE 1.2: RabbitMQ ==="
python main.py --count 8 --size 150 --only rabbitmq

# Teste 1.3: Kafka
echo "=== TESTE 1.3: Kafka ==="
python main.py --count 8 --size 150 --only kafka
```

**✅ Critério de Sucesso**: Todos os testes devem mostrar "✅ Benchmark finalizado" sem erros.

#### **TESTE 2: Rate Limiting (RPS)**

```bash
# Teste 2.1: Baseline com RPS
echo "=== TESTE 2.1: Baseline com Rate Limiting ==="
python main.py --count 8 --size 100 --rps 3 --only baseline

# Teste 2.2: RabbitMQ com RPS
echo "=== TESTE 2.2: RabbitMQ com Rate Limiting ==="
python main.py --count 6 --size 100 --rps 2 --only rabbitmq

# Teste 2.3: Kafka com RPS
echo "=== TESTE 2.3: Kafka com Rate Limiting ==="
python main.py --count 6 --size 100 --rps 2 --only kafka
```

**✅ Critério de Sucesso**: Throughput deve estar próximo ao RPS especificado.

#### **TESTE 3: Múltiplos Clientes Concorrentes**

```bash
# Teste 3.1: Baseline com múltiplos clientes
echo "=== TESTE 3.1: Baseline - Múltiplos Clientes ==="
python main.py --count 12 --size 100 --producers 3 --consumers 2 --only baseline

# Teste 3.2: RabbitMQ com múltiplos clientes
echo "=== TESTE 3.2: RabbitMQ - Múltiplos Clientes ==="
python main.py --count 8 --size 100 --producers 2 --consumers 2 --only rabbitmq

# Teste 3.3: Kafka com múltiplos clientes
echo "=== TESTE 3.3: Kafka - Múltiplos Clientes ==="
python main.py --count 8 --size 100 --producers 2 --consumers 2 --only kafka
```

**✅ Critério de Sucesso**: Throughput deve aumentar proporcionalmente ao número de clientes.

#### **TESTE 4: Chaos Engineering (Tolerância a Falhas)**

```bash
# Teste 4.1: Chaos Engineering - RabbitMQ
echo "=== TESTE 4.1: Chaos Engineering - RabbitMQ ==="
python main.py --chaos --count 5 --size 100 --only rabbitmq

# Aguardar recuperação
sleep 30

# Teste 4.2: Chaos Engineering - Kafka
echo "=== TESTE 4.2: Chaos Engineering - Kafka ==="
python main.py --chaos --count 5 --size 100 --only kafka

# Aguardar recuperação
sleep 30
```

**✅ Critério de Sucesso**: Sistema deve se recuperar automaticamente após falhas.

#### **TESTE 5: Monitoramento de Recursos**

```bash
# Teste 5.1: Monitoramento - RabbitMQ
echo "=== TESTE 5.1: Monitoramento - RabbitMQ ==="
python main.py --count 5 --size 100 --only rabbitmq

# Teste 5.2: Monitoramento - Kafka
echo "=== TESTE 5.2: Monitoramento - Kafka ==="
python main.py --count 5 --size 100 --only kafka
```

**✅ Critério de Sucesso**: Arquivos de monitoramento devem ser gerados em `logs/`.

#### **TESTE 6: Benchmarks Integrados**

```bash
# Teste 6.1: Benchmark Completo (Todos os Brokers)
echo "=== TESTE 6.1: Benchmark Completo ==="
python main.py --count 10 --size 100

# Teste 6.2: Benchmark com Rate Limiting
echo "=== TESTE 6.2: Benchmark com Rate Limiting ==="
python main.py --count 20 --size 100 --rps 5

# Teste 6.3: Benchmark com Múltiplos Clientes
echo "=== TESTE 6.3: Benchmark com Múltiplos Clientes ==="
python main.py --count 30 --size 100 --producers 3 --consumers 2
```

**✅ Critério de Sucesso**: Todos os brokers devem ser testados em sequência.

#### **TESTE 7: Baseline HTTP Detalhado**

```bash
# Teste 7.1: Iniciar servidor baseline
echo "=== TESTE 7.1: Iniciando Servidor Baseline ==="
python main.py --server --port 5000 &

# Aguardar inicialização
sleep 5

# Teste 7.2: Testar cliente baseline
echo "=== TESTE 7.2: Testando Cliente Baseline ==="
python main.py --count 15 --size 100 --only baseline

# Parar servidor
pkill -f "python main.py --server"
```

**✅ Critério de Sucesso**: Servidor deve responder e processar requisições.

#### **TESTE 8: Performance Comparativa Extensiva**

```bash
# Teste 8.1: Performance com diferentes tamanhos de mensagem
echo "=== TESTE 8.1: Performance - Tamanhos Variados ==="
python main.py --count 50 --size 64 --only baseline
python main.py --count 50 --size 64 --only rabbitmq
python main.py --count 50 --size 64 --only kafka

python main.py --count 50 --size 1024 --only baseline
python main.py --count 50 --size 1024 --only rabbitmq
python main.py --count 50 --size 1024 --only kafka

python main.py --count 50 --size 4096 --only baseline
python main.py --count 50 --size 4096 --only rabbitmq
python main.py --count 50 --size 4096 --only kafka

# Teste 8.2: Performance com diferentes cargas
echo "=== TESTE 8.2: Performance - Cargas Variadas ==="
python main.py --count 100 --size 100 --only baseline
python main.py --count 100 --size 100 --only rabbitmq
python main.py --count 100 --size 100 --only kafka

python main.py --count 500 --size 100 --only baseline
python main.py --count 500 --size 100 --only rabbitmq
python main.py --count 500 --size 100 --only kafka
```

**✅ Critério de Sucesso**: Dados suficientes para análise estatística.

### Script de Execução Automática

Para executar todos os testes automaticamente:

```bash
# Criar script de execução completa
cat > executar_todos_testes.sh << 'EOF'
#!/bin/bash

echo "🎓 INICIANDO EXECUÇÃO COMPLETA DE TODOS OS TESTES"
echo "=================================================="

# Ativar ambiente virtual
source venv/bin/activate

# Limpar logs antigos para evitar confusão
echo "🧹 Limpando logs antigos..."
./scripts/clear_logs.sh

# Verificar se containers estão rodando
if ! docker compose ps | grep -q "Up"; then
    echo "❌ Containers não estão rodando. Iniciando..."
    docker compose up -d
    sleep 60
fi

# Executar todos os testes
echo "🧪 Executando Teste 1: Validação Básica"
# Baseline com servidor
python main.py --server --port 5000 &
sleep 3
python main.py --count 10 --size 200 --only baseline
pkill -f "python main.py --server"
# RabbitMQ e Kafka
python main.py --count 8 --size 150 --only rabbitmq
python main.py --count 8 --size 150 --only kafka

echo "🧪 Executando Teste 2: Rate Limiting"
python main.py --count 8 --size 100 --rps 3 --only baseline
python main.py --count 6 --size 100 --rps 2 --only rabbitmq
python main.py --count 6 --size 100 --rps 2 --only kafka

echo "🧪 Executando Teste 3: Múltiplos Clientes"
python main.py --count 12 --size 100 --producers 3 --consumers 2 --only baseline
python main.py --count 8 --size 100 --producers 2 --consumers 2 --only rabbitmq
python main.py --count 8 --size 100 --producers 2 --consumers 2 --only kafka

echo "🧪 Executando Teste 4: Chaos Engineering"
python main.py --chaos --count 5 --size 100 --only rabbitmq
sleep 30
python main.py --chaos --count 5 --size 100 --only kafka
sleep 30

echo "🧪 Executando Teste 5: Monitoramento"
python main.py --count 5 --size 100 --only rabbitmq
python main.py --count 5 --size 100 --only kafka

echo "🧪 Executando Teste 6: Benchmarks Integrados"
python main.py --count 10 --size 100
python main.py --count 20 --size 100 --rps 5
python main.py --count 30 --size 100 --producers 3 --consumers 2

echo "🧪 Executando Teste 7: Baseline HTTP"
python main.py --server --port 5000 &
sleep 5
python main.py --count 15 --size 100 --only baseline
pkill -f "python main.py --server"

echo "🧪 Executando Teste 8: Performance Comparativa"
python main.py --count 100 --size 100 --only baseline
python main.py --count 100 --size 100 --only rabbitmq
python main.py --count 100 --size 100 --only kafka

echo "✅ TODOS OS TESTES CONCLUÍDOS COM SUCESSO!"
echo "📊 Verifique os resultados em: logs/"
EOF

# Dar permissão de execução
chmod +x executar_todos_testes.sh

# Executar todos os testes
./executar_todos_testes.sh
```

---

## 📊 Análise e Visualização dos Resultados

### Estrutura dos Logs Gerados

```
logs/
├── baseline/
│   ├── benchmark_results.csv          # Resultados consolidados
│   ├── [timestamp]_send_times.json    # Timestamps de envio
│   ├── [timestamp]_latency.csv        # Medições de latência
│   └── [timestamp]_summary.csv        # Resumo estatístico
├── kafka/
│   ├── benchmark_results.csv          # Resultados consolidados
│   ├── [timestamp]_send_times.json    # Timestamps de envio
│   ├── [timestamp]_latency.csv        # Medições de latência
│   ├── [timestamp]_summary.csv        # Resumo estatístico
│   └── resource_monitoring.csv        # Monitoramento de recursos
└── rabbitmq/
    ├── benchmark_results.csv          # Resultados consolidados
    ├── [timestamp]_send_times.json    # Timestamps de envio
    ├── [timestamp]_latency.csv        # Medições de latência
    ├── [timestamp]_summary.csv        # Resumo estatístico
    └── resource_monitoring.csv        # Monitoramento de recursos
```

### Análise dos Resultados

#### 1. Visualização dos Resultados Consolidados
```bash
# Ver resultados consolidados de cada broker
echo "=== RESULTADOS BASELINE ==="
cat logs/baseline/benchmark_results.csv

echo "=== RESULTADOS RABBITMQ ==="
cat logs/rabbitmq/benchmark_results.csv

echo "=== RESULTADOS KAFKA ==="
cat logs/kafka/benchmark_results.csv
```

#### 2. Análise de Latência
```bash
# Analisar latências mais recentes
echo "=== LATÊNCIAS BASELINE ==="
ls -la logs/baseline/*latency.csv | tail -1 | xargs cat

echo "=== LATÊNCIAS RABBITMQ ==="
ls -la logs/rabbitmq/*latency.csv | tail -1 | xargs cat

echo "=== LATÊNCIAS KAFKA ==="
ls -la logs/kafka/*latency.csv | tail -1 | xargs cat
```

#### 3. Análise de Throughput
```bash
# Extrair throughput dos summaries
echo "=== THROUGHPUT BASELINE ==="
ls -la logs/baseline/*summary.csv | tail -1 | xargs grep "throughput"

echo "=== THROUGHPUT RABBITMQ ==="
ls -la logs/rabbitmq/*summary.csv | tail -1 | xargs grep "throughput"

echo "=== THROUGHPUT KAFKA ==="
ls -la logs/kafka/*summary.csv | tail -1 | xargs grep "throughput"
```

#### 4. Monitoramento de Recursos
```bash
# Verificar monitoramento de recursos
echo "=== RECURSOS RABBITMQ ==="
ls -la logs/rabbitmq/*resource_monitoring.csv | tail -1 | xargs head -10

echo "=== RECURSOS KAFKA ==="
ls -la logs/kafka/*resource_monitoring.csv | tail -1 | xargs head -10
```

### Visualização Gráfica (Opcional)

#### Instalação de Ferramentas de Visualização
```bash
# Instalar ferramentas para análise de dados
pip install pandas matplotlib seaborn numpy

# Criar script de visualização
cat > visualizar_resultados.py << 'EOF'
#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import glob
import os

def plot_benchmark_results():
    """Criar gráficos dos resultados de benchmark"""
    
    # Carregar dados
    baseline_data = pd.read_csv('logs/baseline/benchmark_results.csv')
    rabbitmq_data = pd.read_csv('logs/rabbitmq/benchmark_results.csv')
    kafka_data = pd.read_csv('logs/kafka/benchmark_results.csv')
    
    # Combinar dados
    all_data = pd.concat([
        baseline_data.assign(broker='Baseline'),
        rabbitmq_data.assign(broker='RabbitMQ'),
        kafka_data.assign(broker='Kafka')
    ])
    
    # Criar gráficos
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Throughput por broker
    sns.barplot(data=all_data, x='broker', y='throughput', ax=axes[0,0])
    axes[0,0].set_title('Throughput por Broker')
    axes[0,0].set_ylabel('Mensagens/segundo')
    
    # Latência por broker
    sns.barplot(data=all_data, x='broker', y='avg_latency', ax=axes[0,1])
    axes[0,1].set_title('Latência Média por Broker')
    axes[0,1].set_ylabel('Latência (segundos)')
    
    # Taxa de sucesso
    sns.barplot(data=all_data, x='broker', y='success_rate', ax=axes[1,0])
    axes[1,0].set_title('Taxa de Sucesso por Broker')
    axes[1,0].set_ylabel('Taxa de Sucesso (%)')
    
    # Duração total
    sns.barplot(data=all_data, x='broker', y='duration', ax=axes[1,1])
    axes[1,1].set_title('Duração Total por Broker')
    axes[1,1].set_ylabel('Duração (segundos)')
    
    plt.tight_layout()
    plt.savefig('benchmark_results.png', dpi=300, bbox_inches='tight')
    print("📊 Gráfico salvo como: benchmark_results.png")

if __name__ == "__main__":
    plot_benchmark_results()
EOF

# Executar visualização
python visualizar_resultados.py
```

---

## 📈 Interpretação dos Resultados

### Métricas Principais

#### 1. **Throughput (Mensagens/segundo)**
- **Baseline HTTP**: Esperado 50-200 msgs/s
- **RabbitMQ**: Esperado 1,000-5,000 msgs/s
- **Apache Kafka**: Esperado 5,000-20,000 msgs/s

#### 2. **Latência (Segundos)**
- **Baseline HTTP**: Esperado 0.001-0.010s
- **RabbitMQ**: Esperado 0.001-0.005s
- **Apache Kafka**: Esperado 0.001-0.003s

#### 3. **Taxa de Sucesso (%)**
- **Todos os brokers**: Esperado 95-100%

#### 4. **Uso de Recursos**
- **CPU**: Varia conforme carga
- **Memória**: RabbitMQ ~200MB, Kafka ~300MB

### Análise Comparativa

#### Cenário 1: Mensagens Pequenas (100 bytes)
```bash
# Executar teste específico
python main.py --count 100 --size 100 --only baseline
python main.py --count 100 --size 100 --only rabbitmq
python main.py --count 100 --size 100 --only kafka

# Analisar resultados
echo "=== COMPARAÇÃO - MENSAGENS PEQUENAS ==="
echo "Baseline: $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f3) msgs/s"
echo "RabbitMQ: $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f3) msgs/s"
echo "Kafka:    $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f3) msgs/s"
```

#### Cenário 2: Mensagens Grandes (4KB)
```bash
# Executar teste específico
python main.py --count 50 --size 4096 --only baseline
python main.py --count 50 --size 4096 --only rabbitmq
python main.py --count 50 --size 4096 --only kafka

# Analisar resultados
echo "=== COMPARAÇÃO - MENSAGENS GRANDES ==="
echo "Baseline: $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f3) msgs/s"
echo "RabbitMQ: $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f3) msgs/s"
echo "Kafka:    $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f3) msgs/s"
```

#### Cenário 3: Rate Limiting
```bash
# Executar teste com rate limiting
python main.py --count 20 --size 100 --rps 5 --only baseline
python main.py --count 20 --size 100 --rps 5 --only rabbitmq
python main.py --count 20 --size 100 --rps 5 --only kafka

# Verificar se rate limiting funcionou
echo "=== VERIFICAÇÃO RATE LIMITING ==="
echo "Baseline: $(tail -1 logs/baseline/benchmark_results.csv | cut -d',' -f3) msgs/s (esperado ~5)"
echo "RabbitMQ: $(tail -1 logs/rabbitmq/benchmark_results.csv | cut -d',' -f3) msgs/s (esperado ~5)"
echo "Kafka:    $(tail -1 logs/kafka/benchmark_results.csv | cut -d',' -f3) msgs/s (esperado ~5)"
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
            print(f"Throughput médio: {data['throughput'].mean():.2f} msgs/s")
            print(f"Latência média: {data['avg_latency'].mean():.6f}s")
            print(f"Taxa de sucesso média: {data['success_rate'].mean():.2f}%")
            print(f"Throughput máximo: {data['throughput'].max():.2f} msgs/s")
            print(f"Throughput mínimo: {data['throughput'].min():.2f} msgs/s")
            
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
        
        print(f"Baseline - Throughput médio: {baseline_data['throughput'].mean():.2f} msgs/s")
        print(f"RabbitMQ - Throughput médio: {rabbitmq_data['throughput'].mean():.2f} msgs/s")
        print(f"Kafka    - Throughput médio: {kafka_data['throughput'].mean():.2f} msgs/s")
        
        print()
        print("🏆 RANKING DE PERFORMANCE:")
        throughputs = {
            'Baseline': baseline_data['throughput'].mean(),
            'RabbitMQ': rabbitmq_data['throughput'].mean(),
            'Kafka': kafka_data['throughput'].mean()
        }
        
        ranking = sorted(throughputs.items(), key=lambda x: x[1], reverse=True)
        for i, (broker, throughput) in enumerate(ranking, 1):
            print(f"{i}º lugar: {broker} - {throughput:.2f} msgs/s")
            
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
python main.py --count 5 --size 100 --only rabbitmq
```

#### 10. **Erro: "Mensagem recebida sem timestamp correspondente"**
```bash
# Este erro indica que o consumidor está lendo mensagens antigas
# Limpar logs e executar teste limpo
./scripts/clear_logs.sh
python main.py --count 5 --size 100 --only kafka
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
- **Versão**: 4.1.1
- **Cluster**: 3 nós com Quorum Queues
- **Portas**: 5672 (AMQP), 15672 (Management)
- **Configurações**: Confirmação de entrega, mensagens persistentes

#### Apache Kafka
- **Versão**: 4.0 (imagem Docker: `bitnami/kafka:3.6`)
- **Modo**: KRaft (sem Zookeeper)
- **Queue Mode**: Simulação de KIP-932
- **Portas**: 9092 (Broker), 9000 (Kafdrop)
- **Nota**: A tag `3.6` do Bitnami garante reprodutibilidade e suporta KRaft. A numeração do Bitnami não corresponde exatamente à versão do Kafka. Para Kafka 4.0 exato, verifique tags disponíveis em: https://hub.docker.com/r/bitnami/kafka/tags

#### Baseline HTTP
- **Framework**: Flask
- **Porta**: 5000 (configurável)
- **Processamento**: 1ms simulado por requisição

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