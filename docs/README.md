# 🚀 RabbitMQ vs Apache Kafka - Comparative Benchmark

Este projeto implementa um sistema completo de benchmark comparativo entre **RabbitMQ** e **Apache Kafka**, incluindo uma baseline HTTP síncrona para comparação de performance. O sistema foi desenvolvido seguindo as melhores práticas de engenharia de software e inclui funcionalidades avançadas como rate limiting, chaos engineering e monitoramento de recursos.

## 🎯 Objetivos do Projeto

- **Comparação de Performance**: Benchmark detalhado entre RabbitMQ, Kafka e HTTP síncrono
- **Tolerância a Falhas**: Testes automatizados de recuperação e disponibilidade
- **Escalabilidade**: Suporte a múltiplos produtores e consumidores concorrentes
- **Monitoramento**: Coleta de métricas de recursos e performance em tempo real
- **Análise de Latência**: Medição precisa de tempos de resposta end-to-end

## 📋 Pré-requisitos

- **Sistema Operacional**: Ubuntu 24.04 LTS (ou similar)
- **Docker**: Versão 20.10+ com Docker Compose
- **Python**: 3.10+ com pip
- **Recursos**: Mínimo 4GB RAM, 2 CPU cores

## 🚀 Configuração Rápida

### 1. Configuração Automática do Ambiente
```bash
# Dar permissão de execução e rodar o script
chmod +x scripts/setup_dev_environment.sh
./scripts/setup_dev_environment.sh
```

### 2. Ativar Ambiente Virtual
```bash
source venv/bin/activate
```

### 3. Iniciar Infraestrutura
```bash
docker compose up -d
```

### 4. Verificar Serviços
```bash
# Verificar status dos containers
docker compose ps

# Ver logs em tempo real
docker compose logs -f
```

## 🧪 Executando Benchmarks

### Comando Principal
O sistema utiliza o `main.py` como ponto de entrada único:

```bash
# Benchmark completo (todos os brokers)
python main.py --count 100 --size 1024

# Benchmark específico
python main.py --only kafka --count 50 --size 512
python main.py --only rabbitmq --count 50 --size 512
python main.py --only baseline --count 50 --size 512

# Com rate limiting
python main.py --count 100 --rps 10

# Múltiplos clientes
python main.py --count 200 --producers 4 --consumers 2

# Chaos engineering
python main.py --chaos --count 50 --chaos-delay 15
```

### Parâmetros Disponíveis
- `--count`: Número de mensagens (padrão: 100)
- `--size`: Tamanho das mensagens em bytes (padrão: 1024)
- `--rps`: Rate limiting em mensagens por segundo
- `--producers`: Número de produtores concorrentes (padrão: 1)
- `--consumers`: Número de consumidores concorrentes (padrão: 1)
- `--only`: Broker específico (kafka, rabbitmq, baseline)
- `--chaos`: Ativar experimentos de tolerância a falhas
- `--chaos-delay`: Delay antes de causar falha (segundos)

## 🔧 Funcionalidades Avançadas

### 1. Baseline HTTP Síncrona
```bash
# Iniciar servidor baseline
python main.py --server --port 5000

# Testar cliente baseline
python main.py --only baseline --count 10
```

### 2. Rate Limiting (RPS)
```bash
# Teste com 5 mensagens por segundo
python main.py --count 20 --rps 5
```

### 3. Múltiplos Clientes Concorrentes
```bash
# 3 produtores e 2 consumidores
python main.py --count 60 --producers 3 --consumers 2
```

### 4. Chaos Engineering
```bash
# Teste de tolerância a falhas
python main.py --chaos --count 100 --chaos-delay 10
```

### 5. Monitoramento de Recursos
O sistema automaticamente coleta métricas de CPU e memória durante os benchmarks.

## 📊 Análise de Resultados

### Localização dos Logs
```
logs/
├── baseline/
│   ├── benchmark_results.csv
│   └── [timestamp]_summary.csv
├── kafka/
│   ├── benchmark_results.csv
│   ├── [timestamp]_send_times.json
│   ├── [timestamp]_latency.csv
│   └── [timestamp]_summary.csv
└── rabbitmq/
    ├── benchmark_results.csv
    ├── [timestamp]_send_times.json
    ├── [timestamp]_latency.csv
    └── [timestamp]_summary.csv
```

### Métricas Coletadas
- **Latência**: Tempo end-to-end de envio até processamento
- **Throughput**: Mensagens processadas por segundo
- **Taxa de Sucesso**: Percentual de mensagens entregues com sucesso
- **Recursos**: Uso de CPU e memória dos brokers
- **Tolerância a Falhas**: Tempo de indisponibilidade e recuperação

## 🔍 Interfaces de Monitoramento

### RabbitMQ Management
- **URL**: http://localhost:15672
- **Credenciais**: `user` / `password`
- **Funcionalidades**: Monitoramento de filas, conexões e cluster

