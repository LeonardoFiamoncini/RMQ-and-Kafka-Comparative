#!/bin/bash

echo "=============================="
echo "Iniciando configuração do ambiente de desenvolvimento..."
echo "=============================="

# Função para verificar se um comando existe
command_exists() {
    command -v "$1" &> /dev/null
}

# Atualizar pacotes
echo "🔄 Atualizando lista de pacotes..."
sudo apt update && sudo apt upgrade -y

# Python 3
if command_exists python3; then
    echo "✅ Python3 já está instalado"
else
    echo "🚀 Instalando Python3..."
    sudo apt install -y python3
fi

# Pip
if command_exists pip3; then
    echo "✅ pip3 já está instalado"
else
    echo "🚀 Instalando pip3..."
    sudo apt install -y python3-pip
fi

# Venv
if python3 -m venv --help &> /dev/null; then
    echo "✅ Módulo venv já está disponível"
else
    echo "🚀 Instalando módulo venv..."
    sudo apt install -y python3-venv
fi

# Docker
if command_exists docker; then
    echo "✅ Docker já está instalado"
else
    echo "🚀 Instalando Docker via repositório oficial..."
    sudo apt install -y ca-certificates curl gnupg lsb-release software-properties-common

    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

# Docker Compose
if docker compose version &> /dev/null; then
    echo "✅ Docker Compose já está disponível"
else
    echo "⚠️ Docker Compose (plugin) não está funcional — verifique instalação manualmente"
fi

# Adicionar usuário ao grupo docker
if groups $USER | grep -q '\bdocker\b'; then
    echo "✅ Usuário já está no grupo docker"
else
    echo "🚀 Adicionando usuário ao grupo docker..."
    sudo usermod -aG docker $USER
    echo "⚠️ Faça logout/login ou reinicie o terminal para aplicar o grupo docker."
fi

# Ambiente virtual - No setup, ele será removido (caso já exista) e gerado novamente
rm -rf venv
python3 -m venv venv
sudo apt install python3-full

# Ativar ambiente virtual e instalar dependências
echo "🐍 Ativando ambiente virtual e instalando bibliotecas Python..."
source venv/bin/activate
pip install --upgrade pip
pip install pika

echo "=============================="
echo "✅ Instalação finalizada com sucesso!"
echo "➡️ Execute agora: source venv/bin/activate"
echo "⚠️ E lembre-se de reiniciar o terminal para usar Docker sem sudo (se necessário)."
echo "=============================="
