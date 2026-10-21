# Node.js service (same pattern as currencyservice)
FROM --platform=$BUILDPLATFORM node:20-alpine AS builder
RUN apk add --no-cache python3 make g++
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

FROM alpine:3.19
RUN apk add --no-cache nodejs && \
    addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
USER appuser
EXPOSE 50051
ENTRYPOINT ["node", "index.js"]
