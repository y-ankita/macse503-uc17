
import hashlib
import json
import time

import requests
import psycopg2
from psycopg2.extras import Json

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "EHCMDP_PostgreSQL",
    "user": "postgres",
    "password": "root",
}

STREAM_URL = (
    "https://api.sondahub.com/v1/identity/events?topics=directory"
)


def save_event(db, source_id, event_name, raw_data):
    payload = json.loads(raw_data)

    if not isinstance(payload, dict):
        raise ValueError("Expected a JSON object from the event stream")

    # Stable key prevents the same payload being inserted twice.
    canonical = json.dumps(
        payload, sort_keys=True, separators=(",", ":")
    )
    event_key = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    with db.cursor() as cur:
        cur.execute(
            """
            INSERT INTO staging.stg_identity_events
            (event_key, source_event_id, topic, event_type,
             event_timestamp, payload)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (event_key) DO NOTHING
            """,
            (
                event_key,
                source_id,
                payload.get("topic", "directory"),
                payload.get("type", event_name),
                payload.get("ts"),
                Json(payload),
            ),
        )

    db.commit()
    print(f"Event received; stored key: {event_key[:12]}")


def main():
    db = psycopg2.connect(**DB_CONFIG)
    print("Connected to PostgreSQL. Listening for events...")

    try:
        while True:
            try:
                with requests.get(
                    STREAM_URL,
                    stream=True,
                    timeout=(15, 90),
                    headers={"Accept": "text/event-stream"},
                ) as response:
                    response.raise_for_status()

                    source_id = None
                    event_name = None
                    data_lines = []

                    print("Connected to event stream.")

                    for raw_line in response.iter_lines():
                        line = raw_line.decode("utf-8").strip()

                        if not line:
                            if data_lines:
                                try:
                                    save_event(
                                        db, source_id, event_name,
                                        "\n".join(data_lines)
                                    )
                                except (ValueError, json.JSONDecodeError) as exc:
                                    print("Invalid event:", exc)
                                except psycopg2.Error:
                                    db.rollback()
                                    raise

                            source_id = None
                            event_name = None
                            data_lines = []
                            continue

                        if line.startswith(":"):
                            continue
                        if line.startswith("id:"):
                            source_id = line[3:].strip()
                        elif line.startswith("event:"):
                            event_name = line[6:].strip()
                        elif line.startswith("data:"):
                            data_lines.append(line[5:].lstrip())

            except KeyboardInterrupt:
                break
            except (requests.RequestException, psycopg2.Error) as exc:
                print("Connection error:", exc)
                time.sleep(5)

                if db.closed:
                    db = psycopg2.connect(**DB_CONFIG)

    finally:
        db.close()
        print("Consumer stopped.")


if __name__ == "__main__":
    main()
