# Python service — alpine keeps image small
FROM --platform=$BUILDPLATFORM python:3.12-alpine AS builder
WORKDIR /app
# Install deps into a separate /install dir so we can copy only that
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
# Copy installed packages from builder
COPY --from=builder /install /usr/local
COPY . .
USER appuser
EXPOSE 8080
ENTRYPOINT ["python", "email_server.py"]
