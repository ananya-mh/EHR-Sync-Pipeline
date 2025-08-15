from kafka import KafkaProducer
import json
import time
from faker import Faker
import random

fake = Faker()

conditions = ["diabetes", "hypertension", "asthma", "heart disease", "cancer"]

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(0, 10, 1)
)

while True:
    patient = {
        "id": fake.random_int(min=1, max=10000),
        "name": fake.name(),
        "age": random.randint(1, 100),
        "condition": random.choice(conditions)
    }
    producer.send("ehr.patient.events", value=patient)
    print("Sent:", patient)
    time.sleep(2)
