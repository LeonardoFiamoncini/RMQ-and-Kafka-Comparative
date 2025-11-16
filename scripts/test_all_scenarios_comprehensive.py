#!/usr/bin/env python3
"""
Script COMPLETO para testar TODOS os cenários possíveis da aplicação
e identificar bugs sistematicamente.
"""

import subprocess
import sys
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Any
from itertools import product

# Configurações
LOGS_DIR = Path("logs")
RESULTS_FILE = Path("comprehensive_test_results.json")
TIMEOUT = 300  # 5 minutos por teste

# Valores válidos conforme main.py
VALID_COUNTS = [10, 100, 1000, 10000, 100000]
VALID_PRODUCERS = [1, 4, 16, 64]
VALID_CONSUMERS = [4, 64]
VALID_SYSTEMS = ["rabbitmq", "kafka", "baseline"]
VALID_RPS = [None, 20, 50, 100, 200]

def run_command(cmd: List[str], timeout: int = TIMEOUT) -> Dict[str, Any]:
    """Executa um comando e retorna resultado detalhado"""
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=Path.cwd()
        )
        duration = time.time() - start_time
        
        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "duration": duration,
            "stdout": result.stdout[-1000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
            "command": " ".join(cmd)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "duration": timeout,
            "error": f"Timeout após {timeout}s",
            "command": " ".join(cmd)
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "duration": 0,
            "error": str(e),
            "command": " ".join(cmd)
        }

def check_containers() -> bool:
    """Verifica se os containers Docker estão rodando"""
    result = run_command(["docker", "compose", "ps"], timeout=10)
    if not result["success"]:
        return False
    
    output = result["stdout"]
    # Verificar se há containers rodando
    lines = [l for l in output.split("\n") if l.strip() and not l.startswith("NAME")]
    return len(lines) > 0

def check_logs_exist(system: str) -> Dict[str, bool]:
    """Verifica se os arquivos de log foram criados"""
    log_dir = LOGS_DIR / system
    if not log_dir.exists():
        return {"exists": False, "files": []}
    
    files = list(log_dir.glob("*"))
    return {
        "exists": True,
        "files": [f.name for f in files],
        "has_benchmark_results": (log_dir / "benchmark_results.csv").exists(),
        "has_latency_files": len(list(log_dir.glob("*_latency.csv"))) > 0,
        "has_summary_files": len(list(log_dir.glob("*_summary.csv"))) > 0,
        "has_send_times": len(list(log_dir.glob("*_send_times.json"))) > 0
    }

def test_basic_scenarios() -> List[Dict[str, Any]]:
    """Testa cenários básicos de cada sistema"""
    results = []
    
    print("\n" + "="*70)
    print("TESTE 1: CENÁRIOS BÁSICOS")
    print("="*70)
    
    # Teste básico de cada sistema
    basic_tests = [
        {"system": "rabbitmq", "count": 10, "producers": 1, "consumers": 4},
        {"system": "kafka", "count": 10, "producers": 1, "consumers": 4},
        {"system": "baseline", "count": 10, "producers": 1, "consumers": 4},
    ]
    
    for test in basic_tests:
        print(f"\n🧪 Testando: {test['system']} (count={test['count']}, producers={test['producers']}, consumers={test['consumers']})")
        
        cmd = [
            "python", "main.py",
            "--count", str(test["count"]),
            "--producers", str(test["producers"]),
            "--consumers", str(test["consumers"]),
            "--system", test["system"]
        ]
        
        result = run_command(cmd)
        logs_check = check_logs_exist(test["system"])
        
        results.append({
            "test_type": "basic",
            "test_config": test,
            "result": result,
            "logs": logs_check,
            "passed": result["success"] and logs_check.get("has_benchmark_results", False)
        })
        
        status = "✅ PASSOU" if results[-1]["passed"] else "❌ FALHOU"
        print(f"   {status} (duração: {result['duration']:.2f}s)")
        if not result["success"]:
            print(f"   Erro: {result.get('error', result.get('stderr', '')[:200])}")
    
    return results

