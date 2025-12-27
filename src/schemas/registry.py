"""Schema Registry client and Avro serialization utilities."""

import logging
from typing import Optional, Dict, Any
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroSerializer, AvroDeserializer
from confluent_kafka.serialization import SerializationContext, MessageField

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class SchemaRegistryManager:
    """Manages Schema Registry connection and serializers/deserializers."""
    
    def __init__(self):
        """Initialize Schema Registry client and serializers."""
        self.settings = get_settings()
        self.client: Optional[SchemaRegistryClient] = None
        self.serializers: Dict[str, AvroSerializer] = {}
        self.deserializers: Dict[str, AvroDeserializer] = {}
        
        # Only initialize if Schema Registry is configured
        if self.settings.kafka_schema_registry_url:
            self._init_client()
    
    def _init_client(self):
        """Initialize Schema Registry client with authentication."""
        try:
            config = {
                'url': self.settings.kafka_schema_registry_url
            }
            
            # Add authentication if configured
            if self.settings.kafka_schema_registry_api_key and self.settings.kafka_schema_registry_api_secret:
                config['basic.auth.user.info'] = f"{self.settings.kafka_schema_registry_api_key}:{self.settings.kafka_schema_registry_api_secret}"
            
            self.client = SchemaRegistryClient(config)
            logger.info(f"✅ Schema Registry client initialized: {self.settings.kafka_schema_registry_url}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Schema Registry client: {e}")
            self.client = None
    
    def is_enabled(self) -> bool:
        """Check if Schema Registry is enabled and initialized."""
        return self.client is not None
    
    def get_serializer(self, schema: Dict[str, Any], to_dict_func=None) -> Optional[AvroSerializer]:
        """
        Get or create an Avro serializer for a schema.
        
        Args:
            schema: Avro schema dictionary
            to_dict_func: Optional function to convert objects to dictionaries
        
        Returns:
            AvroSerializer instance or None if Schema Registry is not enabled
        """
        if not self.is_enabled():
            return None
        
        schema_str = str(schema)
        if schema_str not in self.serializers:
            self.serializers[schema_str] = AvroSerializer(
                schema_registry_client=self.client,
                schema_str=str(schema),
                to_dict=to_dict_func
            )
        
        return self.serializers[schema_str]
    
    def get_deserializer(self, schema: Dict[str, Any], from_dict_func=None) -> Optional[AvroDeserializer]:
        """
        Get or create an Avro deserializer for a schema.
        
        Args:
            schema: Avro schema dictionary
            from_dict_func: Optional function to convert dictionaries to objects
        
        Returns:
            AvroDeserializer instance or None if Schema Registry is not enabled
        """
        if not self.is_enabled():
            return None
        
        schema_str = str(schema)
        if schema_str not in self.deserializers:
            self.deserializers[schema_str] = AvroDeserializer(
                schema_registry_client=self.client,
                schema_str=str(schema),
                from_dict=from_dict_func
            )
        
        return self.deserializers[schema_str]
    
    def serialize(self, schema: Dict[str, Any], data: Dict[str, Any], topic: str) -> Optional[bytes]:
        """
        Serialize data using Avro schema.
        
        Args:
            schema: Avro schema dictionary
            data: Data to serialize
            topic: Kafka topic name
        
        Returns:
            Serialized bytes or None if Schema Registry is not enabled
        """
        if not self.is_enabled():
            return None
        
        serializer = self.get_serializer(schema)
        if serializer:
            ctx = SerializationContext(topic, MessageField.VALUE)
            return serializer(data, ctx)
        return None
    
    def deserialize(self, schema: Dict[str, Any], data: bytes, topic: str) -> Optional[Dict[str, Any]]:
        """
        Deserialize data using Avro schema.
        
        Args:
            schema: Avro schema dictionary
            data: Serialized bytes
            topic: Kafka topic name
        
        Returns:
            Deserialized dictionary or None if Schema Registry is not enabled
        """
        if not self.is_enabled():
            return None
        
        deserializer = self.get_deserializer(schema)
        if deserializer:
            ctx = SerializationContext(topic, MessageField.VALUE)
            return deserializer(data, ctx)
        return None


# Global Schema Registry manager instance
_schema_registry_manager: Optional[SchemaRegistryManager] = None


def get_schema_registry_manager() -> SchemaRegistryManager:
    """Get or create the global Schema Registry manager instance."""
    global _schema_registry_manager
    if _schema_registry_manager is None:
        _schema_registry_manager = SchemaRegistryManager()
    return _schema_registry_manager


def schema_registry_enabled() -> bool:
    """Check if Schema Registry is enabled."""
    return get_schema_registry_manager().is_enabled()
