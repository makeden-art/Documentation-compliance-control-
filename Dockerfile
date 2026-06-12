FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer-nogui libreoffice-calc-nogui \
    curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY app.py dwg_converter.py normocontrol.py normocontrol_engine.py office_checkers.py crypto_stamp.py VERSION ./

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
