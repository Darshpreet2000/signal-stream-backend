#!/usr/bin/env python
"""Quick server test."""
import asyncio
import sys

async def test_server():
    """Test if server responds."""
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:8001/health', timeout=5) as resp:
                print(f"Status: {resp.status}")
                text = await resp.text()
                print(f"Response: {text}")
                return True
    except asyncio.TimeoutError:
        print("ERROR: Request timed out after 5 seconds")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_server())
    sys.exit(0 if result else 1)
