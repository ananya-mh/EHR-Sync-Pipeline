from reader.kafka_reader import read_events
from processor.transform import process_data
from writer.db_writer import write_event

def main():
    print("Starting main script...")
    for raw_event in read_events():
        cleaned = process_data(raw_event)
        write_event(cleaned)

if __name__ == "__main__":
    main()
