# .NET service — uses Microsoft's "chiseled" image (their distroless equivalent)
# Stage 1 — build with full SDK
FROM --platform=$BUILDPLATFORM mcr.microsoft.com/dotnet/sdk:8.0-alpine AS builder
WORKDIR /app
# Restore deps (separate layer = cached unless .csproj changes)
COPY src/cartservice/*.csproj ./
RUN dotnet restore
COPY src/cartservice/ ./
# PublishSingleFile=false, SelfContained=false = smaller image (runtime is in the base image)
RUN dotnet publish -c Release -o /out

# Stage 2 — chiseled = non-root, no shell, no package manager
FROM mcr.microsoft.com/dotnet/aspnet:8.0-noble-chiseled
WORKDIR /app
COPY --from=builder /out .
# chiseled images run as app (uid 1654) by default
EXPOSE 7070
ENTRYPOINT ["dotnet", "cartservice.dll"]
