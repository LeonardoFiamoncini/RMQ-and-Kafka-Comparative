#!/usr/bin/env python3
"""
Script para testar TODOS os cenários da aplicação e validar métricas
"""

import subprocess
import sys
import time
import json
import csv
from pathlib import Path

LOGS_DIR = Path("logs")

# Cenários para testar baseados no README.md
SCENARIOS = [
    # Exemplos básicos
    {
        "name": "Exemplo 1: Teste Básico RabbitMQ",
        "command": ["python", "main.py", "--count", "100", "--producers", "1", "--consumers", "4", "--system", "rabbitmq"],
        "expected_messages": 100,
        "system": "rabbitmq"
    },
    {
        "name": "Exemplo 2: Teste Kafka múltiplos produtores",
        "command": ["python", "main.py", "--count", "1000", "--producers", "16", "--consumers", "64", "--system", "kafka"],
        "expected_messages": 1000,
        "system": "kafka"
    },
    {
        "name": "Exemplo 4: Teste com Rate Limiting",
        "command": ["python", "main.py", "--count", "1000", "--producers", "4", "--consumers", "4", "--system", "rabbitmq", "--rps", "100"],
        "expected_messages": 1000,
        "system": "rabbitmq"
    },
    # TESTE 1: Validação Básica
    {
        "name": "TESTE 1.2: RabbitMQ",
        "command": ["python", "main.py", "--count", "100", "--producers", "1", "--consumers", "4", "--system", "rabbitmq"],
        "expected_messages": 100,
        "system": "rabbitmq"
    },
    {
        "name": "TESTE 1.3: Kafka",
        "command": ["python", "main.py", "--count", "100", "--producers", "1", "--consumers", "4", "--system", "kafka"],
        "expected_messages": 100,
        "system": "kafka"
    },
    # TESTE 2: Rate Limiting
    {
        "name": "TESTE 2.2: RabbitMQ com RPS",
        "command": ["python", "main.py", "--count", "100", "--producers", "4", "--consumers", "4", "--system", "rabbitmq", "--rps", "20"],
        "expected_messages": 100,
        "system": "rabbitmq"
    },
    {
        "name": "TESTE 2.3: Kafka com RPS",
        "command": ["python", "main.py", "--count", "100", "--producers", "4", "--consumers", "4", "--system", "kafka", "--rps", "20"],
        "expected_messages": 100,
        "system": "kafka"
    },
    # TESTE 3: Múltiplos Clientes
    {
        "name": "TESTE 3.2: RabbitMQ múltiplos clientes",
        "command": ["python", "main.py", "--count", "1000", "--producers", "16", "--consumers", "64", "--system", "rabbitmq"],
        "expected_messages": 1000,
        "system": "rabbitmq"
    },
    {
        "name": "TESTE 3.3: Kafka múltiplos clientes",
        "command": ["python", "main.py", "--count", "1000", "--producers", "16", "--consumers", "64", "--system", "kafka"],
        "expected_messages": 1000,
        "system": "kafka"
    },
    # TESTE 6: Benchmarks Integrados
    {
        "name": "TESTE 6.1: Benchmark RabbitMQ",
        "command": ["python", "main.py", "--count", "1000", "--producers", "4", "--consumers", "4", "--system", "rabbitmq"],
        "expected_messages": 1000,
        "system": "rabbitmq"
    },
    {
        "name": "TESTE 6.2: Benchmark Kafka",
        "command": ["python", "main.py", "--count", "1000", "--producers", "4", "--consumers", "4", "--system", "kafka"],
        "expected_messages": 1000,
        "system": "kafka"
    },
]

