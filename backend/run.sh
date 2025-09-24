#!/bin/bash

# Exit on any error
set -e

echo "Starting AIVE Backend API..."

# Activate virtual environment
source .venv/bin/activate

# Wait for database to be ready (if using external database)
if [ ! -z "$DATABASE_URL" ]; then
    echo "Waiting for database to be ready..."
    
    # Simple connection test using Python
    python3 -c "
import asyncio
import asyncpg
import os
import time

async def wait_for_db():
    db_url = os.getenv('DATABASE_URL', '')
    if 'postgresql' in db_url:
        # Remove +asyncpg from URL for initial connection test
        test_url = db_url.replace('+asyncpg', '')
        max_retries = 30
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Try to connect
                conn = await asyncpg.connect(test_url)
                await conn.close()
                print('Database connection successful!')
                break
            except Exception as e:
                retry_count += 1
                print(f'Database connection attempt {retry_count}/{max_retries} failed: {e}')
                if retry_count >= max_retries:
                    print('Failed to connect to database after maximum retries')
                    exit(1)
                await asyncio.sleep(2)

if __name__ == '__main__':
    asyncio.run(wait_for_db())
"
fi

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo "Starting server..."

# Start the FastAPI application
exec uvicorn src.server_api:app --host 0.0.0.0 --port 8000