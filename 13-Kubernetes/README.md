# Spring PetClinic Deployment on GKE

## Task

![task](task.png)

## **1. Create GKE Cluster**
![cluster1](cluster1.png)

![cluster2](cluster2.png)

![cluste3](clutsercreated.png)


---

## **2. Installed GKE Auth Plugin**

```bash
gcloud components install gke-gcloud-auth-plugin

gcloud container clusters get-credentials arpetclinic-cluster --region europe-central2 --project gd-gcp-internship-devops
```

![gke](gkecomppodes.png)


## **3. Build Kubernetes**

deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: petclinic
  labels:
    app: petclinic
spec:
  replicas: 2
  selector:
    matchLabels:
      app: petclinic
  template:
    metadata:
      labels:
        app: petclinic
    spec:
      containers:
      - name: petclinic
        image: europe-central2-docker.pkg.dev/gd-gcp-internship-devops/arpetclinic-repo/spring-petclinic-ar:latest
        ports:
        - containerPort: 8080
        readinessProbe:
          httpGet:
            path: /
            port: 8080
          initialDelaySeconds: 10
          periodSeconds: 5
```
Service (service.yaml)

```yaml
apiVersion: v1
kind: Service
metadata:
  name: petclinic-service
spec:
  selector:
    app: petclinic
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8080
  type: LoadBalancer
  ```

## **4. Apply** 

kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

```kubectl get svc petclinic-service```

![pod](pods.png)

⸻

## **5. Verify**


![get](getip.png)
![result](result.png)
