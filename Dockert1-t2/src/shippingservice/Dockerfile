FROM --platform=$BUILDPLATFORM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /shippingservice .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /shippingservice /shippingservice
USER nonroot:nonroot
EXPOSE 50051
ENTRYPOINT ["/shippingservice"]
