# Python load generator — uses Locust to generate traffic
FROM --platform=$BUILDPLATFORM python:3.12-alpine AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
USER appuser
# 8089 = Locust web UI
EXPOSE 8089
ENTRYPOINT ["locust", "--headless", "-f", "locustfile.py"]
