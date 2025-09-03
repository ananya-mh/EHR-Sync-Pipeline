import psycopg2

def write_patient_event(patient):
    try:
        conn = psycopg2.connect(
            host="postgres",
            dbname="ehr_db",
            user="postgres",
            password="password"
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO patients (id, name, age, condition) VALUES (%s, %s, %s, %s) ON CONFLICT (id) DO NOTHING;",
            (patient["id"], patient["name"], patient["age"], patient["condition"])
        )
        conn.commit()
        print("Inserted!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error inserting: {e}")

def write_lab_result(lab_result):
    try:
        conn = psycopg2.connect(
            host="postgres",
            dbname="ehr_db",
            user="postgres",
            password="password"
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO lab_results (id, patient_id, test_code, test_name, value, unit, result_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
            """,
            (
                lab_result["id"],
                lab_result["patient_id"],
                lab_result["test_code"],
                lab_result["test_name"],
                lab_result["value"],
                lab_result["unit"],
                lab_result["result_time"]
            )
        )
        conn.commit()
        print("✅ Inserted lab result")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error inserting lab result: {e}")

def write_medication(med):
    try:
        conn = psycopg2.connect(
            host="postgres",
            dbname="ehr_db",
            user="postgres",
            password="password"
        )
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO medications (id, patient_id, drug_code, drug_name, dose, route, start_time, end_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING;
            """,
            (med["id"], med["patient_id"], med["drug_code"], med["drug_name"], med["dose"], med['route'], med["start_time"], med["end_time"])
        )
        conn.commit()
        print("Inserted!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"❌ Error inserting: {e}")
