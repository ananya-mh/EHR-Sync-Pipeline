"""Producer that generates synthetic medication events to Kafka."""

import json
import random
import time
import uuid
from datetime import datetime, timedelta, timezone

from kafka import KafkaProducer

from src.config.settings import settings

MEDICATIONS = [
    ("AMOX", "Amoxicillin", "500mg", "oral"),
    ("IBU", "Ibuprofen", "200mg", "oral"),
    ("MET", "Metformin", "850mg", "oral"),
    ("LIS", "Lisinopril", "10mg", "oral"),
    ("INS", "Insulin", "20 units", "subcutaneous"),
]


def main() -> None:
    """Continuously produce random medication events to Kafka."""
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        api_version=(0, 10, 1),
    )

    while True:
        drug_code, drug_name, dose, route = random.choice(MEDICATIONS)
        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(days=random.randint(1, 30))

        medication = {
            "id": str(uuid.uuid4()),
            "patient_id": str(uuid.uuid4()),
            "drug_code": drug_code,
            "drug_name": drug_name,
            "dose": dose,
            "route": route,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }
        producer.send("ehr.medications.events", value=medication)
        print("Sent medication:", medication)
        time.sleep(2)


if __name__ == "__main__":
    main()
