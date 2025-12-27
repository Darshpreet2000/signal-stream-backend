"""SignalStream AI Backend - Main FastAPI application."""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    messages_router,
    conversations_router,
    health_router,
    websocket_router,
)
from .ai import GeminiService
from .config import get_settings
from .kafka import KafkaProducerService, KafkaAdminService
from .consumers import (
    ConversationProcessorConsumer,
    SentimentAgentConsumer,
    PIIAgentConsumer,
    InsightsAgentConsumer,
    SummaryAgentConsumer,
    AggregationConsumer,
)

# Configure logging
settings = get_settings()
log_level = logging.DEBUG if settings.app_env == "development" else logging.INFO

logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
)
logger = logging.getLogger(__name__)
logger.info(f"Logging configured at level={logging.getLevelName(log_level)}")

# Global application state
app_state: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup and shutdown.

    Args:
        app: FastAPI application
    """
    settings = get_settings()

    logger.info("🚀 Starting SignalStream AI Backend...")
    logger.debug("→ Lifespan startup initiated")
    logger.info("   HTTP server will start immediately...")
    logger.info("   Kafka consumers will initialize in background...")

    # Initialize basic services first (non-blocking)
    try:
        # Gemini AI Service (fast, no network call during init)
        logger.info("Initializing Gemini AI service...")
        gemini_service = GeminiService(settings)
        app.state.gemini_service = gemini_service

        # Intelligence cache (for API lookups)
        app.state.intelligence_cache = {}
        app.state.producer = None
        app.state.consumers = []
        app.state.consumer_tasks = []
        app.state.kafka_ready = False

        logger.info("✅ Core services initialized")
        logger.info(f"   - API Version: {settings.api_version}")
        logger.info(f"   - Gemini Model: {settings.gemini_model}")

    except Exception as e:
        logger.error(f"Failed to start core services: {e}", exc_info=True)
        raise

    # Start Kafka initialization in background
    async def initialize_kafka():
        """Initialize Kafka services in background."""
        try:
            logger.info("🔄 Background: Starting Kafka initialization...")

            if not settings.kafka_is_configured:
                if settings.app_env == "development":
                    logger.warning(
                        "Kafka is not configured (or disabled). Running in development mode without Kafka. "
                        "Message ingestion will use the in-process dev shortcut; streaming pipeline will be disabled."
                    )
                    app.state.kafka_ready = False
                    return

                raise RuntimeError(
                    "Kafka is not configured. Set KAFKA_ENABLED=true and provide KAFKA_BOOTSTRAP_SERVERS and credentials."
                )
            
            # Kafka Admin - ensure topics exist
            logger.info("Background: Initializing Kafka admin...")
            kafka_admin = KafkaAdminService(settings)
            await kafka_admin.ensure_topics_exist()

            # Kafka Producer
            logger.info("Background: Initializing Kafka producer...")
            loop = asyncio.get_running_loop()
            producer = await loop.run_in_executor(None, KafkaProducerService, settings)
            app.state.producer = producer

            # Initialize consumers
            logger.info("Background: Initializing Kafka consumers...")

            # Conversation Processor
            conv_processor = await loop.run_in_executor(None, ConversationProcessorConsumer, settings, producer)

            # AI Agents
            sentiment_agent = await loop.run_in_executor(None, SentimentAgentConsumer, settings, producer, gemini_service)
            pii_agent = await loop.run_in_executor(None, PIIAgentConsumer, settings, producer, gemini_service)
            insights_agent = await loop.run_in_executor(None, InsightsAgentConsumer, settings, producer, gemini_service)
            summary_agent = await loop.run_in_executor(None, SummaryAgentConsumer, settings, producer, gemini_service)

            # Aggregation Consumer
            aggregation_consumer = await loop.run_in_executor(None, AggregationConsumer, settings, producer)
            app.state.intelligence_cache = aggregation_consumer.intelligence_cache

            # Store consumers in app state
            app.state.consumers = [
                conv_processor,
                sentiment_agent,
                pii_agent,
                insights_agent,
                summary_agent,
                aggregation_consumer,
            ]

            # Start consumers as background tasks
            logger.info("Background: Starting consumer tasks...")
            consumer_tasks = []
            for consumer in app.state.consumers:
                task = asyncio.create_task(consumer.start())
                consumer_tasks.append(task)

            app.state.consumer_tasks = consumer_tasks
            app.state.kafka_ready = True
            logger.info("✅ Kafka services initialized successfully!")
            logger.info(f"   - Kafka Bootstrap: {settings.kafka_bootstrap_servers}")
            logger.info(f"   - Consumers Running: {len(app.state.consumers)}")  # Now 5 instead of 6

            logger.info("✅ Kafka services initialized successfully!")
            logger.info(f"   - Kafka Bootstrap: {settings.kafka_bootstrap_servers}")
            logger.info(f"   - Consumers Running: {len(consumer_tasks)}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Kafka services: {e}", exc_info=True)
            app.state.kafka_ready = False

    # Start Kafka initialization task (non-blocking)
    task = asyncio.create_task(initialize_kafka())
    logger.info("✅ Background Kafka task created")

    # Yield control to the application (HTTP server starts now)
    logger.info("🌐 Yielding to HTTP server...")
    yield
    logger.info("🛑 Received shutdown signal")

    # Shutdown
    logger.info("🛑 Shutting down SignalStream AI Backend...")

    try:
        # Stop all consumers
        logger.info("Stopping consumers...")
        for consumer in getattr(app.state, "consumers", []):
            await consumer.stop()

        # Cancel consumer tasks
        for task in getattr(app.state, "consumer_tasks", []):
            task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*getattr(app.state, "consumer_tasks", []), return_exceptions=True)

        # Flush and close producer
        if hasattr(app.state, "producer") and app.state.producer:
            logger.info("Closing Kafka producer...")
            await app.state.producer.close()

        logger.info("✅ Shutdown complete")

    except Exception as e:
        logger.error(f"Error during shutdown: {e}", exc_info=True)


# Create FastAPI application
app = FastAPI(
    title="SignalStream AI",
    description="""
# SignalStream AI - Real-time Support Intelligence Platform

Powered by **Confluent Kafka** and **Google Gemini AI**, SignalStream AI provides
real-time intelligence for customer support conversations.

## Features

- **Real-time Message Ingestion**: Ingest support messages from any channel
- **AI-Powered Analysis**: Sentiment, PII detection, intent extraction, summarization
- **Streaming Intelligence**: WebSocket API for real-time updates
- **Multi-Tenant**: Built for SaaS with tenant isolation
- **Event-Driven**: Kafka-first architecture for scalability

## Getting Started

### 1. Ingest Messages

```
POST /v1/messages
```

### 2. Get Intelligence

```
GET /v1/conversations/{conversation_id}/insights
```

### 3. Stream Real-time Updates

```
WebSocket: ws://localhost:8000/ws/conversations/{conversation_id}/stream
```

## Customer Onboarding

To integrate your application:

1. Obtain API credentials (tenant_id)
2. Send messages to `/v1/messages` endpoint
3. Receive intelligence via polling or WebSocket

See full documentation at `/docs`.
    """,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# Include routers
app.include_router(health_router, prefix="")
app.include_router(messages_router, prefix=f"/{settings.api_version}")
app.include_router(conversations_router, prefix=f"/{settings.api_version}")
app.include_router(websocket_router, prefix="")


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint."""
    return {
        "name": "SignalStream AI",
        "version": "0.1.0",
        "status": "operational",
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()

    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
