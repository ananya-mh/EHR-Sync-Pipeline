from kafka import KafkaProducer
import json
import time
import uuid
from faker import Faker
import random
from datetime import datetime

fake = Faker()

producer = KafkaProducer(
    bootstrap_servers=['kafka:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(0, 10, 1)
)

# Some common lab tests
lab_tests = [
    ("HB", "Hemoglobin", "g/dL"),
    ("WBC", "White Blood Cell Count", "10^3/uL"),
    ("GLU", "Glucose", "mg/dL"),
    ("CR", "Creatinine", "mg/dL"),
    ("CHOL", "Cholesterol", "mg/dL")
]

while True:
    test_code, test_name, unit = random.choice(lab_tests)
    lab_result = {
        "id": str(uuid.uuid4()),
        "patient_id": str(uuid.uuid4()),  # in real case, match existing patient IDs
        "test_code": test_code,
        "test_name": test_name,
        "value": round(random.uniform(1, 200), 2),
        "unit": unit,
        "result_time": datetime.utcnow().isoformat()
    }

    producer.send("ehr.labresults.events", value=lab_result)
    print("Sent lab result:", lab_result)
    time.sleep(2)