def test_parameter_combinations() -> List[Dict[str, Any]]:
    """Testa combinações de parâmetros válidos"""
    results = []
    
    print("\n" + "="*70)
    print("TESTE 2: COMBINAÇÕES DE PARÂMETROS")
    print("="*70)
    
    # Combinar parâmetros (limitado para não demorar muito)
    test_combinations = [
        # Pequenos testes rápidos
        {"count": 10, "producers": 1, "consumers": 4, "rps": None},
        {"count": 10, "producers": 4, "consumers": 4, "rps": None},
        {"count": 100, "producers": 1, "consumers": 4, "rps": None},
        {"count": 100, "producers": 4, "consumers": 4, "rps": 20},
        # Testes médios
        {"count": 1000, "producers": 4, "consumers": 4, "rps": None},
        {"count": 1000, "producers": 16, "consumers": 64, "rps": None},
    ]
    
    for combo in test_combinations:
        for system in ["rabbitmq", "kafka"]:  # Baseline precisa servidor separado
            print(f"\n🧪 {system}: count={combo['count']}, producers={combo['producers']}, consumers={combo['consumers']}, rps={combo['rps']}")
            
            cmd = [
                "python", "main.py",
                "--count", str(combo["count"]),
                "--producers", str(combo["producers"]),
                "--consumers", str(combo["consumers"]),
                "--system", system
            ]
            
            if combo["rps"]:
                cmd.extend(["--rps", str(combo["rps"])])
            
            result = run_command(cmd)
            logs_check = check_logs_exist(system)
            
            results.append({
                "test_type": "parameter_combination",
                "test_config": {**combo, "system": system},
                "result": result,
                "logs": logs_check,
                "passed": result["success"] and logs_check.get("has_benchmark_results", False)
            })
            
            status = "✅ PASSOU" if results[-1]["passed"] else "❌ FALHOU"
            print(f"   {status} (duração: {result['duration']:.2f}s)")
    
    return results

