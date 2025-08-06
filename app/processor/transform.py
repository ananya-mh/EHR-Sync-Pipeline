def process_data(patient):
    patient["name"] = patient["name"].upper()
    patient["age"] = int(patient["age"])
    patient["condition"] = patient.get("condition", "Unknown")
    return patient