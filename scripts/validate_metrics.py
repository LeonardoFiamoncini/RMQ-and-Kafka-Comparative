#!/usr/bin/env python3
"""
Script para validar métricas coletadas nos testes
Verifica se T (latência) e V (throughput) estão corretos
"""

import json
import csv
from pathlib import Path
from collections import defaultdict

LOGS_DIR = Path("logs")

def validate_latency_file(latency_file: Path, expected_count: int) -> dict:
    """Valida arquivo de latência"""
    results = {
        "file": str(latency_file),
        "expected": expected_count,
        "actual": 0,
        "valid": True,
        "errors": []
    }
    
    try:
        with open(latency_file, 'r') as f:
            reader = csv.DictReader(f)
            latencies = []
            msg_ids = set()
            
            for row in reader:
                try:
                    msg_id = row.get('msg_id', '')
                    latency = float(row.get('latency_seconds', 0))
                    
                    if msg_id in msg_ids:
                        results["errors"].append(f"Duplicata encontrada: msg_id {msg_id}")
                        results["valid"] = False
                    
                    msg_ids.add(msg_id)
                    
                    if latency < 0:
                        results["errors"].append(f"Latência negativa para msg_id {msg_id}: {latency}")
                        results["valid"] = False
                    
                    if latency > 3600:  # Mais de 1 hora é suspeito
                        results["errors"].append(f"Latência muito alta para msg_id {msg_id}: {latency}s")
                        results["valid"] = False
                    
                    latencies.append(latency)
                except (ValueError, KeyError) as e:
                    results["errors"].append(f"Erro ao processar linha: {e}")
                    results["valid"] = False
            
            results["actual"] = len(latencies)
            results["latencies"] = latencies
            
            if results["actual"] != expected_count:
                results["errors"].append(
                    f"Contagem incorreta: esperado {expected_count}, encontrado {results['actual']}"
                )
                results["valid"] = False
            
    except Exception as e:
        results["errors"].append(f"Erro ao ler arquivo: {e}")
        results["valid"] = False
    
    return results

def validate_send_times(send_times_file: Path, expected_count: int) -> dict:
    """Valida arquivo de send_times"""
    results = {
        "file": str(send_times_file),
        "expected": expected_count,
        "actual": 0,
        "valid": True,
        "errors": []
    }
    
    try:
        with open(send_times_file, 'r') as f:
            content = f.read().strip()
            send_times = json.loads(content)
            
            if not isinstance(send_times, dict):
                results["errors"].append("send_times não é um dicionário")
                results["valid"] = False
                return results
            
            results["actual"] = len(send_times)
            
            # Verificar se todas as chaves são strings numéricas válidas
            for key in send_times.keys():
                try:
                    int(key)  # Verificar se pode ser convertido para int
                except ValueError:
                    results["errors"].append(f"Chave inválida: {key}")
                    results["valid"] = False
            
            # Verificar se todos os valores são timestamps válidos
            for key, value in send_times.items():
                try:
                    timestamp = float(value)
                    if timestamp <= 0:
                        results["errors"].append(f"Timestamp inválido para {key}: {timestamp}")
                        results["valid"] = False
                except (ValueError, TypeError):
                    results["errors"].append(f"Valor inválido para {key}: {value}")
                    results["valid"] = False
            
            if results["actual"] != expected_count:
                results["errors"].append(
                    f"Contagem incorreta: esperado {expected_count}, encontrado {results['actual']}"
                )
                results["valid"] = False
                
    except json.JSONDecodeError as e:
        results["errors"].append(f"Erro ao fazer parse do JSON: {e}")
        results["valid"] = False
    except Exception as e:
        results["errors"].append(f"Erro ao ler arquivo: {e}")
        results["valid"] = False
    
    return results

def validate_benchmark_results(benchmark_file: Path) -> dict:
    """Valida arquivo de resultados consolidados"""
    results = {
        "file": str(benchmark_file),
        "valid": True,
        "errors": [],
        "rows": []
    }
    
    try:
        with open(benchmark_file, 'r') as f:
            reader = csv.DictReader(f)
            
            for row_num, row in enumerate(reader, start=2):  # Começar em 2 (linha 1 é header)
                row_errors = []
                
                # Verificar campos obrigatórios
                required_fields = ['tech', 'messages', 'latency_avg', 'throughput']
                for field in required_fields:
                    if field not in row:
                        row_errors.append(f"Campo obrigatório ausente: {field}")
                
                # Validar valores numéricos
                try:
                    messages = int(row.get('messages', 0))
                    if messages <= 0:
                        row_errors.append(f"Mensagens deve ser > 0, encontrado: {messages}")
                except (ValueError, TypeError):
                    row_errors.append(f"Valor inválido para messages: {row.get('messages')}")
                
                try:
                    latency_avg = float(row.get('latency_avg', 0))
                    if latency_avg < 0:
                        row_errors.append(f"Latência média negativa: {latency_avg}")
                except (ValueError, TypeError):
                    row_errors.append(f"Valor inválido para latency_avg: {row.get('latency_avg')}")
                
                try:
                    throughput = float(row.get('throughput', 0))
                    if throughput < 0:
                        row_errors.append(f"Throughput negativo: {throughput}")
                except (ValueError, TypeError):
                    row_errors.append(f"Valor inválido para throughput: {row.get('throughput')}")
                
                if row_errors:
                    results["valid"] = False
                    results["errors"].append(f"Linha {row_num}: {', '.join(row_errors)}")
                
                results["rows"].append(row)
                
    except Exception as e:
        results["errors"].append(f"Erro ao ler arquivo: {e}")
        results["valid"] = False
    
    return results

