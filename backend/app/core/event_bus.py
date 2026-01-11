from confluent_kafka import Producer
import json
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class EventBus:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBus, cls).__new__(cls)
            cls._instance.producer = None
        return cls._instance

    def initialize(self, bootstrap_servers: str = "localhost:9092"):
        """Initialize the Kafka producer"""
        try:
            conf = {"bootstrap.servers": bootstrap_servers, "client.id": "concord-backend-producer"}
            self.producer = Producer(conf)
            logger.info(f"✅ Connected to Kafka at {bootstrap_servers}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            self.producer = None

    def publish(self, topic: str, payload: dict):
        """Publish an event to a Kafka topic"""
        if not self.producer:
            logger.warning(f"⚠️ EventBus not initialized. Skipping event: {topic}")
            return

        def delivery_report(err, msg):
            if err is not None:
                logger.error(f"❌ Message delivery failed: {err}")
            else:
                logger.debug(f"✅ Message delivered to {msg.topic()} [{msg.partition()}]")

        try:
            self.producer.produce(
                topic, json.dumps(payload).encode("utf-8"), callback=delivery_report
            )
            # self.producer.flush() # Blocking, use poll() in production for throughput
            self.producer.poll(0)
        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
