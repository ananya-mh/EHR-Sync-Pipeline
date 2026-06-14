"""Producer that generates synthetic patient events to Kafka."""

import json
import random
import time
import uuid

from faker import Faker
from kafka import KafkaProducer

from src.config.settings import settings

fake = Faker()

CONDITIONS = ["diabetes", "hypertension", "asthma", "heart disease", "cancer"]


def main() -> None:
    """Continuously produce random patient events to Kafka."""
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        api_version=(0, 10, 1),
    )

    while True:
        patient = {
            "id": str(uuid.uuid4()),
            "name": fake.name(),
            "age": random.randint(0, 120),
            "condition": random.choice(CONDITIONS),
        }
        producer.send("ehr.patient.events", value=patient)
        print("Sent:", patient)
        time.sleep(2)


if __name__ == "__main__":
    main()
