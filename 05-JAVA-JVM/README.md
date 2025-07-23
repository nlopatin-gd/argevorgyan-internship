# Jenkins Deployment on Tomcat with JMX Monitoring
In this task I set up Apache Tomcat, deploying Jenkins as a WAR application, enabling JMX for monitoring, and managing JVM parameters. Each step is documented with appropriate screenshots.

---

## 1. Download and install Tomcat

- Installed **Apache Tomcat 10.1.**
- Installed jdk
- Set `JAVA_HOME` and started Tomcat.

**Screenshot:**  
![hom](scr3.png)
![tomstart](scr1.png)


---

## 2. Tomcat root page

- Opened http://localhost:8080 in browser. 
![root](scr2.png)

---

## 3. Identify process ports

Checked which ports the Java process was using:
:
- 8080 (HTTP)
- 8005 (shutdown)
![ports](scr4.png)

---

## 4. Remove def apps and access Jenkins

- Deleted default apps from `webapps/`
![rmapps](scr5.png)

- Restarted Tomcat and accessed Jenkins at `http://localhost:8080/jenkins`
![jenk](scr6.png)

---

## 5. Enable JMX in Tomcat

Created `setenv.sh`
![conf](scr7.png)

---

## 6. Check ports

```bash
lsof -i -nP | grep java
```

Expected ports:
- 8080
- 8005
- 9010 (JMX/RMI)  
![jmx ports](scr8.png)

---

## 7. Reduce JVM Memory: Expect Errors

Tested with small memory config:
![small](scr9.png)

Expectt: `OutOfMemoryError`. 
![err](scr10.png)

---

## 8. Increase JVM Memory & Enable GC

Set memory & garbage collector:
![inc](scr11.png)

Restarted Tomcat. Jenkins ran successfully.


---

## 9. Monitor Jenkins Using JConsole

Started `jconsole` and connected locally.

- Overview
![ov](over.png)
- Memory
![me](mem.png)
- Sum
![sum](sum.png)
- Connect by port
![po](scr13.png)

---

## 10. Run Jenkins Standalone 

Ran jenkins as standalone app (make sure jdk version supports it)
```bash
java -jar jenkins.war
``` 
![standalone Jenkins](stand.png)

---
## Links

- [Jenkins WAR](https://www.jenkins.io/download/)
- [Tomcat Docs](https://tomcat.apache.org/tomcat-10.1-doc/monitoring.html)
- [Jenkins Java Requirements](https://www.jenkins.io/redirect/java-support/)
