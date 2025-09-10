#build
FROM maven:3-eclipse-temurin-21-alpine AS build

WORKDIR /app

COPY pom.xml .

# Copy settings.xml
COPY src ./src
RUN mvn clean package -DskipTests -B

#run 
FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-Djava.awt.headless=true", "-jar", "app.jar"]
