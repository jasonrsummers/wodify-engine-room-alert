FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN playwright install chromium

CMD ["python", "main.py"]
