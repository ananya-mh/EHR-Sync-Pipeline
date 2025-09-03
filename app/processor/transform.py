def process_data(patient):
    patient["name"] = patient["name"].strip().title()
    patient["age"] = max(0, min(int(patient["age"]), 120))  # clamp age
    patient["condition"] = patient.get("condition", "Unknown").title()
    return patient

    