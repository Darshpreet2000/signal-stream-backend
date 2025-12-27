"""Initialize ksqlDB schema."""

import asyncio
import logging
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.utils.ksqldb_client import KsqlDBClient
from src.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize ksqlDB schema."""
    settings = get_settings()
    client = KsqlDBClient()

    if not client.is_configured:
        logger.error("ksqlDB client not configured. Please set KSQLDB_URL, KSQLDB_API_KEY, KSQLDB_API_SECRET.")
        return

    schema_path = os.path.join(os.path.dirname(__file__), "ksqldb", "schema.sql")
    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        return

    logger.info(f"Reading schema from {schema_path}...")
    with open(schema_path, "r") as f:
        sql_content = f.read()

    # Split by semicolon to get individual statements
    # This is a simple split and might break if semicolons are in strings, but sufficient for this schema
    statements = [s.strip() + ";" for s in sql_content.split(";") if s.strip()]

    logger.info(f"Found {len(statements)} statements to execute.")

    for i, stmt in enumerate(statements):
        logger.info(f"Executing statement {i+1}/{len(statements)}...")
        logger.debug(f"SQL: {stmt}")
        success = await client.execute_statement(stmt)
        if not success:
            logger.error(f"Failed to execute statement {i+1}. Aborting.")
            return
        # Small delay to ensure ksqlDB processes it
        await asyncio.sleep(1)

    logger.info("✅ ksqlDB initialization complete.")


if __name__ == "__main__":
    asyncio.run(main())