def validate_system(system: str) -> dict:
    """Valida todas as métricas de um sistema"""
    system_dir = LOGS_DIR / system
    
    if not system_dir.exists():
        return {
            "system": system,
            "valid": False,
            "errors": [f"Diretório não encontrado: {system_dir}"],
            "latency_files": [],
            "send_times_files": [],
            "benchmark_results": None
        }
    
    results = {
        "system": system,
        "valid": True,
        "errors": [],
        "latency_files": [],
        "send_times_files": [],
        "benchmark_results": None
    }
    
    # Encontrar arquivos mais recentes
    latency_files = sorted(system_dir.glob("*_latency.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
    send_times_files = sorted(system_dir.glob("*_send_times.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    benchmark_file = system_dir / "benchmark_results.csv"
    
    # Validar arquivos de latência
    for latency_file in latency_files[:3]:  # Validar os 3 mais recentes
        # Tentar extrair count do nome do arquivo ou usar um valor padrão
        # Por enquanto, vamos apenas validar a estrutura
        validation = validate_latency_file(latency_file, -1)  # -1 = não validar contagem
        # Remover erros de contagem quando expected é -1
        if validation["errors"]:
            validation["errors"] = [e for e in validation["errors"] if "Contagem incorreta" not in e]
            if not validation["errors"]:
                validation["valid"] = True
        results["latency_files"].append(validation)
        if not validation["valid"]:
            results["valid"] = False
            results["errors"].extend(validation["errors"])
    
    # Validar arquivos send_times
    for send_times_file in send_times_files[:3]:  # Validar os 3 mais recentes
        validation = validate_send_times(send_times_file, -1)  # -1 = não validar contagem
        # Remover erros de contagem quando expected é -1
        if validation["errors"]:
            validation["errors"] = [e for e in validation["errors"] if "Contagem incorreta" not in e]
            if not validation["errors"]:
                validation["valid"] = True
        results["send_times_files"].append(validation)
        if not validation["valid"]:
            results["valid"] = False
            results["errors"].extend(validation["errors"])
    
    # Validar benchmark_results
    if benchmark_file.exists():
        validation = validate_benchmark_results(benchmark_file)
        results["benchmark_results"] = validation
        if not validation["valid"]:
            results["valid"] = False
            results["errors"].extend(validation["errors"])
    
    return results

def main():
    """Função principal"""
    print("🔍 VALIDAÇÃO DE MÉTRICAS")
    print("=" * 60)
    
    systems = ["baseline", "rabbitmq", "kafka"]
    all_valid = True
    
    for system in systems:
        print(f"\n📊 Validando {system.upper()}...")
        results = validate_system(system)
        
        if results["valid"]:
            print(f"   ✅ {system.upper()} - Válido")
        else:
            print(f"   ❌ {system.upper()} - Inválido")
            all_valid = False
            for error in results["errors"]:
                print(f"      • {error}")
        
        # Mostrar estatísticas
        if results["latency_files"]:
            latest = results["latency_files"][0]
            if latest.get("actual", 0) > 0:
                latencies = latest.get("latencies", [])
                if latencies:
                    avg = sum(latencies) / len(latencies)
                    print(f"   📈 Latências: {latest['actual']} mensagens, média: {avg:.6f}s")
        
        if results["send_times_files"]:
            latest = results["send_times_files"][0]
            print(f"   📤 Send Times: {latest['actual']} timestamps")
        
        if results["benchmark_results"]:
            rows = results["benchmark_results"]["rows"]
            if rows:
                latest_row = rows[-1]  # Última linha
                print(f"   📊 Último benchmark: {latest_row.get('messages')} msgs, "
                      f"T={latest_row.get('latency_avg')}s, V={latest_row.get('throughput')} msg/s")
    
    print("\n" + "=" * 60)
    if all_valid:
        print("✅ TODAS AS MÉTRICAS VÁLIDAS")
    else:
        print("❌ PROBLEMAS ENCONTRADOS NAS MÉTRICAS")
    
    return 0 if all_valid else 1

if __name__ == "__main__":
    exit(main())

