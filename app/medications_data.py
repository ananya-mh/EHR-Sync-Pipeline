from kafka import KafkaProducer
import json
import time
import uuid
from faker import Faker
import random
from datetime import datetime, timedelta

fake = Faker()

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(0, 10, 1)
)

# Some common drugs
medications = [
    ("AMOX", "Amoxicillin", "500mg", "oral"),
    ("IBU", "Ibuprofen", "200mg", "oral"),
    ("MET", "Metformin", "850mg", "oral"),
    ("LIS", "Lisinopril", "10mg", "oral"),
    ("INS", "Insulin", "20 units", "subcutaneous")
]

while True:
    drug_code, drug_name, dose, route = random.choice(medications)
    start_time = datetime.utcnow()
    end_time = start_time + timedelta(days=random.randint(1, 30))

    medication = {
        "id": str(uuid.uuid4()),
        "patient_id": str(uuid.uuid4()),  # in real case, match existing patient IDs
        "drug_code": drug_code,
        "drug_name": drug_name,
        "dose": dose,
        "route": route,
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat(),
        "ingested_at": datetime.utcnow().isoformat()
    }

    producer.send("ehr.medications.events", value=medication)
    print("Sent medication:", medication)
    time.sleep(2)
