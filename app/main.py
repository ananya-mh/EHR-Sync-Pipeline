import threading
from reader.patient_consumer import read_events as read_patient_events
from reader.lab_results_consumer import read_lab_results
from reader.medications_consumer import read_medications

from processor.transform import process_data
from writer.db_writer import write_patient_event, write_medication, write_lab_result

def run_consumer(read_func, write_func, name):
    print(f"Starting conumer: {name}...")
    for raw_event in read_func():
        cleaned = process_data(raw_event)
        write_func(cleaned)

def main():
    consumers = [
        (read_patient_events, "patient_consumer"),
        (read_medication, "medication_consumer"),
        (read_lab_results, "lab_consumer"),
    ]

    threads = []
    for func, name in consumers:
        t = threading.Thread(target=run_consumer, args=(func,name),daemon=True)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    if __name__ == "__main__":
        main()