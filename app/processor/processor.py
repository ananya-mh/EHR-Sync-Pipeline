def process_data(data):
    print("Processing data...")
    return [{"name": d["name"].upper(), "age": d["age"]} for d in data]
