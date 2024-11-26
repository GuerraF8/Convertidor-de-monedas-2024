# backend_rates/Dockerfile

FROM python:3.8-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p data && chmod -R 777 data

EXPOSE 5000

ENV FLASK_APP=app.py

CMD ["python", "app.py"]