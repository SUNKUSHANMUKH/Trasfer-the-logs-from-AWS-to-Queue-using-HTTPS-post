FROM python:3.10-slim
WORKDIR /app
COPY sqs_puller.py .
RUN pip install boto3 kafka-python
CMD ["python", "sqs_puller.py"]
