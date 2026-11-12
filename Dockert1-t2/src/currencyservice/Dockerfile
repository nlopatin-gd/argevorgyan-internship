# Stage 1: install production dependencies.
# No --platform=$BUILDPLATFORM here on purpose: node_modules must be built for the
# target architecture (amd64), otherwise native modules would be arm64 on a Mac.
FROM node:24.20.0-alpine AS builder
RUN apk add --no-cache python3 make g++
WORKDIR /usr/src/app
COPY package*.json ./
RUN npm ci --omit=dev

# Stage 2: alpine + only the node binary (no npm, no compilers)
FROM alpine:3.24.1
RUN apk add --no-cache nodejs && adduser -S -u 10001 app
WORKDIR /usr/src/app
COPY --from=builder /usr/src/app/node_modules ./node_modules
COPY . .
USER 10001
# checkov:skip=CKV_DOCKER_2:no curl in the runtime image; health is checked by Kubernetes gRPC probes
EXPOSE 7000
ENTRYPOINT ["node", "server.js"]