def validate_metrics(system: str, expected_messages: int) -> dict:
    """Valida métricas coletadas"""
    system_dir = LOGS_DIR / system
    benchmark_file = system_dir / "benchmark_results.csv"
    
    if not benchmark_file.exists():
        return {
            "valid": False,
            "error": "Arquivo benchmark_results.csv não encontrado"
        }
    
    # Ler última linha do arquivo
    with open(benchmark_file, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            return {
                "valid": False,
                "error": "Nenhuma linha encontrada no arquivo"
            }
        last_row = rows[-1]
    
    # Validar métricas
    errors = []
    
    # Verificar mensagens
    try:
        messages = int(last_row.get('messages', 0))
        if messages != expected_messages:
            errors.append(f"Mensagens incorretas: esperado {expected_messages}, encontrado {messages}")
    except (ValueError, TypeError):
        errors.append(f"Valor inválido para messages: {last_row.get('messages')}")
    
    # Verificar latência média
    try:
        latency_avg = float(last_row.get('latency_avg', 0))
        if latency_avg < 0:
            errors.append(f"Latência média negativa: {latency_avg}")
        if latency_avg == 0 and expected_messages > 0:
            errors.append("Latência média é zero (deveria ter latências coletadas)")
    except (ValueError, TypeError):
        errors.append(f"Valor inválido para latency_avg: {last_row.get('latency_avg')}")
    
    # Verificar throughput
    try:
        throughput = float(last_row.get('throughput', 0))
        if throughput < 0:
            errors.append(f"Throughput negativo: {throughput}")
        if throughput == 0 and expected_messages > 0:
            errors.append("Throughput é zero (deveria ter mensagens processadas)")
    except (ValueError, TypeError):
        errors.append(f"Valor inválido para throughput: {last_row.get('throughput')}")
    
    # Verificar percentis
    for percentile in ['latency_50', 'latency_95', 'latency_99']:
        try:
            value = float(last_row.get(percentile, 0))
            if value < 0:
                errors.append(f"{percentile} negativo: {value}")
        except (ValueError, TypeError):
            errors.append(f"Valor inválido para {percentile}: {last_row.get(percentile)}")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "metrics": last_row
    }

def run_scenario(scenario: dict) -> dict:
    """Executa um cenário e valida métricas"""
    print(f"\n{'='*60}")
    print(f"🧪 {scenario['name']}")
    print(f"{'='*60}")
    print(f"Comando: {' '.join(scenario['command'])}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            scenario['command'],
            capture_output=True,
            text=True,
            timeout=300  # 5 minutos timeout
        )
        
        duration = time.time() - start_time
        
        if result.returncode != 0:
            return {
                "success": False,
                "error": f"Comando falhou com código {result.returncode}",
                "stderr": result.stderr[-500:] if result.stderr else "",
                "duration": duration
            }
        
        # Aguardar um pouco para garantir que arquivos foram salvos
        time.sleep(2)
        
        # Validar métricas
        validation = validate_metrics(scenario['system'], scenario['expected_messages'])
        
        return {
            "success": True,
            "validation": validation,
            "duration": duration,
            "stdout": result.stdout[-500:] if result.stdout else ""
        }
        
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Timeout após 5 minutos",
            "duration": time.time() - start_time
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Erro inesperado: {e}",
            "duration": time.time() - start_time
        }

def main():
    """Função principal"""
    print("🚀 TESTE COMPLETO DE TODOS OS CENÁRIOS")
    print("=" * 60)
    print(f"Total de cenários: {len(SCENARIOS)}")
    
    # Limpar logs antes de começar
    print("\n🧹 Limpando logs antigos...")
    subprocess.run(["./scripts/clear_logs.sh"], capture_output=True)
    
    results = []
    passed = 0
    failed = 0
    
    for i, scenario in enumerate(SCENARIOS, 1):
        print(f"\n[{i}/{len(SCENARIOS)}] Executando cenário...")
        result = run_scenario(scenario)
        results.append({
            "scenario": scenario['name'],
            **result
        })
        
        if result.get("success") and result.get("validation", {}).get("valid"):
            passed += 1
            print(f"✅ {scenario['name']} - PASSOU")
            if result.get("validation", {}).get("metrics"):
                metrics = result["validation"]["metrics"]
                print(f"   📊 T={metrics.get('latency_avg')}s, V={metrics.get('throughput')} msg/s")
        else:
            failed += 1
            print(f"❌ {scenario['name']} - FALHOU")
            if result.get("error"):
                print(f"   Erro: {result['error']}")
            if result.get("validation", {}).get("errors"):
                for error in result["validation"]["errors"]:
                    print(f"   • {error}")
    
    # Resumo final
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL")
    print("=" * 60)
    print(f"✅ Passou: {passed}/{len(SCENARIOS)}")
    print(f"❌ Falhou: {failed}/{len(SCENARIOS)}")
    print(f"📈 Taxa de sucesso: {(passed/len(SCENARIOS)*100):.1f}%")
    
    # Salvar resultados em arquivo
    results_file = Path("test_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\n📁 Resultados detalhados salvos em: {results_file}")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())


