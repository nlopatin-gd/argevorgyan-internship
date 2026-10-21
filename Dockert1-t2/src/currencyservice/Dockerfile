# Node.js service
# Stage 1 — install deps (needs build tools for native modules)
FROM --platform=$BUILDPLATFORM node:20-alpine AS builder
RUN apk add --no-cache python3 make g++
WORKDIR /app
COPY package*.json ./
# npm ci = clean install, faster and more reproducible than npm install
RUN npm ci --only=production

# Stage 2 — alpine + node binary only, no npm or build tools
FROM alpine:3.19
# Install only the node runtime, not npm
RUN apk add --no-cache nodejs && \
    addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder /app/node_modules ./node_modules
COPY . .
USER appuser
EXPOSE 7000
ENTRYPOINT ["node", "server.js"]