### Kafdrop (Kafka)
- **URL**: http://localhost:9000
- **Funcionalidades**: Visualização de tópicos, consumidores e mensagens

### RabbitMQ Cluster
- **Nó 1**: http://localhost:15672
- **Nó 2**: http://localhost:15673
- **Nó 3**: http://localhost:15674

## ⚙️ Arquitetura do Projeto

```
.
├── main.py                          # Ponto de entrada principal
├── docker-compose.yml               # Infraestrutura Docker
├── requirements.txt                 # Dependências Python
├── src/                            # Código fonte modular
│   ├── core/                       # Configurações e utilitários
│   │   ├── config.py              # Configurações centralizadas
│   │   ├── logger.py              # Sistema de logging
│   │   └── metrics.py             # Coleta de métricas
│   ├── brokers/                    # Implementações dos brokers
│   │   ├── base.py                # Classe base abstrata
│   │   ├── baseline/              # HTTP síncrono
│   │   ├── kafka/                 # Apache Kafka
│   │   └── rabbitmq/              # RabbitMQ
│   ├── orchestration/              # Orquestração e testes
│   │   ├── benchmark.py           # Execução de benchmarks
│   │   ├── chaos.py               # Chaos engineering
│   │   └── monitoring.py          # Monitoramento de recursos
│   └── web/                       # Interface web (opcional)
├── scripts/                        # Scripts de automação
│   ├── setup_dev_environment.sh   # Configuração do ambiente
│   ├── clear_logs.sh              # Limpeza de logs
│   └── rabbitmq_cluster_init.sh   # Inicialização do cluster
├── docs/                          # Documentação
│   ├── README.md                  # Este arquivo
│   └── spec.md                    # Especificação técnica
├── tests/                         # Testes automatizados
└── logs/                          # Logs e resultados
```

## 🛠️ Desenvolvimento

### Formatação de Código
```bash
# Formatar código com black
black src/

# Ordenar imports com isort
isort src/

# Verificar qualidade com flake8
flake8 src/
```

### Executar Testes
```bash
# Executar todos os testes
pytest tests/

# Com cobertura
pytest --cov=src tests/
```

### Limpeza de Logs
```bash
# Limpar todos os logs
./scripts/clear_logs.sh
```

## 🛑 Parando o Ambiente

```bash
# Parar containers
docker compose down

# Desativar ambiente virtual
deactivate

# Remover volumes (cuidado: apaga dados)
docker compose down -v
```

## 🔧 Configurações Avançadas

### RabbitMQ
- **Quorum Queues**: Habilitadas para alta disponibilidade
- **Cluster**: 3 nós com replicação automática
- **Confirmação de Entrega**: Habilitada para garantia de entrega

### Apache Kafka
- **KRaft Mode**: Sem dependência do Zookeeper
- **Queue Mode**: Simulação de comportamento de fila
- **Compressão**: GZIP para otimização de rede

### Baseline HTTP
- **Flask**: Servidor web leve
- **Processamento**: Simulação de 1ms por requisição
- **Métricas**: Coleta de estatísticas em tempo real

## ⁉️ Solução de Problemas

### Problemas Comuns

#### 1. Erro de Permissão Docker
```bash
# Verificar se usuário está no grupo docker
groups | grep docker

# Se não estiver, reinicie o terminal após setup
```

#### 2. Porta em Uso
```bash
# Verificar portas em uso
sudo netstat -tlnp | grep :5672
sudo netstat -tlnp | grep :9092

# Parar serviços conflitantes
sudo systemctl stop rabbitmq-server
```

#### 3. Containers Não Iniciam
```bash
# Verificar logs
docker compose logs

# Recriar containers
docker compose down
docker compose up -d --force-recreate
```

#### 4. Problemas de Cluster RabbitMQ
```bash
# Verificar status do cluster
docker exec rabbitmq-1 rabbitmqctl cluster_status

# Reinicializar cluster
docker compose restart rabbitmq-1 rabbitmq-2 rabbitmq-3
```

### Logs de Debug
```bash
# Logs detalhados da aplicação
tail -f logs/application.log

# Logs específicos de um broker
tail -f logs/kafka/benchmark_results.csv
tail -f logs/rabbitmq/benchmark_results.csv
```

## 📈 Performance Esperada

### Cenários Típicos
- **Baseline HTTP**: ~100-500 msgs/s (dependendo do hardware)
- **RabbitMQ**: ~1,000-10,000 msgs/s
- **Apache Kafka**: ~10,000-100,000 msgs/s

### Fatores que Afetam Performance
- **Tamanho das Mensagens**: Mensagens maiores = menor throughput
- **Rate Limiting**: Limita artificialmente o throughput
- **Recursos do Sistema**: CPU, RAM e I/O
- **Rede**: Latência e largura de banda

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para mais detalhes.

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique a seção de solução de problemas
2. Consulte os logs em `logs/`
3. Abra uma issue no repositório
4. Consulte a documentação técnica em `docs/spec.md`