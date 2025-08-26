#build
FROM maven:3-eclipse-temurin-21-alpine AS build

WORKDIR /app

ARG DOCKERNEXUS
ENV DOCKERNEXUS=${DOCKERNEXUS}

COPY settings.xml /root/.m2/settings.xml

COPY pom.xml .

RUN mvn dependency:go-offline -B

COPY src ./src

RUN mvn clean package -DskipTests -B \
    && rm -rf /root/.m2  

#run 
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-Djava.awt.headless=true", "-jar", "app.jar"]
