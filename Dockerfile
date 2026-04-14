FROM python:3.12-alpine

# Systemabhängige Basics (optional, aber meist sinnvoll)
RUN apk add --no-cache \
    gcc \
    musl-dev \
    libffi-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV FLASK_ENV=production
EXPOSE 5000

CMD ["python", "app.py"]
