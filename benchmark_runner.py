import subprocess
import time
import csv
import os
from datetime import datetime
import argparse
import psutil
from statistics import mean, median, quantiles
import multiprocessing
from multiprocessing import Pool, Queue, Process
import json
import glob
import threading
import signal
import random

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")

TECHS = {
    "rabbitmq": {
        "producer": os.path.join(BASE_DIR, "rabbitmq", "producer.py"),
        "consumer": os.path.join(BASE_DIR, "rabbitmq", "consumer.py"),
    },
    "kafka": {
        "producer": os.path.join(BASE_DIR, "kafka", "producer.py"),
        "consumer": os.path.join(BASE_DIR, "kafka", "consumer.py"),
    },
    "baseline": {
        "producer": os.path.join(BASE_DIR, "baseline", "producer.py"),
        "consumer": None,  # Baseline não tem consumidor separado
    },
}

def monitor_resources(process):
    cpu_total = 0
    mem_total = 0
    samples = 0
    while process.poll() is None:
        try:
            p = psutil.Process(process.pid)
            cpu_total += p.cpu_percent(interval=0.1)
            mem_total += p.memory_info().rss / (1024 * 1024)
            samples += 1
        except psutil.NoSuchProcess:
            break
    return cpu_total / samples if samples > 0 else 0, mem_total / samples if samples > 0 else 0

