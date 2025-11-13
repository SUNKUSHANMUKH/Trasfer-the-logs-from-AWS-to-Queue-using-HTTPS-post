THIS IS WHAT WE ARE MAKING:

           [AWS CloudTrail]
                 |
                 v
          [AWS EventBridge]
                 |
                 v
          [AWS SQS Queue]
                 |
                 v (boto3 inside Docker)
       +-----------------------------+
       |  SQS Puller Docker App      |
       |  Reads SQS → Sends to Kafka |
       +-----------------------------+
                 |
                 v
       +-----------------------------+
       |  Kafka + Flask Docker App   |
       |  Accepts HTTP POST logs     |
       |  and stores all logs inside |
       +-----------------------------+
 


PART 1 — PREPARATION ON YOUR WINDOWS PC

🪜 Step 1: Install these tools

Tool

Purpose

Download

Docker Desktop

Runs your containers

https://www.docker.com/products/docker-desktop

Git

Helps with files

https://git-scm.com/download/win

OpenSSL

For HTTPS certs

Win64 OpenSSL Light

AWS Account

You need this for CloudTrail/SQS

https://aws.amazon.com

👉 After installation, start Docker Desktop.
You should see the 🐳 whale icon on your taskbar — that means Docker is running.



PART 2 — SETUP ON AWS CLOUD

We’ll create:

SQS Queue

CloudTrail Trail

EventBridge Rule (sends CloudTrail → SQS)



Step 1: Create an SQS Queue

Go to the AWS Console.

In the search bar, type SQS → click Simple Queue Service.

Click Create queue.

Choose Standard Queue.

Enter Queue name:

my-cloudtrail-queue

Scroll down → keep all defaults.

Click Create queue.

Copy these:

Queue URL — looks like
https://sqs.ap-south-1.amazonaws.com/123456789012/my-cloudtrail-queue

Queue ARN — looks like
arn:aws:sqs:ap-south-1:123456789012:my-cloudtrail-queue

✅ Keep them safe — you’ll use them later in Docker.



🌲 Step 2: Enable CloudTrail → EventBridge

Go to AWS Console → CloudTrail.

In the left panel, click Trails.

If you already have one trail (like default), click on it.

Under General details, look for this option:

“Send events to EventBridge”

✅ Turn it ON.

Click Save changes.

If you don’t have a trail:

Click Create trail.

Trail name: my-trail

Check ✅ “Create a new S3 bucket” (CloudTrail needs it).

Check ✅ “Send events to EventBridge”.

Click Next → Create trail.

✅ Now CloudTrail is configured to push all AWS API logs to EventBridge.



🔔 Step 3: Create EventBridge Rule → SQS

Go to AWS Console → EventBridge.

In the left sidebar, click Rules.

Click Create rule.

Rule name: cloudtrail-to-sqs

Event source: Choose Event pattern.

Event pattern → Choose “Custom pattern (JSON)”.

Paste this JSON:



{
 "source": ["aws.cloudtrail"],
 "detail-type": ["AWS API Call via CloudTrail"]
}


This matches all CloudTrail events.

Click Next.

Under Targets:

Choose SQS queue.

From dropdown, pick my-cloudtrail-queue.

If it asks to create a new role, choose Yes, create new.

Click Next → Next → Create rule.

✅ Done!
Now every CloudTrail event (like EC2 start, S3 bucket create, IAM changes, etc.) will go to your SQS queue.





🧩 Step 4: Verify SQS Permissions (optional, only if needed)

If EventBridge fails to send to SQS (error in console later), fix with this queue policy:

Go to SQS → my-cloudtrail-queue → Permissions tab(QUEUE WILL WRITTEN) → Edit Policy.



Now we’ll add a new permission block to allow EventBridge to send CloudTrail messages into your queue.

Copy this JSON block 👇 and paste it inside the Statement array, right after the existing one.


Paste this (edit your values):

{
 "Sid": "AllowEventBridgeToSendMessages",
 "Effect": "Allow",
 "Principal": {
   "Service": "events.amazonaws.com"
 },
 "Action": "sqs:SendMessage",
 "Resource": "arn:aws:sqs:ap-south-1:608520608063:my-cloudtrail-queue",
 "Condition": {
   "ArnEquals": {
     "aws:SourceArn": "arn:aws:events:ap-south-1:608520608063:rule/cloudtrail-to-sqs"
   }
 }
}




THEN,

Your full policy will look like this 👇

