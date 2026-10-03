FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7000

# --proxy-headers makes uvicorn trust X-Forwarded-Proto/-For from the reverse
# proxy, so the app sees the public https scheme and the real client IP rather
# than the proxy's. --forwarded-allow-ips="*" is required because the proxy
# reaches the container from the Docker bridge gateway, whose address is not
# fixed; the container is only published on loopback, so nothing else can
# connect to forge those headers.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000", \
     "--proxy-headers", "--forwarded-allow-ips", "*"]
