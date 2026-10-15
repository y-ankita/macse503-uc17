-- Realtime Identity Events
SELECT
    src.event_key,
    src.source_event_id,
    src.topic,
    src.event_type,
    src.event_timestamp,
    src.payload
FROM staging.stg_identity_events AS src
WHERE NOT EXISTS (
    SELECT 1
    FROM staging.stg_identity_events_clean AS clean
    WHERE clean.event_key = src.event_key
)
ORDER BY src.event_timestamp ASC NULLS LAST;