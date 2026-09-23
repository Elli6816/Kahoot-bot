FROM mcr.microsoft.com/playwright/python:v1.42.0-jammy

WORKDIR /app

RUN pip install --no-cache-dir python-telegram-bot==21.1.1 playwright==1.42.0 aiohttp==3.9.3
RUN playwright install --with-deps chromium

COPY . .

CMD ["python", "sender.py"]
