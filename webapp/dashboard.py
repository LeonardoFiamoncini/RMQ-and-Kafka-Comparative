from flask import Flask, render_template
import os
import pandas as pd
from glob import glob

app = Flask(__name__, template_folder="templates", static_folder="static")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def load_summary_data():
    data = {"rabbitmq": [], "kafka": []}
    for tech in data.keys():
        summary_files = glob(os.path.join(BASE_DIR, "logs", tech, "*_summary.csv"))
        for file in summary_files:
            df = pd.read_csv(file)
            for _, row in df.iterrows():
                data[tech].append({
                    "timestamp": row["timestamp"],
                    "tech": tech,
                    "avg_latency_sec": row["avg_latency_sec"],
                    "throughput_msgs_per_sec": row["throughput_msgs_per_sec"]
                })
    return data

def compute_aggregates(data):
    aggregates = {}
    for tech, records in data.items():
        if records:
            latencies = [r["avg_latency_sec"] for r in records]
            throughputs = [r["throughput_msgs_per_sec"] for r in records]
            aggregates[tech] = {
                "avg_latency": sum(latencies) / len(latencies),
                "avg_throughput": sum(throughputs) / len(throughputs),
                "min_latency": min(latencies),
                "max_throughput": max(throughputs),
                "runs": len(records)
            }
        else:
            aggregates[tech] = {
                "avg_latency": 0,
                "avg_throughput": 0,
                "min_latency": 0,
                "max_throughput": 0,
                "runs": 0
            }
    return aggregates

@app.route("/dashboard")
def dashboard():
    summary_data = load_summary_data()
    aggregates = compute_aggregates(summary_data)
    return render_template("dashboard.html", data=summary_data, aggregates=aggregates)

if __name__ == "__main__":
    app.run(debug=True)
