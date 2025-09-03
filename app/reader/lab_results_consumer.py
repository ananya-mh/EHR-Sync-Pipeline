from kafka import KafkaConsumer
import json

def read_lab_results():
    consumer = KafkaConsumer(
        "ehr.labresults.events",  
        bootstrap_servers='kafka:9092',
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        group_id='ehr-lab-results-consumer-group',
        api_version=(0, 10, 1)  
    )
    for message in consumer:
        yield message.value

