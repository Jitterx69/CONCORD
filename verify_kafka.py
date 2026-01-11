from app.core.event_bus import EventBus
import time
import uuid


def verify_kafka():
    print("⏳ Connecting to Kafka (localhost:9092)...")
    # For local testing from host machine
    bus = EventBus()
    bus.initialize(bootstrap_servers="localhost:9092")

    if not bus.producer:
        print(
            "❌ Failed to initialize Producer. ensure Docker is running and ports are mapped."
        )
        return

    print("📤 Publishing test event...")
    fact_id = str(uuid.uuid4())
    bus.publish(
        "narrative.facts.created",
        {
            "fact_id": fact_id,
            "subject": "TestSubject",
            "predicate": "TestPredicate",
            "object": "TestObject",
            "timestamp": str(time.time()),
        },
    )

    # We can't easily check Rust logs from here without docker logs command
    print(
        f"✅ Event {fact_id} published. Check 'docker logs concord-rust-core' to see if it was consumed."
    )


if __name__ == "__main__":
    verify_kafka()
