import psycopg2

def write_event(patient):
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
