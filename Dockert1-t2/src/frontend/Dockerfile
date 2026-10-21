# Stage 1 — compile
# golang:1.23-alpine has the Go compiler. alpine keeps it small.
# $BUILDPLATFORM = your Mac's arch (arm64), so the compile runs fast natively.
FROM --platform=$BUILDPLATFORM golang:1.23-alpine AS builder
WORKDIR /app
# Copy deps first — Docker caches this layer; if source changes but deps don't, no re-download
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# CGO_ENABLED=0 = pure Go binary, no C libs needed at runtime
# GOOS/GOARCH = cross-compile for linux/amd64 (what GKE runs)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /frontend .

# Stage 2 — runtime image
# distroless has no shell, no package manager — smallest attack surface possible
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /frontend /frontend
# nonroot user is built into distroless (uid 65532)
USER nonroot:nonroot
EXPOSE 8080
ENTRYPOINT ["/frontend"]
