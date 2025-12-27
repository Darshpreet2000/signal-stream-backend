"""ksqlDB client for querying materialized views.

This client is optional and only used when ksqlDB credentials are configured.
"""

import json
import logging
import socket
from typing import Any, Dict, List, Optional

import aiohttp

from ..config import get_settings

logger = logging.getLogger(__name__)


class KsqlDBClient:
    """Client for the ksqlDB REST API."""

    def __init__(self) -> None:
        settings = get_settings()
        self.url = settings.ksqldb_url.rstrip("/")
        self.api_key = settings.ksqldb_api_key
        self.api_secret = settings.ksqldb_api_secret

        if self.url:
            logger.info(f"ksqlDB client configured: {self.url}")
        else:
            logger.info("ksqlDB client not configured (KSQLDB_URL is empty)")

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.api_key and self.api_secret)

    async def execute_statement(self, ksql: str) -> bool:
        """Execute a ksqlDB statement (DDL/DML) via the /ksql endpoint.

        Used for CREATE STREAM, CREATE TABLE, INSERT, etc.
        Returns True if successful, False otherwise.
        """
        if not self.is_configured:
            logger.debug("ksqlDB execute_statement skipped (client not configured)")
            return False

        endpoint = f"{self.url}/ksql"
        payload = {
            "ksql": ksql,
            "streamsProperties": {},
        }

        auth = aiohttp.BasicAuth(self.api_key, self.api_secret)
        headers = {"Content-Type": "application/vnd.ksql.v1+json"}

        try:
            timeout = aiohttp.ClientTimeout(total=60)
            connector = aiohttp.TCPConnector(family=socket.AF_INET)
            async with aiohttp.ClientSession(timeout=timeout, auth=auth, connector=connector) as session:
                async with session.post(endpoint, json=payload, headers=headers) as resp:
                    text = await resp.text()

                    if resp.status != 200:
                        logger.error(f"ksqlDB statement failed: {resp.status} - {text[:500]}")
                        return False

                    logger.info("ksqlDB statement executed successfully")
                    return True

        except Exception as e:
            logger.error(f"Error executing ksqlDB statement: {repr(e)}", exc_info=True)
            return False

    async def execute_query(self, ksql: str) -> Optional[List[Dict[str, Any]]]:
        """Execute a ksqlDB query.

        Returns a list of rows (dicts) or None if there are no data rows or an error.
        Handles both JSON array responses and NDJSON (newline-delimited JSON).
        """
        if not self.is_configured:
            logger.debug("ksqlDB execute_query skipped (client not configured)")
            return None

        endpoint = f"{self.url}/query"
        payload = {
            "ksql": ksql,
            "streamsProperties": {"ksql.streams.auto.offset.reset": "earliest"},
        }

        auth = aiohttp.BasicAuth(self.api_key, self.api_secret)
        # Accept both v1+json and delimited formats
        headers = {
            "Content-Type": "application/vnd.ksql.v1+json",
            "Accept": "application/vnd.ksql.v1+json"
        }

        try:
            timeout = aiohttp.ClientTimeout(total=120)
            connector = aiohttp.TCPConnector(family=socket.AF_INET)
            async with aiohttp.ClientSession(timeout=timeout, auth=auth, connector=connector) as session:
                async with session.post(endpoint, json=payload, headers=headers) as resp:
                    text = await resp.text()

                    if resp.status != 200:
                        logger.error(f"ksqlDB query failed: {resp.status} - {text[:500]}")
                        return None

                    try:
                        data: Any = await resp.json()
                    except Exception as e:
                        logger.warning(
                            f"ksqlDB JSON parse error (possibly NDJSON): {e}. Parsing line-by-line."
                        )
                        try:
                            lines = [ln for ln in text.strip().split("\n") if ln.strip()]
                            data = [json.loads(ln) for ln in lines]
                        except Exception as parse_error:
                            logger.error(f"Failed to parse ksqlDB response as NDJSON: {parse_error}")
                            return None

                    if isinstance(data, dict):
                        if "header" in data or "queryId" in data:
                            return None
                        if "error_code" in data or "message" in data:
                            logger.warning(f"ksqlDB returned error object: {data}")
                            return None
                        return [data]

                    if isinstance(data, list):
                        clean: List[Dict[str, Any]] = []
                        for row in data:
                            if not isinstance(row, dict):
                                continue
                            if "header" in row or "queryId" in row:
                                continue
                            clean.append(row)
                        return clean or None

                    return None

        except Exception as e:
            logger.error(f"Error executing ksqlDB query: {repr(e)}", exc_info=True)
            return None


_ksqldb_client: Optional[KsqlDBClient] = None


def get_ksqldb_client() -> KsqlDBClient:
    global _ksqldb_client
    if _ksqldb_client is None:
        _ksqldb_client = KsqlDBClient()
    return _ksqldb_client
