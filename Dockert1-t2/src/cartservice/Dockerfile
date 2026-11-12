ARG BUILDPLATFORM=linux/amd64

# Stage 1: build with the full .NET SDK, produce a self-contained trimmed binary
FROM --platform=$BUILDPLATFORM mcr.microsoft.com/dotnet/sdk:10.0.100-noble AS builder
ARG TARGETARCH=amd64
# Workaround: the SDK can crash under QEMU/Rosetta emulation (MSB4184) without this
ENV DOTNET_EnableWriteXorExecute=0
WORKDIR /app
COPY cartservice.csproj .
RUN dotnet restore cartservice.csproj -a $TARGETARCH
COPY . .
RUN dotnet publish cartservice.csproj \
    -p:PublishSingleFile=true \
    -a $TARGETARCH \
    --self-contained true \
    -p:PublishTrimmed=true \
    -p:TrimMode=full \
    -c release \
    -o /cartservice

# Stage 2: chiseled runtime-deps = Microsoft's distroless (no shell, no package manager)
FROM mcr.microsoft.com/dotnet/runtime-deps:10.0.0-noble-chiseled
WORKDIR /app
COPY --from=builder /cartservice .
ENV DOTNET_EnableDiagnostics=0 \
    ASPNETCORE_HTTP_PORTS=7070
USER 1000
# checkov:skip=CKV_DOCKER_2:chiseled image has no shell/curl; health is checked by Kubernetes gRPC probes
EXPOSE 7070
ENTRYPOINT ["/app/cartservice"]
