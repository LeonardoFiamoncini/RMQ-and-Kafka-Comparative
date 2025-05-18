# 🐇 RabbitMQ App - Message Queue Example

Este projeto demonstra a configuração de um ambiente com RabbitMQ em Docker e scripts Python para produtor/consumidor de mensagens.

## 📋 Pré-requisitos
- Ubuntu 24.04 LTS (ou similar)
- Docker e Docker Compose instalados *(o script de setup faz isso automaticamente)*
- Python 3.10+

## 🚀 Configuração do Ambiente

### 1. Executar Script de Configuração
```bash
# Dar permissão de execução e rodar o script
chmod +x setup_dev_environment.sh
./setup_dev_environment.sh
```

### 2. Ativar Ambiente Virtual
```bash
source venv/bin/activate
# Se ocorrer erro, use:
# . venv/bin/activate
```

### 3. Iniciar Containers Docker
```bash
docker compose up -d
```

## 🧪 Testando o Sistema

### Enviar Mensagens (Produtor)
```bash
python producer.py
```

### Consumir Mensagens (Consumidor)
```bash
python consumer.py
```

## 🛑 Parando o Ambiente
```bash
# Desativar ambiente virtual
deactivate

# Parar e remover containers
docker compose down
```

## 🔍 Verificando os Serviços

Acesse o **RabbitMQ Management Interface** em:  
http://localhost:15672  
Credenciais padrão: `guest`/`guest`

Para ver os logs em tempo real:
```bash
docker compose logs -f
```

## ⚙️ Estrutura do Projeto
```
.
├── docker-compose.yml
├── setup_dev_environment.sh
├── producer.py
├── consumer.py
└── venv/               # Ambiente virtual Python (gerado automaticamente)
```

## 💡 Informações Adicionais

### Variáveis de Ambiente
O arquivo `docker-compose.yml` configura automaticamente:
- Usuário padrão: `RABBITMQ_DEFAULT_USER=guest`
- Senha padrão: `RABBITMQ_DEFAULT_PASS=guest`

### Notas Importantes
1. Após executar o script de setup, reinicie o terminal para aplicar as permissões do Docker
2. O ambiente virtual Python é recriado automaticamente a cada execução do script
3. Para modificar as configurações do RabbitMQ, edite o `docker-compose.yml`

## ⁉️ Solução de Problemas
Se encontrar erros de permissão com Docker:
```bash
# Verificar se o usuário está no grupo 'docker'
groups | grep docker

# Se não estiver, reinicie a sessão do terminal após executar o setup
```
