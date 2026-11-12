FROM --platform=$BUILDPLATFORM golang:1.27-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
# fix known CVEs in golang.org/x/net (same as frontend/productcatalogservice)
RUN go get golang.org/x/net@v0.62.0
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o shippingservice .

FROM gcr.io/distroless/static-debian12:nonroot
WORKDIR /app
COPY --from=builder /app/shippingservice /app/shippingservice
USER nonroot:nonroot
# checkov:skip=CKV_DOCKER_2:distroless has no shell/curl; health is checked by Kubernetes gRPC probes
EXPOSE 50051
ENTRYPOINT ["/app/shippingservice"]
