#!/bin/bash

set -euo pipefail

echo "=============================="
echo "Iniciando configuração do ambiente de desenvolvimento..."
echo "=============================="

command_exists() {
    command -v "$1" &> /dev/null
}

exit_on_failure() {
    echo "❌ Erro crítico: $1"
    exit 1
}

if [ $(id -u) -eq 0 ]; then
    exit_on_failure "Execute o script como usuário normal, não como root!"
fi

echo "🔄 Atualizando pacotes do sistema..."
sudo apt update && sudo apt upgrade -y

python_dependencies=(
    python3
    python3-pip
    python3-venv
    python3-full
)

for pkg in "${python_dependencies[@]}"; do
    if ! dpkg -s "$pkg" > /dev/null 2>&1; then
        echo "🚀 Instalando $pkg..."
        sudo apt install -y --no-install-recommends "$pkg"
    else
        echo "✅ $pkg já está instalado"
    fi
done

if ! command_exists docker; then
    echo "🚀 Instalando Docker..."
    sudo apt install -y ca-certificates curl gnupg lsb-release software-properties-common
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
        sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
    sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
else
    echo "✅ Docker já está instalado"
fi

if ! docker compose version > /dev/null 2>&1; then
    echo "⚠️ Docker Compose (plugin) não funcional - execute manualmente: sudo apt install docker-compose-plugin"
fi

if ! getent group docker > /dev/null; then
    echo "🚀 Criando grupo docker..."
    sudo groupadd docker
fi

if ! groups "$USER" | grep -q '\bdocker\b'; then
    echo "🚀 Adicionando usuário ao grupo docker..."
    sudo usermod -aG docker "$USER"
    echo "⚠️ Reinicie a sessão para aplicar permissões do Docker"
else
    echo "✅ Usuário já está no grupo docker"
fi

venv_dir="venv"
if [ -d "$venv_dir" ]; then
    echo "🔁 Removendo ambiente virtual antigo..."
    rm -rf "$venv_dir"
fi

echo "🐍 Criando novo ambiente virtual em: $venv_dir"
python3 -m venv "$venv_dir"

echo "📦 Instalando bibliotecas Python no ambiente virtual..."
source "$venv_dir/bin/activate"
pip install --upgrade pip

requirements=(
    flask
    pika
    kafka-python
)

echo "➡️ Instalando: ${requirements[*]}"
pip install --no-cache-dir "${requirements[@]}"

echo "=============================="
echo "✅ Ambiente de desenvolvimento configurado com sucesso!"
echo "➡️ Para ativar o ambiente: source venv/bin/activate"
echo "⚠️ Reinicie o terminal para aplicar permissões do Docker (se necessário)"
echo "=============================="

set +euo pipefail