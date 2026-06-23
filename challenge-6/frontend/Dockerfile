FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

WORKDIR /app

COPY frontend/requirements.txt /app/frontend/requirements.txt
RUN pip install --no-cache-dir -r /app/frontend/requirements.txt

COPY frontend /app/frontend
COPY lib /app/lib

WORKDIR /app/frontend
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
