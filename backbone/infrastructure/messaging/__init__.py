"""
Messaging Infrastructure - Event bus adapters for different message brokers
"""
from .kafka_adapter import KafkaEventBusAdapter
from .rabbitmq_adapter import RabbitMQEventBusAdapter
from .redis_adapter import RedisEventBusAdapter

__all__ = [
    "KafkaEventBusAdapter",
    "RabbitMQEventBusAdapter", 
    "RedisEventBusAdapter"
]


class EventBusAdapterFactory:
    """Factory for creating event bus adapters."""
    
    @staticmethod
    def create_kafka_adapter(
        bootstrap_servers: str,
        topic_prefix: str = "events",
        group_id: str = "backbone-consumer",
        logger=None
    ) -> "KafkaEventBusAdapter":
        """Creates Kafka event bus adapter."""
        return KafkaEventBusAdapter(bootstrap_servers, topic_prefix, group_id, logger)
    
    @staticmethod
    def create_rabbitmq_adapter(
        connection_url: str,
        exchange_name: str = "backbone.events",
        queue_prefix: str = "backbone",
        logger=None
    ) -> "RabbitMQEventBusAdapter":
        """Creates RabbitMQ event bus adapter."""
        return RabbitMQEventBusAdapter(connection_url, exchange_name, queue_prefix, logger)
    
    @staticmethod
    def create_redis_adapter(
        redis_url: str,
        channel_prefix: str = "backbone.events",
        logger=None
    ) -> "RedisEventBusAdapter":
        """Creates Redis event bus adapter."""
        return RedisEventBusAdapter(redis_url, channel_prefix, logger)
    
    @staticmethod
    def get_available_adapters() -> list[str]:
        """Gets list of available adapters based on installed packages."""
        available = []
        
        try:
            import aiokafka
            available.append("kafka")
        except ImportError:
            pass
        
        try:
            import aio_pika
            available.append("rabbitmq")
        except ImportError:
            pass
        
        try:
            import aioredis
            available.append("redis")
        except ImportError:
            pass
        
        return available