# Task 1 Prometheus & Grafana
![task](task.png)

---

## 1. Dockerfile Updates

- Added JMX Prometheus Exporter java agent to the dockerfile
- Exposed port **9404** for the exporter metrics
- Updated `ENTRYPOINT` to include the `-javaagent` flag for JMX metrics collection

```dockerfile
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

```

---

## 2. Docker Compose Updates

- Added **Prometheus** container
  -  JMX metrics from Spring Petclinic (`spring-petclinic:9404`).
  - Exposed on port **9090**.
- Added **Grafana** container
  - Exposed on port **3000**
  - Ensure that prometheus is running before starting
  

```yaml
services:
  spring-petclinic:
    build:
      context: ./
    image: spring-petclinic:latest
    ports:
      - "8079:8080"     
      - "9404:9404"     
    networks:
      - spring-network
    privileged: true            
    volumes:
      - /proc:/host_proc:ro     

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    networks:
      - spring-network
    depends_on:
      - spring-petclinic

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    networks:
      - spring-network
    depends_on:
      - prometheus

volumes:
  grafana_data:

networks:
  spring-network:
    driver: bridge
```
---

## 3. Prometheus Configuration

Created prometheus.yml to configure Prometheus to collect metrics from Spring Petclinic.
scrape_configs defines what to monitor and job_name labels the job.
targets specifies the service endpoints exposing metrics

- `prometheus.yml` 

```yaml
scrape_configs:
  - job_name: "spring-petclinic-jmx"
    static_configs:
      - targets:
          - "spring-petclinic:9404"
```

---

## 4. Verification Steps

1. **Spring Petclinic**:
   -  ensure the application runs.
   ![spring](springui.png)
2. **JMX Exporter**:
   - verify metrics are displayed.
   ![jmx](jmx.png)
3. **Prometheus**:
   ![up](up.png)
   - Run queries:
     - `java_lang_OperatingSystem_CpuLoad`
     ![query2](query2.png)
     - `java_lang_OperatingSystem_FreeMemorySize`
     ![query1](query1.png)
     - `java_lang_Memory_HeapMemoryUsage_used`
     ![query3](query3.png)
     - `java_lang_Runtime_Uptime`
     ![query4](query4.png)
4. **Grafana**:
    ![graf](grafui.png)
   - Open `http://localhost:3000`, add Prometheus as a data source (`http://prometheus:9090`)
   - Import dashboard **ID 10519** to visualize JVM metrics.
   ![data](datasource.png)

5. **Fixing broken panels**

Some Grafana panels were not displaying information correctly. I updated the PromQL queries in the affected panels to use simple, direct java_... JVM metrics, which resolved the issue and made the panels work correctly.
For example: instead of `os_free_physical_memory_bytes{job="$job",instance="$instance"}` I used `java_lang_OperatingSystem_FreePhysicalMemorySize{job="$job",instance="$instance"}` etc
![example](example.png)
<table>
  <tr>
    <th style="font-size:24px; text-align:center;">Before</th>
    <th style="font-size:24px; text-align:center;">After</th>
  </tr>
  <tr>
    <td><img src="before.png" alt="Before" width="1000"></td>
    <td><img src="after1.png" alt="After" width="1000"></td>
  </tr>
  <tr>
    <td><img src="before2.png" alt="Before2" width="1000"></td>
    <td><img src="after2.png" alt="After2" width="1000"></td>
  </tr>
</table>

---

## 5. Summary

- **Spring Petclinic Dockerfile** updated for JMX Prometheus Exporter.  
- **Prometheus and Grafana containers** added via Docker Compose.  
- Initially, some Grafana panels were not displaying metrics correctly. To troubleshoot, I experimented with different Docker base images:  
  - Tried building the application in a **smaller image** (Alpine-based Eclipse Temurin) to see if panel issues were caused because of alpine images.  
  - Switched to a **full OS image** and even added `privileged: true` in the Docker Compose setup.  
- None of these image changes solved the problem. The real cause was incorrect **PromQL** queries in the broken panels. Replacing them with simple, direct  queries fixed the issue c:

# Task 2 - Logging 

![task2](task2.png)

--- 

## 1. Run the Spring Petclinic Application with Logs

Ran the Spring application and redirected logs to a separate file:

```bash
java -jar target/spring-petclinic-4.0.5.jar > pet.log 
```

---

## 2. Configure Loki

installed Loki and configured `loki-config.yaml`

```yaml
auth_enabled: false

server:
  http_listen_port: 3100
  grpc_listen_port: 9095
  log_level: info

common:
  path_prefix: ./loki
  storage:
    filesystem:
      chunks_directory: ./loki/chunks
      rules_directory: ./loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: ./loki/index
    cache_location: ./loki/cache
    cache_ttl: 24h
  filesystem:
    directory: ./loki/chunks

compactor:
  working_directory: ./loki/compactor


limits_config:
  allow_structured_metadata: false
```

---

## 3. Configure Promtail

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 9096   
  log_level: info

positions:
  filename: ./promtail-positions.yaml

clients:
  - url: http://localhost:3100/loki/api/v1/push

scrape_configs:
  - job_name: spring-petclinic-logs
    static_configs:
      - targets:
          - localhost
        labels:
          job: spring-petclinic
          __path__: ./pet.log
```
Wait till loki is ready then proceed to promtail 

![lok](lokiready.png)

---

### 4. Start Promtail

```bash
promtail -config.file=promtail-config.yaml
```
![prom](promtail.png)

---

### 5. Verify Logs in Grafana

Added Loki as data-sourcee
![addlok](addloki.png)

Proceeded to explore and checked logs there 

`{job="spring-petclinic"}`

![verify](verify.png)