{
 "Version": "2012-10-17",
 "Id": "__default_policy_ID",
 "Statement": [
   {
     "Sid": "__owner_statement",
     "Effect": "Allow",
     "Principal": {
       "AWS": "arn:aws:iam::608520608063:root"
     },
     "Action": "SQS:*",
     "Resource": "arn:aws:sqs:ap-south-1:608520608063:my-cloudtrail-queue"
   },
   {
     "Sid": "AllowEventBridgeToSendMessages",
     "Effect": "Allow",
     "Principal": {
       "Service": "events.amazonaws.com"
     },
     "Action": "sqs:SendMessage",
     "Resource": "arn:aws:sqs:ap-south-1:608520608063:my-cloudtrail-queue",
     "Condition": {
       "ArnEquals": {
         "aws:SourceArn": "arn:aws:events:ap-south-1:608520608063:rule/cloudtrail-to-sqs"
       }
     }
   }
 ]
}





Step 5: Test Your Setup (CloudTrail → SQS)

Let’s trigger a test AWS event (like creating an S3 bucket):

Step 5.1 — Trigger an event:

Go to S3 → Create bucket
Name it:

test-bucket-sunku123

Click Create bucket.

Step 5.2 — Check SQS:

Go back to SQS → my-cloudtrail-queue

Click Send and receive messages

Click Poll for messages

🟢 You should now see messages appearing!

Go to S3 → Create bucket → name it something like:
test-cloudtrail-bucket-<yourname> → click Create bucket.

Wait 30–60 seconds.

Go to SQS → my-cloudtrail-queue → Send and receive messages.

Click Poll for messages.



CloudTrail Logs to Kafka via SQS and Flask



🔹 Objective

The goal of this project was to create an automated pipeline that transfers AWS CloudTrail logs to an Apache Kafka topic using:

AWS CloudTrail

Amazon SQS

Python (Flask, Boto3, Requests)

Docker & Docker Compose

EC2 instances for deployment



🧭 High-Level Architecture

CloudTrail → SQS → EC2 Instance #1 (SQS Puller) → EC2 Instance #2 (Flask + Kafka)


Component

Function

CloudTrail

Captures AWS account activity logs

SQS

Stores logs in a message queue

EC2 #1 – SQS Puller

Polls SQS, reads messages, and sends them to Flask over HTTP

EC2 #2 – Flask + Kafka

Receives HTTP POSTs and pushes them into Kafka topic

Kafka Broker

Stores and streams CloudTrail events in topic cloudtrail-logs



💻 Tools & Technologies

AWS Services: CloudTrail, SQS, EC2

Programming Language: Python 3.10

Libraries: boto3, requests, kafka-python, flask

Containers: Docker, Docker Compose

OS: Ubuntu 22.04 LTS



⚙️ Setup Flow (Step-by-Step)

🔸 1. Create SQS Queue in AWS Console

Queue name: my-cloudtrail-queue

Note the Queue URL

https://sqs.ap-south-1.amazonaws.com/<account-id>/my-cloudtrail-queue

Attach IAM policy to user/role with these permissions:

{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"],
      "Resource": "arn:aws:sqs:ap-south-1:<account-id>:my-cloudtrail-queue"
    }
  ]
}



🔸 2. Launch Two EC2 Instances

Instance

Role

Purpose

EC2 #1

SQS Puller

Pulls messages from SQS and sends to Flask

EC2 #2

Flask + Kafka

Hosts Flask API and Kafka broker



🔸 3. Install Docker & Docker Compose

sudo apt update
sudo apt install docker.io -y
sudo apt install docker-compose-plugin -y
sudo systemctl enable docker
sudo systemctl start docker




