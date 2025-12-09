FROM maven:3-eclipse-temurin-21 AS build

WORKDIR /app

COPY pom.xml .

COPY src ./src

RUN mvn clean package -DskipTests -B -Dmaven.wagon.http.retryHandler.count=5

FROM eclipse-temurin:21-jre

WORKDIR /app

ADD https://repo1.maven.org/maven2/io/prometheus/jmx/jmx_prometheus_javaagent/0.20.0/jmx_prometheus_javaagent-0.20.0.jar /jmx.jar

COPY jmx_exporter_config.yaml /config/jmx.yaml

COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080

EXPOSE 9404

ENTRYPOINT ["java", "-javaagent:/jmx.jar=9404:/config/jmx.yaml", "-Djava.awt.headless=true", "-jar", "app.jar"]
