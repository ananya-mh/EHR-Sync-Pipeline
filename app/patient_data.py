from kafka import KafkaProducer
import json
import time
from faker import Faker
import random
import uuid

fake = Faker()

conditions = ["diabetes", "hypertension", "asthma", "heart disease", "cancer"]

producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(0, 10, 1)
)

while True:
    patient = {
        "id": str(uuid.uuid4()),  # generate UUID as string
        "name": fake.name(),
        "age": random.randint(0, 120),  # matches CHECK constraint
        "condition": random.choice(conditions)
    }
    producer.send("ehr.patient.events", value=patient)
    print("Sent:", patient)
    time.sleep(2)
