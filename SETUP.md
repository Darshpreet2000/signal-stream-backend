# SignalStream AI - Setup Guide

## Getting Started

Follow these steps to get the SignalStream AI backend running:

### Step 1: Install Dependencies

```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Setup Confluent Cloud

1. **Sign up for Confluent Cloud** (free tier available):
   - Go to https://confluent.cloud
   - Create a free account
   - Select "Basic" cluster (free)
   - Choose a cloud provider and region

2. **Get Kafka Credentials**:
   - In Confluent Cloud console, go to your cluster
   - Click "API Keys" in the left menu
   - Click "Add Key" → Select "Global Access"
   - **Save the Key and Secret** (you won't see the secret again!)
   
3. **Get Bootstrap Servers**:
   - In your cluster, go to "Cluster Settings"
   - Copy the "Bootstrap server" URL (e.g., `pkc-xxxxx.us-west-2.aws.confluent.cloud:9092`)

### Step 3: Setup Google Gemini

1. **Get Gemini API Key**:
   - Go to https://aistudio.google.com/app/apikey
   - Click "Create API Key"
   - Copy the API key

### Step 4: Configure Environment

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your credentials:
   ```bash
   nano .env  # or use your favorite editor
   ```

3. **Required configuration**:
   ```bash
   # Confluent Cloud Kafka
   KAFKA_BOOTSTRAP_SERVERS=pkc-xxxxx.us-west-2.aws.confluent.cloud:9092
   KAFKA_API_KEY=YOUR_API_KEY
   KAFKA_API_SECRET=YOUR_API_SECRET

   # Google Gemini
   GEMINI_API_KEY=YOUR_GEMINI_API_KEY
   ```

### Step 5: Run the Application

```bash
# Option 1: Using the run script
python run.py

# Option 2: Using uvicorn directly
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
🚀 Starting SignalStream AI Backend...
   - API Version: v1
   - Kafka Bootstrap: pkc-xxxxx...
   - Gemini Model: gemini-1.5-pro
   - Consumers Running: 6
✅ SignalStream AI Backend started successfully!
```

### Step 6: Verify Installation

1. **Check health endpoint**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Open API docs**:
   - Visit http://localhost:8000/docs
   - You should see the Swagger UI with all endpoints

3. **Test message ingestion**:
   ```bash
   curl -X POST "http://localhost:8000/v1/messages" \
     -H "Content-Type: application/json" \
     -d '{
       "conversation_id": "test-123",
       "sender": "customer",
       "message": "Hello, I need help with my order",
       "channel": "chat"
     }'
   ```

### Step 7: Run Demo Script

```bash
# Install additional dependencies for demo
pip install websockets

# Run the example script
python example.py
```

This will:
- Send sample customer messages
- Retrieve AI-generated intelligence
- Stream real-time updates via WebSocket

## Troubleshooting

### Issue: Kafka Connection Failed

**Error**: `Failed to resolve 'pkc-xxxxx.us-west-2.aws.confluent.cloud'`

**Solution**:
- Check your internet connection
- Verify bootstrap servers URL is correct
- Ensure API key has proper permissions

### Issue: Gemini API Rate Limit

**Error**: `Rate limit exceeded`

**Solution**:
- Reduce `GEMINI_RPM_LIMIT` in `.env`
- Wait a few minutes before retrying
- Consider upgrading Gemini API tier

### Issue: Topics Not Found

**Error**: `Topic 'support.messages.raw' not found`

**Solution**:
- The application automatically creates topics on startup
- Check Confluent Cloud console to verify topics exist
- Ensure your API key has `Create` permissions

### Issue: Python Version

**Error**: `Python 3.11 required`

**Solution**:
```bash
# Check Python version
python --version

# If < 3.11, install Python 3.11+
# macOS:
brew install python@3.11

# Ubuntu:
sudo apt install python3.11
```

## Next Steps

1. **Explore the API**:
   - Visit http://localhost:8000/docs
   - Try the interactive API documentation

2. **Integrate Your App**:
   - Use the `/v1/messages` endpoint to send messages
   - Poll `/v1/conversations/{id}/insights` for intelligence
   - Or connect via WebSocket for real-time updates

3. **Monitor Kafka**:
   - Check Confluent Cloud console
   - View topic data and consumer lag
   - Monitor throughput metrics

4. **Production Deployment**:
   - Use Docker: `docker build -t signalstream-backend .`
   - Deploy to cloud (AWS, GCP, Azure)
   - Configure production Kafka cluster
   - Add authentication and rate limiting

## Support

- **Documentation**: See [README.md](README.md)
- **Issues**: Create a GitHub issue
- **Questions**: Contact the development team

## Architecture Overview

```
Customer App → POST /v1/messages
                      ↓
              [Kafka: messages.raw]
                      ↓
           [Conversation Processor]
                      ↓
         [Kafka: conversations.state]
                      ↓
          ┌─────────┴──────────┐
          ▼         ▼         ▼
    [Sentiment] [PII]  [Insights]  [Summary]
          │         │         │         │
          └─────────┴─────────┴─────────┘
                      ↓
            [Aggregation Consumer]
                      ↓
          [Kafka: aggregated intelligence]
                      ↓
          ┌───────────────────┐
          ▼                   ▼
    GET /insights     WebSocket /stream
```

Enjoy building with SignalStream AI! 🚀
