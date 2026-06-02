# Backend Dockerfile
# 1. Download python:3.11-slim
# 2. Create /app
# 3. Copy requirements.txt
# 4. Install dependencies
# 5. Copy project files
# 6. Save image as "realtyiq"

FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
