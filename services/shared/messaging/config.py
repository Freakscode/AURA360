"""
Kafka Configuration Management

Handles environment-specific configuration for Kafka connections.
Supports both local development (docker-compose) and production (Confluent Cloud).
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class KafkaConfig:
    """Kafka connection configuration"""

    bootstrap_servers: str
    schema_registry_url: Optional[str] = None
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None

    @classmethod
    def from_env(cls) -> "KafkaConfig":
        """
        Load configuration from environment variables.

        Environment Variables:
            KAFKA_BOOTSTRAP_SERVERS: Comma-separated list of Kafka brokers
            KAFKA_SCHEMA_REGISTRY_URL: URL of Schema Registry (optional)
            KAFKA_SECURITY_PROTOCOL: Security protocol (PLAINTEXT, SASL_SSL, etc.)
            KAFKA_SASL_MECHANISM: SASL mechanism (PLAIN, SCRAM-SHA-256, etc.)
            KAFKA_API_KEY: Confluent Cloud API Key (username)
            KAFKA_API_SECRET: Confluent Cloud API Secret (password)
        """
        is_production = os.getenv("ENV", "development") == "production"

        if is_production:
            # Confluent Cloud configuration
            return cls(
                bootstrap_servers=os.getenv(
                    "KAFKA_BOOTSTRAP_SERVERS",
                    "pkc-xxxxx.us-east-1.aws.confluent.cloud:9092"
                ),
                schema_registry_url=os.getenv(
                    "KAFKA_SCHEMA_REGISTRY_URL",
                    "https://psrc-xxxxx.us-east-1.aws.confluent.cloud"
                ),
                security_protocol="SASL_SSL",
                sasl_mechanism="PLAIN",
                sasl_username=os.getenv("KAFKA_API_KEY"),
                sasl_password=os.getenv("KAFKA_API_SECRET"),
            )
        else:
            # Local development configuration
            return cls(
                bootstrap_servers=os.getenv(
                    "KAFKA_BOOTSTRAP_SERVERS",
                    "localhost:9092"
                ),
                schema_registry_url=os.getenv(
                    "KAFKA_SCHEMA_REGISTRY_URL",
                    "http://localhost:8081"
                ),
                security_protocol="PLAINTEXT",
            )

    def to_producer_config(self) -> dict:
        """Convert to confluent_kafka Producer configuration"""
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "client.id": f"aura360-producer-{os.getpid()}",
            "acks": "all",  # Wait for all replicas
            "retries": 3,
            "max.in.flight.requests.per.connection": 5,
            "enable.idempotence": True,  # Exactly-once semantics
            "compression.type": "snappy",
        }

        if self.security_protocol != "PLAINTEXT":
            config.update({
                "security.protocol": self.security_protocol,
                "sasl.mechanism": self.sasl_mechanism,
                "sasl.username": self.sasl_username,
                "sasl.password": self.sasl_password,
            })

        return config

    def to_consumer_config(self, group_id: str, **kwargs) -> dict:
        """
        Convert to confluent_kafka Consumer configuration

        Args:
            group_id: Consumer group ID
            **kwargs: Additional consumer-specific configuration
        """
        config = {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": group_id,
            "client.id": f"aura360-consumer-{os.getpid()}",
            "auto.offset.reset": kwargs.get("auto_offset_reset", "earliest"),
            "enable.auto.commit": kwargs.get("enable_auto_commit", True),
            "auto.commit.interval.ms": kwargs.get("auto_commit_interval_ms", 5000),
            "max.poll.interval.ms": kwargs.get("max_poll_interval_ms", 300000),  # 5 min
            "session.timeout.ms": kwargs.get("session_timeout_ms", 45000),  # 45s
        }

        if self.security_protocol != "PLAINTEXT":
            config.update({
                "security.protocol": self.security_protocol,
                "sasl.mechanism": self.sasl_mechanism,
                "sasl.username": self.sasl_username,
                "sasl.password": self.sasl_password,
            })

        return config


# Singleton instance
_kafka_config: Optional[KafkaConfig] = None


def get_kafka_config() -> KafkaConfig:
    """Get or create the global Kafka configuration"""
    global _kafka_config
    if _kafka_config is None:
        _kafka_config = KafkaConfig.from_env()
    return _kafka_config
