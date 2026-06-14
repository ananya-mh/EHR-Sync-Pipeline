"""Producer that generates synthetic lab result events to Kafka."""

import json
import random
import time
import uuid
from datetime import datetime, timezone

from kafka import KafkaProducer

from src.config.settings import settings

LAB_TESTS = [
    ("HB", "Hemoglobin", "g/dL"),
    ("WBC", "White Blood Cell Count", "10^3/uL"),
    ("GLU", "Glucose", "mg/dL"),
    ("CR", "Creatinine", "mg/dL"),
    ("CHOL", "Cholesterol", "mg/dL"),
]


def main() -> None:
    """Continuously produce random lab result events to Kafka."""
    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        api_version=(0, 10, 1),
    )

    while True:
        test_code, test_name, unit = random.choice(LAB_TESTS)
        lab_result = {
            "id": str(uuid.uuid4()),
            "patient_id": str(uuid.uuid4()),
            "test_code": test_code,
            "test_name": test_name,
            "value": round(random.uniform(1, 200), 2),
            "unit": unit,
            "result_time": datetime.now(timezone.utc).isoformat(),
        }
        producer.send("ehr.labresults.events", value=lab_result)
        print("Sent lab result:", lab_result)
        time.sleep(2)


if __name__ == "__main__":
    main()
