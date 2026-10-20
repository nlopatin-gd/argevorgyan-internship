# Java service — JDK to compile, JRE to run (JRE is ~70MB vs JDK ~300MB)
FROM --platform=$BUILDPLATFORM eclipse-temurin:21-jdk-alpine AS builder
WORKDIR /app
# Gradle wrapper + build files first (cache layer)
COPY gradlew build.gradle ./
COPY gradle ./gradle
RUN ./gradlew dependencies --no-daemon
COPY . .
# shadowJar = fat jar with all deps bundled
RUN ./gradlew shadowJar --no-daemon

# JRE-only runtime — no compiler, saves ~200MB
FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
WORKDIR /app
COPY --from=builder /app/build/libs/*.jar app.jar
USER appuser
EXPOSE 9555
ENTRYPOINT ["java", "-jar", "app.jar"]