def get_container_ids():
    """Obtém os IDs dos contêineres dos brokers"""
    try:
        # Obter lista de contêineres em execução
        result = subprocess.run(['docker', 'ps', '--format', '{{.ID}} {{.Names}}'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return []
        
        containers = {}
        for line in result.stdout.strip().split('\n'):
            if line:
                container_id, name = line.split(' ', 1)
                containers[name] = container_id
        
        # Filtrar apenas os brokers
        broker_containers = {}
        for name, container_id in containers.items():
            if any(broker in name.lower() for broker in ['kafka', 'rabbitmq']):
                broker_containers[name] = container_id
        
        return broker_containers
    except Exception as e:
        print(f"Erro ao obter IDs dos contêineres: {e}")
        return {}

def monitor_docker_resources(monitoring_event, output_file, interval=1.0):
    """
    Monitora recursos dos contêineres Docker em uma thread separada
    
    Args:
        monitoring_event: threading.Event para controlar o monitoramento
        output_file: arquivo CSV para salvar as métricas
        interval: intervalo entre medições em segundos
    """
    print(f"🔍 Iniciando monitoramento de recursos Docker...")
    
    # Obter IDs dos contêineres
    containers = get_container_ids()
    if not containers:
        print("⚠️ Nenhum contêiner de broker encontrado")
        return
    
    print(f"📊 Monitorando {len(containers)} contêineres: {list(containers.keys())}")
    
    # Criar arquivo CSV com cabeçalho
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'container_name', 'container_id', 'cpu_percent', 'memory_usage'])
    
    sample_count = 0

    while not monitoring_event.is_set():
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            
            for container_name, container_id in containers.items():
                try:
                    # Executar docker stats para obter métricas
                    result = subprocess.run([
                        'docker', 'stats', container_id, 
                        '--no-stream', 
                        '--format', '{{.CPUPerc}},{{.MemUsage}}'
                    ], capture_output=True, text=True, timeout=5)
                    
                    if result.returncode == 0:
                        cpu_mem = result.stdout.strip()
                        if ',' in cpu_mem:
                            cpu_percent, mem_usage = cpu_mem.split(',', 1)
                            # Limpar formatação (remover % e unidades)
                            cpu_percent = cpu_percent.replace('%', '').strip()
                            mem_usage = mem_usage.strip()
                            
                            # Salvar no CSV
                            with open(output_file, 'a', newline='') as f:
                                writer = csv.writer(f)
                                writer.writerow([timestamp, container_name, container_id, cpu_percent, mem_usage])
                            
                            sample_count += 1
                        else:
                            print(f"⚠️ Formato inesperado para {container_name}: {cpu_mem}")
                    else:
                        print(f"⚠️ Erro ao obter stats de {container_name}: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    print(f"⚠️ Timeout ao obter stats de {container_name}")
                except Exception as e:
                    print(f"⚠️ Erro ao monitorar {container_name}: {e}")
            
            # Aguardar intervalo
            time.sleep(interval)
            
        except Exception as e:
            print(f"⚠️ Erro no monitoramento: {e}")
            time.sleep(interval)
    
    print(f"✅ Monitoramento finalizado. {sample_count} amostras coletadas.")

def start_resource_monitoring(tech_dir, interval=1.0):
    """
    Inicia o monitoramento de recursos em uma thread separada
    
    Args:
        tech_dir: diretório para salvar o arquivo de monitoramento
        interval: intervalo entre medições em segundos
    
    Returns:
        tuple: (monitoring_event, monitoring_thread)
    """
    # Criar arquivo de monitoramento
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    monitoring_file = os.path.join(tech_dir, f'{timestamp}_docker_resources.csv')
    
    # Criar evento para controlar o monitoramento
    monitoring_event = threading.Event()
    
    # Criar e iniciar thread de monitoramento
    monitoring_thread = threading.Thread(
        target=monitor_docker_resources,
        args=(monitoring_event, monitoring_file, interval),
        daemon=True
    )
    monitoring_thread.start()
    
    return monitoring_event, monitoring_thread

def get_kafka_leader():
    """Identifica o nó líder do cluster Kafka"""
    try:
        # Usar kafka-topics.sh para obter informações do cluster
        result = subprocess.run([
            'docker', 'exec', 'kafka', 'kafka-topics.sh',
            '--bootstrap-server', 'localhost:9092',
            '--describe', '--topic', 'bcc-tcc'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # Para um cluster de 1 nó, o líder é sempre o próprio kafka
            return 'kafka'
        else:
            print(f"Erro ao identificar líder Kafka: {result.stderr}")
            return None
    except Exception as e:
        print(f"Erro ao identificar líder Kafka: {e}")
        return None

def get_rabbitmq_leader():
    """Identifica o nó líder do cluster RabbitMQ"""
    try:
        # Verificar qual nó está ativo como líder
        for node_num in [1, 2, 3]:
            container_name = f'rabbitmq-{node_num}'
            try:
                result = subprocess.run([
                    'docker', 'exec', container_name, 'rabbitmqctl', 'cluster_status'
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0 and 'running_nodes' in result.stdout:
                    # Se o comando funcionou, este é um nó ativo
                    # Para simplificar, vamos considerar o primeiro nó como líder
                    return container_name
            except:
                continue
        
        # Fallback: retornar o primeiro nó
        return 'rabbitmq-1'
    except Exception as e:
        print(f"Erro ao identificar líder RabbitMQ: {e}")
        return 'rabbitmq-1'

def kill_container(container_name):
    """Mata um contêiner Docker"""
    try:
        result = subprocess.run(['docker', 'kill', container_name], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ Contêiner {container_name} foi terminado")
            return True
        else:
            print(f"❌ Erro ao terminar contêiner {container_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erro ao terminar contêiner {container_name}: {e}")
        return False

def wait_for_container_recovery(container_name, max_wait=60):
    """Aguarda um contêiner se recuperar"""
    print(f"⏳ Aguardando recuperação do contêiner {container_name}...")
    start_wait = time.time()
    
    while time.time() - start_wait < max_wait:
        try:
            result = subprocess.run(['docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Status}}'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'Up' in result.stdout:
                recovery_time = time.time() - start_wait
                print(f"✅ Contêiner {container_name} recuperado em {recovery_time:.2f}s")
                return recovery_time
        except:
            pass
        time.sleep(2)
    
    print(f"⚠️ Timeout aguardando recuperação do contêiner {container_name}")
    return max_wait

def run_chaos_experiment(tech, count=100, size=100, rps=None, chaos_delay=10):
    """
    Executa experimento de tolerância a falhas (Chaos Engineering)
    
    Args:
        tech: Tecnologia a testar ('kafka' ou 'rabbitmq')
        count: Número de mensagens
        size: Tamanho das mensagens
        rps: Rate limiting
        chaos_delay: Tempo para aguardar antes de causar falha (segundos)
    """
    print(f"🔥 Iniciando experimento de tolerância a falhas para {tech.upper()}")
    print(f"   • Mensagens: {count}")
    print(f"   • Tamanho: {size} bytes")
    print(f"   • Rate Limiting: {rps or 'unlimited'} RPS")
    print(f"   • Delay para falha: {chaos_delay}s")
    
    # Identificar líder
    if tech == 'kafka':
        leader = get_kafka_leader()
    elif tech == 'rabbitmq':
        leader = get_rabbitmq_leader()
    else:
        print(f"❌ Tecnologia {tech} não suportada para experimento de chaos")
        return
    
    if not leader:
        print(f"❌ Não foi possível identificar líder para {tech}")
        return
    
    print(f"🎯 Líder identificado: {leader}")
    
    # Criar diretório para logs de chaos
    chaos_dir = os.path.join(LOG_DIR, tech, 'chaos')
    os.makedirs(chaos_dir, exist_ok=True)
    
    # Timestamps para medição
    experiment_start = time.time()
    chaos_start = None
    chaos_end = None
    recovery_start = None
    recovery_end = None
    
    # Iniciar produtor em thread separada
    producer_thread = None
    producer_results = {'success': False, 'errors': [], 'messages_sent': 0}
    
    def producer_worker():
        try:
            cmd = ["python", TECHS[tech]["producer"], str(count), str(size)]
            if rps:
                cmd.append(str(rps))
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            producer_results['success'] = result.returncode == 0
            producer_results['stdout'] = result.stdout
            producer_results['stderr'] = result.stderr
        except subprocess.TimeoutExpired:
            producer_results['success'] = False
            producer_results['errors'].append("Timeout")
        except Exception as e:
            producer_results['success'] = False
            producer_results['errors'].append(str(e))
    
    # Iniciar produtor
    print(f"🚀 Iniciando produtor...")
    producer_thread = threading.Thread(target=producer_worker, daemon=True)
    producer_thread.start()
    
    # Aguardar delay antes de causar falha
    print(f"⏰ Aguardando {chaos_delay}s antes de causar falha...")
    time.sleep(chaos_delay)
    
    # Causar falha no líder
    print(f"💥 Causando falha no líder {leader}...")
    chaos_start = time.time()
    
    if kill_container(leader):
        chaos_end = time.time()
        print(f"🔥 Falha causada em {chaos_end - chaos_start:.2f}s")
        
        # Aguardar um pouco para ver o impacto
        time.sleep(5)
        
        # Aguardar recuperação
        recovery_start = time.time()
        recovery_time = wait_for_container_recovery(leader, max_wait=60)
        recovery_end = time.time()
        
        print(f"🔄 Tempo de recuperação: {recovery_time:.2f}s")
    else:
        print(f"❌ Falha ao causar falha no líder {leader}")
        return
    
    # Aguardar produtor finalizar
    print(f"⏳ Aguardando produtor finalizar...")
    producer_thread.join(timeout=60)
    
    experiment_end = time.time()
    
    # Calcular métricas
    downtime = chaos_end - chaos_start if chaos_end and chaos_start else 0
    recovery_time = recovery_end - recovery_start if recovery_end and recovery_start else 0
    total_experiment_time = experiment_end - experiment_start
    
    # Salvar resultados do experimento
    chaos_results_file = os.path.join(chaos_dir, f'{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}_chaos_results.csv')
    with open(chaos_results_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['metric', 'value'])
        writer.writerow(['leader_container', leader])
        writer.writerow(['total_messages', count])
        writer.writerow(['message_size', size])
        writer.writerow(['rps', rps or 'unlimited'])
        writer.writerow(['chaos_delay_sec', chaos_delay])
        writer.writerow(['downtime_sec', downtime])
        writer.writerow(['recovery_time_sec', recovery_time])
        writer.writerow(['total_experiment_time_sec', total_experiment_time])
        writer.writerow(['producer_success', producer_results['success']])
        writer.writerow(['messages_sent', producer_results['messages_sent']])
    
    # Exibir resultados
    print(f"\n📊 RESULTADOS DO EXPERIMENTO DE TOLERÂNCIA A FALHAS:")
    print(f"   • Líder testado: {leader}")
    print(f"   • Tempo de indisponibilidade: {downtime:.2f}s")
    print(f"   • Tempo de recuperação: {recovery_time:.2f}s")
    print(f"   • Tempo total do experimento: {total_experiment_time:.2f}s")
    print(f"   • Produtor bem-sucedido: {producer_results['success']}")
    print(f"   • Resultados salvos em: {chaos_results_file}")
    
    return {
        'leader': leader,
        'downtime': downtime,
        'recovery_time': recovery_time,
        'total_time': total_experiment_time,
        'producer_success': producer_results['success']
    }

def run_producer_process(tech, producer_id, messages_per_producer, message_size, rps=None):
    """Executa um processo produtor individual"""
    try:
        cmd = ["python", TECHS[tech]["producer"], str(messages_per_producer), str(message_size)]
        if rps:
            cmd.append(str(rps))
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {
            "producer_id": producer_id,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "producer_id": producer_id,
            "success": False,
            "stdout": "",
            "stderr": "Timeout expired"
        }
    except Exception as e:
        return {
            "producer_id": producer_id,
            "success": False,
            "stdout": "",
            "stderr": str(e)
        }

def run_consumer_process(tech, consumer_id, expected_messages):
    """Executa um processo consumidor individual"""
    try:
        cmd = ["python", TECHS[tech]["consumer"], str(expected_messages)]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return {
            "consumer_id": consumer_id,
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {
            "consumer_id": consumer_id,
            "success": False,
            "stdout": "",
            "stderr": "Timeout expired"
        }
    except Exception as e:
        return {
            "consumer_id": consumer_id,
            "success": False,
            "stdout": "",
            "stderr": str(e)
        }

def run_benchmark(tech, count=1000, size=200, num_producers=1, num_consumers=1, rps=None):
    print(f"\n▶️ Iniciando benchmark para {tech.upper()}...")
    print(f"   • Produtores: {num_producers}")
    print(f"   • Consumidores: {num_consumers}")
    print(f"   • Mensagens totais: {count}")
    print(f"   • Tamanho da mensagem: {size} bytes")
    if rps:
        print(f"   • Rate Limiting: {rps} RPS")
    
    tech_dir = os.path.join(LOG_DIR, tech)
    os.makedirs(tech_dir, exist_ok=True)

    # Iniciar monitoramento de recursos Docker (exceto para baseline)
    monitoring_event = None
    monitoring_thread = None
    if tech != "baseline":
        print(f"   • Iniciando monitoramento de recursos Docker...")
        monitoring_event, monitoring_thread = start_resource_monitoring(tech_dir, interval=1.0)
        time.sleep(1)  # Aguardar thread de monitoramento inicializar

    # Calcular mensagens por produtor
    messages_per_producer = count // num_producers
    remaining_messages = count % num_producers
    
    # Iniciar consumidores (exceto para baseline)
    if tech != "baseline":
        print(f"   • Iniciando {num_consumers} consumidor(es)...")
        consumer_processes = []
        with Pool(processes=num_consumers) as pool:
            consumer_args = [(tech, i, count) for i in range(num_consumers)]
            consumer_results = pool.starmap(run_consumer_process, consumer_args)
        
        # Aguardar um pouco para os consumidores se conectarem
        time.sleep(3)
    else:
        print(f"   • Baseline HTTP - sem consumidor separado")
        consumer_results = [{"success": True, "consumer_id": 0}]  # Mock para baseline
    
    # Iniciar produtores
    print(f"   • Iniciando {num_producers} produtor(es)...")
    start_time = time.time()
    
    with Pool(processes=num_producers) as pool:
        producer_args = []
        for i in range(num_producers):
            # Distribuir mensagens restantes entre os primeiros produtores
            messages_for_this_producer = messages_per_producer + (1 if i < remaining_messages else 0)
            producer_args.append((tech, i, messages_for_this_producer, size, rps))
        
        producer_results = pool.starmap(run_producer_process, producer_args)
    
    end_time = time.time()
    
    # Verificar resultados dos produtores
    successful_producers = sum(1 for result in producer_results if result["success"])
    print(f"   • Produtores bem-sucedidos: {successful_producers}/{num_producers}")
    
    # Verificar resultados dos consumidores
    successful_consumers = sum(1 for result in consumer_results if result["success"])
    print(f"   • Consumidores bem-sucedidos: {successful_consumers}/{num_consumers}")

    # Coletar métricas de latência de todos os arquivos de log
    latency_files = glob.glob(os.path.join(tech_dir, "*_latency.csv"))
    latencies = []
    
    for latency_file in latency_files:
        try:
            with open(latency_file, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    latencies.append(float(row["latency_seconds"]))
        except Exception as e:
            print(f"   • Erro ao ler arquivo de latência {latency_file}: {e}")

    # Coletar métricas de throughput dos summaries
    summary_files = glob.glob(os.path.join(tech_dir, "*_summary.csv"))
    total_throughput = 0
    total_messages_sent = 0
    
    for summary_file in summary_files:
        try:
            with open(summary_file, newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["metric"] == "total_sent":
                        total_messages_sent += int(row["value"])
                    elif row["metric"] == "actual_rps" and rps:
                        total_throughput += float(row["value"])
        except Exception as e:
            print(f"   • Erro ao ler arquivo de summary {summary_file}: {e}")

    # Calcular métricas
    latency_avg = mean(latencies) if latencies else 0
    latency_50 = median(latencies) if latencies else 0
    latency_95 = quantiles(latencies, n=100)[94] if len(latencies) >= 100 else 0
    latency_99 = quantiles(latencies, n=100)[98] if len(latencies) >= 100 else 0
    
    duration = end_time - start_time
    if not rps:
        throughput = total_messages_sent / duration if duration > 0 else 0
    else:
        throughput = total_throughput

    # Salvar resultados
    csv_path = os.path.join(tech_dir, "benchmark_results.csv")
    write_header = not os.path.exists(csv_path)

    with open(csv_path, mode="a", newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow([
                "timestamp", "messages", "message_size", "num_producers", "num_consumers",
                "rps", "latency_avg", "latency_50", "latency_95", "latency_99", 
                "throughput", "successful_producers", "successful_consumers"
            ])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            count, size, num_producers, num_consumers,
            rps or "unlimited", round(latency_avg, 6),
            round(latency_50, 6), round(latency_95, 6), round(latency_99, 6),
            round(throughput, 2), successful_producers, successful_consumers
        ])

    # Finalizar monitoramento de recursos
    if monitoring_event and monitoring_thread:
        print(f"   • Finalizando monitoramento de recursos...")
        monitoring_event.set()  # Sinalizar para parar o monitoramento
        monitoring_thread.join(timeout=5)  # Aguardar thread finalizar

    print(f"✅ Benchmark {tech.upper()} finalizado:")
    print(f"   • Latência média: {latency_avg:.4f}s")
    print(f"   • Throughput: {throughput:.2f} msgs/s")
    print(f"   • Mensagens processadas: {len(latencies)}")
    print(f"   • Duração total: {duration:.2f}s")

def run_all_benchmarks(count, size, num_producers=1, num_consumers=1, rps=None):
    # Executar para RabbitMQ, Kafka e Baseline
    for tech in ["rabbitmq", "kafka", "baseline"]:
        run_benchmark(tech, count=count, size=size, num_producers=num_producers, 
                     num_consumers=num_consumers, rps=rps)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executa benchmark comparativo RabbitMQ vs Kafka")
    parser.add_argument("--count", type=int, default=1000, help="Quantidade de mensagens")
    parser.add_argument("--size", type=int, default=200, help="Tamanho de cada mensagem (bytes)")
    parser.add_argument("--producers", type=int, default=1, help="Número de produtores concorrentes")
    parser.add_argument("--consumers", type=int, default=1, help="Número de consumidores concorrentes")
    parser.add_argument("--rps", type=int, default=None, help="Rate Limiting (Requests Per Second)")
    parser.add_argument("--only", choices=["kafka", "rabbitmq", "baseline", "both"], default="both", help="Executar apenas para uma tecnologia")
    parser.add_argument("--chaos", action="store_true", help="Executar experimento de tolerância a falhas (Chaos Engineering)")
    parser.add_argument("--chaos-delay", type=int, default=10, help="Delay em segundos antes de causar falha (padrão: 10)")
    args = parser.parse_args()

    if args.chaos:
        print(f"🔥 Iniciando experimento de tolerância a falhas (Chaos Engineering):")
        print(f"   • Tecnologias: {args.only}")
        print(f"   • Mensagens: {args.count}")
        print(f"   • Tamanho: {args.size} bytes")
        print(f"   • Rate Limiting: {args.rps or 'unlimited'} RPS")
        print(f"   • Delay para falha: {args.chaos_delay}s")
        
        if args.only == "both":
            # Executar experimento de chaos para Kafka e RabbitMQ
            for tech in ["kafka", "rabbitmq"]:
                print(f"\n{'='*60}")
                run_chaos_experiment(tech, count=args.count, size=args.size, 
                                   rps=args.rps, chaos_delay=args.chaos_delay)
        else:
            if args.only in ["kafka", "rabbitmq"]:
                run_chaos_experiment(args.only, count=args.count, size=args.size, 
                                   rps=args.rps, chaos_delay=args.chaos_delay)
            else:
                print(f"❌ Tecnologia {args.only} não suportada para experimento de chaos")
    else:
        print(f"🚀 Iniciando benchmark com configuração:")
        print(f"   • Tecnologias: {args.only}")
        print(f"   • Mensagens: {args.count}")
        print(f"   • Tamanho: {args.size} bytes")
        print(f"   • Produtores: {args.producers}")
        print(f"   • Consumidores: {args.consumers}")
        if args.rps:
            print(f"   • Rate Limiting: {args.rps} RPS")

        if args.only == "both":
            run_all_benchmarks(count=args.count, size=args.size, 
                              num_producers=args.producers, num_consumers=args.consumers, rps=args.rps)
        else:
            run_benchmark(args.only, count=args.count, size=args.size, 
                         num_producers=args.producers, num_consumers=args.consumers, rps=args.rps)

        print("\n📊 Resultados salvos em logs/<tech>/benchmark_results.csv")