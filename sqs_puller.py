import boto3, json, time, os
from kafka import KafkaProducer

QUEUE_URL = os.getenv("SQS_QUEUE_URL")
REGION = os.getenv("AWS_REGION", "ap-south-1")
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "kafka:9092")

sqs = boto3.client("sqs", region_name=REGION)
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_BOOTSTRAP],
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("✅ SQS Puller started...")

while True:
    response = sqs.receive_message(QueueUrl=QUEUE_URL, MaxNumberOfMessages=10, WaitTimeSeconds=10)
    for msg in response.get("Messages", []):
        body = json.loads(msg["Body"])
        producer.send("cloudtrail-logs", value=body)
        sqs.delete_message(QueueUrl=QUEUE_URL, ReceiptHandle=msg["ReceiptHandle"])
        print("✅ Sent message to Kafka")
    time.sleep(3)