🔸 4. Setup Kafka + Flask (EC2 #2)

📁 Folder structure

kafka-http/
 ├── Dockerfile
 ├── app.py
 ├── docker-compose.yml


✅ Correct docker-compose.yml

services:
  kafka:
    image: bitnami/kafka:3.7.0
    container_name: kafka-broker
    environment:
      - KAFKA_ENABLE_KRAFT=yes
      - KAFKA_CFG_NODE_ID=1
      - KAFKA_CFG_PROCESS_ROLES=broker,controller
      - KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093
      - KAFKA_CFG_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092
      - KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=1@kafka:9093
      - ALLOW_PLAINTEXT_LISTENER=yes
    ports:
      - "9092:9092"

  kafka-http:
    build: .
    container_name: kafka-http
    ports:
      - "5000:5000"
    depends_on:
      - kafka
    environment:
      - KAFKA_BOOTSTRAP=kafka:9092


✅ Flask App (app.py)

from flask import Flask, request, jsonify
from kafka import KafkaProducer
import json, os, time

app = Flask(__name__)
time.sleep(15)

producer = KafkaProducer(
    bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP"),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

@app.route('/logs', methods=['POST'])
def receive_logs():
    data = request.get_json()
    producer.send('cloudtrail-logs', value=data)
    return jsonify({"status": "Message sent to Kafka"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)


✅ Commands Used:

sudo docker compose up -d --build
sudo docker ps
sudo docker logs -f kafka-http




🔸 5. Setup SQS Puller (EC2 #1)

📁 Folder structure

sqs-puller/
 ├── Dockerfile
 ├── app.py
 ├── .env
 ├── docker-compose.yml


✅ .env

AWS_ACCESS_KEY_ID=xxxxxxxxxx
AWS_SECRET_ACCESS_KEY=xxxxxxxxxx
AWS_REGION=ap-south-1
SQS_QUEUE_URL=https://sqs.ap-south-1.amazonaws.com/<account-id>/my-cloudtrail-queue
FLASK_ENDPOINT=http://<Kafka-EC2-Public-IP>:5000/logs




✅ Dockerfile

FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install boto3 requests
CMD ["python", "-u", "app.py"]


🔥 Fix applied here:
Initially, logs weren’t showing because Python buffered output — fixed by adding the -u flag for unbuffered logging.



✅ docker-compose.yml

services:
  sqs-puller:
    build: .
    container_name: sqs-puller
    restart: unless-stopped
    env_file:
      - ./.env


⚠️ Earlier Mistake:
I had env_file: ./ .env (with an extra space).
Fix: Corrected it to env_file: ./.env



✅ app.py

import boto3, requests, json, os, time

sqs = boto3.client(
    'sqs',
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

sqs_url = os.getenv("SQS_QUEUE_URL")
flask_endpoint = os.getenv("FLASK_ENDPOINT")

print("✅ SQS Puller started... waiting for messages")

while True:
    response = sqs.receive_message(
        QueueUrl=sqs_url,
        MaxNumberOfMessages=1,
        WaitTimeSeconds=10
    )

    if 'Messages' in response:
        for message in response['Messages']:
            body = json.loads(message['Body'])
            print(f"📥 Received message: {body}")

            try:
                r = requests.post(flask_endpoint, json=body)
                if r.status_code == 200:
                    print("📤 Sent to Flask API successfully")
                else:
                    print(f"❌ Failed to send, status code: {r.status_code}")
            except Exception as e:
                print(f"⚠️ Error sending to Flask: {e}")

            sqs.delete_message(
                QueueUrl=sqs_url,
                ReceiptHandle=message['ReceiptHandle']
            )
            print("🗑️ Deleted message from SQS")

    time.sleep(1)




🔸 6. Build and Run Containers

sudo docker compose down -v
sudo docker compose up -d --build
sudo docker logs -f sqs-puller


✅ Fix:
Initially, no logs appeared — fixed by adding -u (unbuffered mode) in CMD line inside Dockerfile.



🔸 7. Verify Connectivity

Send a message from AWS SQS Console:

{
  "event": "TestEvent",
  "message": "Hello from AWS Console!",
  "timestamp": "2025-11-12T13:45:00Z"
}


✅ Output in sqs-puller logs:

📥 Received message: {...}
📤 Sent to Flask API successfully
🗑️ Deleted message from SQS


✅ Output in Kafka consumer:

sudo docker exec -it kafka-broker rpk topic consume cloudtrail-logs --brokers localhost:9092


Shows:

{"event": "TestEvent", "message": "Hello from AWS Console!", "timestamp": "2025-11-12T13:45:00Z"}




🧠 Common Mistakes & Fixes

Issue

Root Cause

Fix

.env not found

Extra space (./ .env)

Corrected to ./.env

No logs showing

Buffered Python output

Added -u flag in CMD

Invalid URL 'None'

Missing FLASK_ENDPOINT

Fixed .env variable

Kafka not connecting

Kafka broker not ready

Added time.sleep(15) in Flask

Permission denied on SQS

Missing IAM policy

Added sqs:ReceiveMessage, sqs:DeleteMessage

Docker version issue

Old Compose v1

Installed docker-compose-plugin



🧩 Verification Commands

Purpose

Command

Check running containers

sudo docker ps

Follow logs

sudo docker logs -f <container>

Consume Kafka topic

sudo docker exec -it kafka-broker rpk topic consume cloudtrail-logs --brokers localhost:9092

Restart containers

sudo docker compose down -v && sudo docker compose up -d --build

Check env vars inside container

sudo docker exec -it sqs-puller bash && echo $FLASK_ENDPOINT



⚡ Final Outcome

Real-time AWS CloudTrail logs now flow through SQS → Flask → Kafka.

System automatically processes and deletes messages.

Containers are lightweight, restart automatically, and fully automated.



























