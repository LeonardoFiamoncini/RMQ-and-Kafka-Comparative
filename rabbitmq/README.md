# RabbitMQ App

## Passo a Passo

### Execute os comandos abaixo para configurar cada uma das dependências e subir corretamente o ambiente em Docker

### 1º Passo

```bash
sh setup_dev_environment.sh

### 2º Passo

```bash
source venv/bin/activate

### 3º Passo

```bash
docker-compose up -d

## Após isso, basta executar os comandos abaixo para enviar e consumir mensagens da Queue, respectivamente

```bash
python producer.py

```bash
python consumer.py