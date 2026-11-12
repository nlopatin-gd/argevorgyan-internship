FROM --platform=$BUILDPLATFORM golang:1.27-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# Trivy: fix CVE-2026-78661 / CVE-2026-78669 in golang.org/x/net
RUN go get golang.org/x/net@v0.62.0
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o productcatalogservice .

FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /app
COPY --from=builder /app/productcatalogservice /app/productcatalogservice
COPY --from=builder /app/products.json /app/products.json
USER nonroot:nonroot
# checkov:skip=CKV_DOCKER_2:distroless has no shell/curl; health is checked by Kubernetes gRPC probes
EXPOSE 3550
ENTRYPOINT ["/app/productcatalogservice"]
