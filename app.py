from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json, os

app = Flask(__name__)
producer = KafkaProducer(
    bootstrap_servers=[os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")],
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/logs', methods=['POST'])
def receive_logs():
    data = request.get_json()
    producer.send('cloudtrail-logs', value=data)
    producer.flush()
    return jsonify({"status": "success"}), 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
