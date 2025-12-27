#!/usr/bin/env python3
"""Run SignalStream AI Backend."""

import sys
import uvicorn

from src.config import get_settings

if __name__ == "__main__":
    settings = get_settings()

    print("=" * 70)
    print("🚀 SignalStream AI Backend")
    print("=" * 70)
    print(f"Environment: {settings.app_env}")
    print(f"Host: {settings.app_host}")
    print(f"Port: {settings.app_port}")
    print(f"API Docs: http://{settings.app_host}:{settings.app_port}/docs")
    print("=" * 70)

    try:
        uvicorn.run(
            "src.main:app",
            host=settings.app_host,
            port=settings.app_port,
            reload=settings.app_env == "development",
            log_level=settings.log_level.lower(),
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        sys.exit(0)
