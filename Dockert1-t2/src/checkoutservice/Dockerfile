# Same pattern as frontend — Go service, distroless runtime
FROM --platform=$BUILDPLATFORM golang:1.23-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o /checkoutservice .

FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=builder /checkoutservice /checkoutservice
USER nonroot:nonroot
EXPOSE 5050
ENTRYPOINT ["/checkoutservice"]
