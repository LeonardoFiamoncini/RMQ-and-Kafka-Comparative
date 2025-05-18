from flask import Flask, render_template, redirect, url_for, send_from_directory
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send-rabbitmq')
def send_rabbitmq():
    try:
        subprocess.run(["python3", "../rabbitmq/producer.py", "100", "200"], check=True)
    except subprocess.CalledProcessError as e:
        return f"Erro ao executar o producer: {e}", 500
    return redirect(url_for('index'))

@app.route('/send-kafka')
def send_kafka():
    return "Funcionalidade do Apache Kafka ainda não implementada.", 501

@app.route('/media/<path:filename>')
def media(filename):
    return send_from_directory('media', filename)

if __name__ == '__main__':
    app.run(debug=True)