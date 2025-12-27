import asyncio
import aiohttp
import requests
import os
import logging
from src.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_requests():
    settings = get_settings()
    url = f"{settings.ksqldb_url}/info"
    logger.info(f"Testing requests connectivity to {url}...")
    try:
        resp = requests.get(url, timeout=10)
        logger.info(f"Requests: Status {resp.status_code}")
        logger.info(f"Requests: Content {resp.text[:100]}")
    except Exception as e:
        logger.error(f"Requests failed: {e}")

async def test_aiohttp():
    settings = get_settings()
    url = f"{settings.ksqldb_url}/ksql"
    logger.info(f"Testing aiohttp POST to {url} with Auth...")
    
    auth = aiohttp.BasicAuth(settings.ksqldb_api_key, settings.ksqldb_api_secret)
    headers = {"Content-Type": "application/vnd.ksql.v1+json"}
    payload = {
        "ksql": "SHOW STREAMS;",
        "streamsProperties": {}
    }

    try:
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(timeout=timeout, auth=auth) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                logger.info(f"aiohttp: Status {resp.status}")
                text = await resp.text()
                logger.info(f"aiohttp: Content {text[:100]}")
    except Exception as e:
        logger.error(f"aiohttp failed: {e}")

if __name__ == "__main__":
    test_requests()
    asyncio.run(test_aiohttp())
