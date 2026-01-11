use rdkafka::config::ClientConfig;
use rdkafka::consumer::{BaseConsumer, Consumer, StreamConsumer};
use rdkafka::message::{Message, Headers};
use rdkafka::util::get_rdkafka_version;
use std::time::Duration;
use tokio::runtime::Runtime;

pub struct CausalConsumer {
    brokers: String,
    topic: String,
}

impl CausalConsumer {
    pub fn new(brokers: &str, topic: &str) -> Self {
        Self {
            brokers: brokers.to_string(),
            topic: topic.to_string(),
        }
    }

    pub fn start(&self) {
        let brokers = self.brokers.clone();
        let topic = self.topic.clone();

        std::thread::spawn(move || {
            let rt = Runtime::new().unwrap();
            rt.block_on(async move {
                let consumer: StreamConsumer = ClientConfig::new()
                    .set("group.id", "rust_causal_core")
                    .set("bootstrap.servers", &brokers)
                    .set("enable.partition.eof", "false")
                    .set("session.timeout.ms", "6000")
                    .set("enable.auto.commit", "true")
                    .create()
                    .expect("Consumer creation failed");

                consumer
                    .subscribe(&[&topic])
                    .expect("Can't subscribe to specified topic");

                println!("ignored: Rust Consumer started on topic: {}", topic);

                loop {
                    match consumer.recv().await {
                        Err(e) => eprintln!("Kafka error: {}", e),
                        Ok(m) => {
                            let payload = match m.payload_view::<str>() {
                                None => "",
                                Some(Ok(s)) => s,
                                Some(Err(e)) => {
                                    eprintln!("Error while deserializing message payload: {:?}", e);
                                    ""
                                }
                            };
                            println!("ignored: Received event: {}", payload);
                            // In a real implementation, we would extract fact_id and call GraphWalker here
                            // For MVP, we just log it.
                        }
                    };
                }
            });
        });
    }
}
