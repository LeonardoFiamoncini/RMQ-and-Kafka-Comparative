#!/bin/bash

set -euo pipefail

echo "=============================="
echo "Iniciando configuração do ambiente de desenvolvimento..."
echo "Versões específicas garantidas para reprodutibilidade:"
echo "  - RabbitMQ: 4.1.1 (imagem: rabbitmq:4.1.1-management)"
echo "  - Apache Kafka: 4.0 (imagem: apache/kafka:4.0.0)"
echo "  - Python: 3.12+"
echo "  - Docker Compose: 2.0+"
echo "=============================="

command_exists() {
    command -v "$1" &> /dev/null
}

exit_on_failure() {
    echo "Erro crítico: $1"
    exit 1
}

if [ $(id -u) -eq 0 ]; then
    exit_on_failure "Execute o script como usuário normal, não como root!"
fi

# Detectar sistema operacional
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS=$ID
            OS_VERSION=$VERSION_ID
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        OS="unknown"
    fi
}

detect_os

echo "🔄 Sistema detectado: $OS"
if [[ "$OS" == "linux" ]]; then
    echo "🔄 Atualizando pacotes do sistema..."
    sudo apt update && sudo apt upgrade -y
elif [[ "$OS" == "macos" ]]; then
    echo "macOS detectado - pulando atualização de pacotes do sistema"
fi

# Instalar dependências Python baseado no OS
if [[ "$OS" == "linux" ]]; then
    python_dependencies=(
        python3
        python3-pip
        python3-venv
        python3-full
    )
    
    for pkg in "${python_dependencies[@]}"; do
        if ! dpkg -s "$pkg" > /dev/null 2>&1; then
            echo "Instalando $pkg..."
            sudo apt install -y --no-install-recommends "$pkg"
        else
            echo "$pkg já está instalado"
        fi
    done
elif [[ "$OS" == "macos" ]]; then
    if ! command_exists python3; then
        echo "Python 3 não encontrado. Instale via Homebrew: brew install python3"
        exit 1
    fi
    echo "Python 3 encontrado: $(python3 --version)"
fi

if ! command_exists docker; then
    if [[ "$OS" == "linux" ]]; then
        echo "Instalando Docker..."
        sudo apt install -y ca-certificates curl gnupg lsb-release software-properties-common
        sudo mkdir -p /etc/apt/keyrings
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
            sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

        echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | \
        sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

        sudo apt update
        sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    elif [[ "$OS" == "macos" ]]; then
        echo "Docker não encontrado no macOS."
        echo "   Instale Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
else
    echo "Docker já está instalado: $(docker --version)"
fi

if ! docker compose version > /dev/null 2>&1; then
    echo "Docker Compose (plugin) não funcional - execute manualmente: sudo apt install docker-compose-plugin"
fi

# Configurar permissões Docker (apenas Linux)
if [[ "$OS" == "linux" ]]; then
    if ! getent group docker > /dev/null; then
        echo "Criando grupo docker..."
        sudo groupadd docker
    fi

    if ! groups "$USER" | grep -q '\bdocker\b'; then
        echo "Adicionando usuário ao grupo docker..."
        sudo usermod -aG docker "$USER"
        echo "Reinicie a sessão para aplicar permissões do Docker"
    else
        echo "Usuário já está no grupo docker"
    fi
elif [[ "$OS" == "macos" ]]; then
    echo "macOS: Permissões Docker gerenciadas pelo Docker Desktop"
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

# Usar requirements.txt para garantir versões fixas e reprodutibilidade
if [ -f "requirements.txt" ]; then
    echo "Instalando dependências de requirements.txt (versões fixas para reprodutibilidade)..."
    pip install --no-cache-dir -r requirements.txt
else
    echo "Arquivo requirements.txt não encontrado. Instalando dependências básicas..."
    requirements=(
        flask==3.1.1
        werkzeug==3.0.1
        pika==1.3.2
        kafka-python==2.2.11
        psutil==7.0.0
        requests==2.31.0
        matplotlib==3.10.7
        seaborn==0.13.2
        pandas==2.3.3
        numpy==2.3.5
        scipy==1.16.3
        black==24.10.0
        isort==5.13.2
        flake8==7.1.1
        pytest==8.3.3
    )
    echo "Instalando: ${requirements[*]}"
    pip install --no-cache-dir "${requirements[@]}"
fi

echo "=============================="
echo "Ambiente de desenvolvimento configurado com sucesso!"
echo ""
echo "📋 Próximos passos:"
echo "   1. Ativar ambiente virtual: source venv/bin/activate"
if [[ "$OS" == "linux" ]]; then
    echo "   2. Reiniciar terminal para aplicar permissões do Docker (se necessário)"
fi
echo "   3. Iniciar containers: docker compose up -d"
echo "   4. Aguardar inicialização: sleep 60"
echo "   5. Verificar status: docker compose ps"
echo ""
echo "Documentação completa: docs/README.md"
echo "Versões garantidas para reprodutibilidade:"
echo "   - RabbitMQ: 4.1.1"
echo "   - Apache Kafka: 4.0.0"
echo "   - Python: 3.12+"
echo "=============================="

set +euo pipefail