def test_server_mode() -> List[Dict[str, Any]]:
    """Testa o modo servidor baseline"""
    results = []
    
    print("\n" + "="*70)
    print("TESTE 3: MODO SERVIDOR BASELINE")
    print("="*70)
    
    # Testar servidor em background
    print("\n🧪 Iniciando servidor baseline...")
    server_cmd = ["python", "main.py", "--server", "--port", "5000"]
    server_process = subprocess.Popen(
        server_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Aguardar servidor iniciar
    time.sleep(5)
    
    # Verificar se servidor está rodando
    health_check = run_command(["curl", "-s", "http://localhost:5000/health"], timeout=5)
    
    if health_check["success"]:
        print("   ✅ Servidor iniciado com sucesso")
        
        # Testar envio de mensagens
        print("\n🧪 Testando envio de mensagens...")
        test_cmd = [
            "python", "main.py",
            "--count", "10",
            "--producers", "1",
            "--consumers", "4",
            "--system", "baseline"
        ]
        
        result = run_command(test_cmd, timeout=60)
        logs_check = check_logs_exist("baseline")
        
        results.append({
            "test_type": "server_mode",
            "test_config": {"port": 5000},
            "result": result,
            "logs": logs_check,
            "health_check": health_check,
            "passed": result["success"] and logs_check.get("has_benchmark_results", False)
        })
        
        status = "✅ PASSOU" if results[-1]["passed"] else "❌ FALHOU"
        print(f"   {status}")
    else:
        print("   ❌ Servidor não iniciou corretamente")
        results.append({
            "test_type": "server_mode",
            "test_config": {"port": 5000},
            "result": {"success": False},
            "health_check": health_check,
            "passed": False
        })
    
    # Parar servidor
    print("\n🧹 Parando servidor...")
    try:
        server_process.terminate()
        server_process.wait(timeout=5)
    except:
        server_process.kill()
    
    # Garantir que não há processos restantes
    run_command(["pkill", "-f", "python main.py --server"], timeout=5)
    
    return results

def test_chaos_engineering() -> List[Dict[str, Any]]:
    """Testa chaos engineering"""
    results = []
    
    print("\n" + "="*70)
    print("TESTE 4: CHAOS ENGINEERING")
    print("="*70)
    
    for system in ["rabbitmq", "kafka"]:
        print(f"\n🧪 Testando chaos engineering: {system}")
        
        cmd = [
            "python", "main.py",
            "--count", "100",
            "--producers", "1",
            "--consumers", "4",
            "--system", system,
            "--chaos",
            "--chaos-delay", "5"
        ]
        
        result = run_command(cmd, timeout=180)  # Mais tempo para chaos
        
        results.append({
            "test_type": "chaos_engineering",
            "test_config": {"system": system, "chaos_delay": 5},
            "result": result,
            "passed": result["success"]
        })
        
        status = "✅ PASSOU" if results[-1]["passed"] else "❌ FALHOU"
        print(f"   {status} (duração: {result['duration']:.2f}s)")
    
    return results

def test_edge_cases() -> List[Dict[str, Any]]:
    """Testa casos extremos e edge cases"""
    results = []
    
    print("\n" + "="*70)
    print("TESTE 5: CASOS EXTREMOS E EDGE CASES")
    print("="*70)
    
    edge_cases = [
        # Mínimo de mensagens
        {"count": 10, "producers": 1, "consumers": 4, "system": "rabbitmq"},
        {"count": 10, "producers": 1, "consumers": 4, "system": "kafka"},
        # Múltiplos produtores, poucas mensagens
        {"count": 10, "producers": 4, "consumers": 4, "system": "rabbitmq"},
        {"count": 10, "producers": 4, "consumers": 4, "system": "kafka"},
        # Rate limiting baixo
        {"count": 100, "producers": 1, "consumers": 4, "system": "rabbitmq", "rps": 10},
        {"count": 100, "producers": 1, "consumers": 4, "system": "kafka", "rps": 10},
    ]
    
    for case in edge_cases:
        system = case.pop("system")
        rps = case.pop("rps", None)
        
        print(f"\n🧪 Edge case: {system}, {case}")
        
        cmd = [
            "python", "main.py",
            "--count", str(case["count"]),
            "--producers", str(case["producers"]),
            "--consumers", str(case["consumers"]),
            "--system", system
        ]
        
        if rps:
            cmd.extend(["--rps", str(rps)])
        
        result = run_command(cmd)
        logs_check = check_logs_exist(system)
        
        results.append({
            "test_type": "edge_case",
            "test_config": {**case, "system": system, "rps": rps},
            "result": result,
            "logs": logs_check,
            "passed": result["success"] and logs_check.get("has_benchmark_results", False)
        })
        
        status = "✅ PASSOU" if results[-1]["passed"] else "❌ FALHOU"
        print(f"   {status}")
    
    return results

def test_invalid_parameters() -> List[Dict[str, Any]]:
    """Testa se a aplicação rejeita parâmetros inválidos corretamente"""
    results = []
    
    print("\n" + "="*70)
    print("TESTE 6: VALIDAÇÃO DE PARÂMETROS INVÁLIDOS")
    print("="*70)
    
    invalid_tests = [
        # Count inválido
        {"cmd": ["python", "main.py", "--count", "5", "--producers", "1", "--consumers", "4", "--system", "rabbitmq"], "should_fail": True},
        {"cmd": ["python", "main.py", "--count", "50", "--producers", "1", "--consumers", "4", "--system", "rabbitmq"], "should_fail": True},
        # Producers inválido
        {"cmd": ["python", "main.py", "--count", "100", "--producers", "2", "--consumers", "4", "--system", "rabbitmq"], "should_fail": True},
        {"cmd": ["python", "main.py", "--count", "100", "--producers", "8", "--consumers", "4", "--system", "rabbitmq"], "should_fail": True},
        # Consumers inválido
        {"cmd": ["python", "main.py", "--count", "100", "--producers", "1", "--consumers", "1", "--system", "rabbitmq"], "should_fail": True},
        {"cmd": ["python", "main.py", "--count", "100", "--producers", "1", "--consumers", "8", "--system", "rabbitmq"], "should_fail": True},
        # Sistema inválido
        {"cmd": ["python", "main.py", "--count", "100", "--producers", "1", "--consumers", "4", "--system", "invalid"], "should_fail": True},
    ]
    
    for test in invalid_tests:
        print(f"\n🧪 Testando rejeição: {' '.join(test['cmd'][2:])}")
        
        result = run_command(test["cmd"], timeout=10)
        
        # Deve falhar se should_fail=True, ou passar se should_fail=False
        expected_failure = test["should_fail"]
        actual_failure = not result["success"]
        
        passed = (expected_failure == actual_failure)
        
        results.append({
            "test_type": "invalid_parameters",
            "test_config": test,
            "result": result,
            "passed": passed
        })
        
        status = "✅ PASSOU" if passed else "❌ FALHOU"
        print(f"   {status} (esperado falhar: {expected_failure}, falhou: {actual_failure})")
    
    return results

def main():
    """Função principal"""
    print("🚀 TESTE COMPLETO E SISTEMÁTICO DE TODOS OS CENÁRIOS")
    print("="*70)
    
    # Verificar pré-requisitos
    print("\n📋 Verificando pré-requisitos...")
    
    if not Path("main.py").exists():
        print("❌ Erro: main.py não encontrado")
        return 1
    
    if not check_containers():
        print("⚠️  Aviso: Containers Docker não estão rodando")
        print("   Execute: docker compose up -d")
        response = input("   Continuar mesmo assim? (s/N): ")
        if response.lower() != 's':
            return 1
    
    # Limpar logs
    print("\n🧹 Limpando logs antigos...")
    run_command(["./scripts/clear_logs.sh"], timeout=30)
    
    all_results = []
    
    # Executar todos os testes
    try:
        all_results.extend(test_basic_scenarios())
        all_results.extend(test_parameter_combinations())
        all_results.extend(test_server_mode())
        all_results.extend(test_chaos_engineering())
        all_results.extend(test_edge_cases())
        all_results.extend(test_invalid_parameters())
    except KeyboardInterrupt:
        print("\n\n⚠️  Testes interrompidos pelo usuário")
        return 1
    
    # Resumo
    print("\n" + "="*70)
    print("📊 RESUMO FINAL")
    print("="*70)
    
    total = len(all_results)
    passed = sum(1 for r in all_results if r.get("passed", False))
    failed = total - passed
    
    print(f"Total de testes: {total}")
    print(f"✅ Passou: {passed}")
    print(f"❌ Falhou: {failed}")
    print(f"📈 Taxa de sucesso: {(passed/total*100):.1f}%")
    
    # Agrupar por tipo de teste
    print("\n📊 Resumo por tipo de teste:")
    test_types = {}
    for result in all_results:
        test_type = result.get("test_type", "unknown")
        if test_type not in test_types:
            test_types[test_type] = {"total": 0, "passed": 0}
        test_types[test_type]["total"] += 1
        if result.get("passed", False):
            test_types[test_type]["passed"] += 1
    
    for test_type, stats in test_types.items():
        print(f"   {test_type}: {stats['passed']}/{stats['total']} ({(stats['passed']/stats['total']*100):.1f}%)")
    
    # Salvar resultados
    print(f"\n📁 Salvando resultados em: {RESULTS_FILE}")
    with open(RESULTS_FILE, 'w') as f:
        json.dump({
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "success_rate": passed/total*100 if total > 0 else 0
            },
            "results": all_results
        }, f, indent=2)
    
    # Listar bugs encontrados
    print("\n🐛 BUGS ENCONTRADOS:")
    bugs = []
    for result in all_results:
        if not result.get("passed", False):
            bug = {
                "test_type": result.get("test_type"),
                "test_config": result.get("test_config"),
                "error": result.get("result", {}).get("error") or result.get("result", {}).get("stderr", "")[:200]
            }
            bugs.append(bug)
            print(f"   • {bug['test_type']}: {bug.get('error', 'Falhou sem erro específico')}")
    
    if not bugs:
        print("   ✅ Nenhum bug encontrado!")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())


