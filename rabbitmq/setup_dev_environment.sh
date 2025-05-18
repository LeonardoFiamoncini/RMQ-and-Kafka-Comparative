#!/bin/bash

# Configuração segura: sair em caso de erro não tratado e uso de variáveis não definidas
set -euo pipefail

echo "=============================="
echo "Iniciando configuração do ambiente de desenvolvimento..."
echo "=============================="

# --- Funções auxiliares ---
command_exists() {
    command -v "$1" &> /dev/null
}

exit_on_failure() {
    echo "❌ Erro crítico: $1"
    exit 1
}

# --- Verificação inicial ---
# Garantir que está sendo executado como usuário normal (não root)
if [ $(id -u) -eq 0 ]; then
    exit_on_failure "Execute o script como usuário normal, não como root!"
fi

# --- Atualização do sistema ---
echo "🔄 Atualizando lista de pacotes..."
if ! sudo apt update > /dev/null 2>&1; then
    exit_on_failure "Falha ao atualizar repositórios APT"
fi

sudo apt upgrade -y --allow-downgrades --allow-remove-essential --allow-change-held-packages

# --- Instalação Python ---
python_dependencies=(
    python3
    python3-pip
    python3-venv
    python3-full
)

for pkg in "${python_dependencies[@]}"; do
    if ! dpkg -s "$pkg" > /dev/null 2>&1; then
        echo "🚀 Instalando $pkg..."
        sudo apt install -y --no-install-recommends "$pkg" || exit_on_failure "Falha ao instalar $pkg"
    else
        echo "✅ $pkg já está instalado"
    fi
done

# --- Docker ---
if ! command_exists docker; then
    echo "🚀 Instalando Docker..."
    
    # Verificar dependências
    docker_deps=(
        ca-certificates
        curl
        gnupg
        lsb-release
        software-properties-common
    )
    
    sudo apt install -y "${docker_deps[@]}" || exit_on_failure "Falha ao instalar dependências do Docker"

    # Configurar repositório
    docker_keyring="/etc/apt/keyrings/docker.gpg"
    docker_list="/etc/apt/sources.list.d/docker.list"
    
    [ ! -f "$docker_keyring" ] && 
        sudo mkdir -p /etc/apt/keyrings &&
        curl -fsSL https://download.docker.com/linux/ubuntu/gpg | 
        sudo gpg --dearmor -o "$docker_keyring"

    [ ! -f "$docker_list" ] &&
        echo "deb [arch=$(dpkg --print-architecture) signed-by=${docker_keyring}] \
        https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | 
        sudo tee "$docker_list" > /dev/null

    sudo apt update || exit_on_failure "Falha ao atualizar após adicionar repositório Docker"
    
    docker_pkgs=(
        docker-ce
        docker-ce-cli
        containerd.io
        docker-buildx-plugin
        docker-compose-plugin
    )
    
    sudo apt install -y "${docker_pkgs[@]}" || exit_on_failure "Falha ao instalar pacotes Docker"
fi

# --- Validação Docker Compose ---
if ! docker compose version > /dev/null 2>&1; then
    echo "⚠️ Docker Compose (plugin) não está funcional - versão mínima requerida: 2.0"
    echo "   Execute manualmente se necessário: sudo apt install docker-compose-plugin"
fi

# --- Configuração de usuário ---
if ! groups "$USER" | grep -q '\bdocker\b'; then
    echo "🚀 Adicionando usuário ao grupo docker..."
    sudo usermod -aG docker "$USER" || exit_on_failure "Falha ao adicionar ao grupo docker"
    echo "⚠️ Reinicie a sessão do terminal para aplicar as permissões"
fi

# --- Ambiente Virtual ---
venv_dir="venv"
echo "🐍 Configurando ambiente virtual em: $venv_dir"
rm -rf "$venv_dir"
python3 -m venv "$venv_dir"

# --- Dependências Python ---
echo "📦 Instalando dependências Python..."
source "$venv_dir/bin/activate"
pip install --upgrade pip || exit_on_failure "Falha ao atualizar pip"

requirements="pika"
if ! pip install --no-cache-dir $requirements; then
    exit_on_failure "Falha ao instalar dependências Python"
fi

# --- Finalização ---
echo "=============================="
echo "✅ Instalação finalizada com sucesso!"
echo "➡️ Para ativar o ambiente: source $venv_dir/bin/activate"
echo "⚠️ Reinicie o terminal para usar Docker sem sudo"
echo "=============================="

# Restauração das configurações padrão do shell
set +euo pipefail