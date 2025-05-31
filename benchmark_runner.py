# benchmark_runner.py
import subprocess
import argparse

def run_test(tech, count, size):
    if tech == "rabbitmq":
        print("⏳ Executando teste com RabbitMQ...")
        subprocess.run(["python", "rabbitmq/producer.py", str(count), str(size)])
        subprocess.run(["python", "rabbitmq/consumer.py"])
    elif tech == "kafka":
        print("⏳ Executando teste com Apache Kafka...")
        subprocess.run(["python", "kafka/producer.py", str(count), str(size)])
        subprocess.run(["python", "kafka/consumer.py"])
    else:
        print("❌ Tecnologia não suportada. Use 'rabbitmq' ou 'kafka'.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Executar testes de benchmark de mensageria.")
    parser.add_argument("tech", choices=["rabbitmq", "kafka"], help="Tecnologia de mensageria")
    parser.add_argument("count", type=int, help="Quantidade de mensagens a serem enviadas")
    parser.add_argument("size", type=int, help="Tamanho em bytes de cada mensagem")

    args = parser.parse_args()
    run_test(args.tech, args.count, args.size)
