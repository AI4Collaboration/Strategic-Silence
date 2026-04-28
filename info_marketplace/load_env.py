"""Helper to load environment variables from .env file."""

import os
from pathlib import Path


def load_env():
    """Load environment variables from .env file if it exists.

from __future__ import annotations

    Tries to use python-dotenv if available, otherwise manually parses .env file.
    """
    # Try using python-dotenv if installed
    try:
        from dotenv import load_dotenv
        env_path = Path(__file__).parent.parent / '.env'
        load_dotenv(env_path)
        return
    except ImportError:
        pass

    # Fallback: manually parse .env file
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        return

    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            # Parse KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                # Set environment variable if not already set
                if key and value and not os.environ.get(key):
                    os.environ[key] = value


if __name__ == "__main__":
    print("=== Testing .env loader ===")

    # Check before loading
    print(f"OPENAI_API_KEY before: {os.environ.get('OPENAI_API_KEY', 'NOT SET')}")

    # Load .env
    load_env()

    # Check after loading
    api_key = os.environ.get('OPENAI_API_KEY', 'NOT SET')
    print(f"OPENAI_API_KEY after: {api_key}")

    if api_key and api_key != 'NOT SET' and api_key != 'your-openai-api-key-here':
        print("\n✓ API key loaded successfully!")
    else:
        print("\n⚠️  Please set your OpenAI API key in .env file")
        print("Edit /Users/mac/Desktop/Word_Play-main/.env and replace 'your-openai-api-key-here' with your actual key")
