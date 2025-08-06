from kafka import KafkaProducer
import json
import time

# Initialize Kafka producer
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(0, 10, 1)
)

# List of sample patient events to send
patients = [
    {"id": 1, "name": "Alice", "age": 30, "condition": "diabetes"},
    {"id": 2, "name": "Bob", "age": 45, "condition": "hypertension"},
    {"id": 3, "name": "Charlie", "age": 25, "condition": "asthma"},
]

# Send each patient event once with delay
for patient in patients:
    # producer.send("ehr.patient.events", value=patient)
    producer.send("ehr.patient.events", value=patient).get(timeout=10)
    print("Sent:", patient)
    time.sleep(2)  # optional delay between messages

# Ensure all messages are sent
producer.flush()
