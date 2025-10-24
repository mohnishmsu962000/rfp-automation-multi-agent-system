FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run with python to see actual errors
CMD python -c "import sys; sys.path.insert(0, '.'); from app.main import app; import uvicorn; import os; uvicorn.run(app, host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))"