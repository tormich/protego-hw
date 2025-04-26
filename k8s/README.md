# Kubernetes Deployment for Protego HW

This directory contains Kubernetes manifests for deploying the Protego HW application.

## Components

- **PostgreSQL Database**: Persistent database for storing drug data and analytics results
- **API Service**: FastAPI application exposing CRUD endpoints
- **Scraper CronJob**: Runs daily to scrape drug data
- **Analytics CronJob**: Runs every 2 days to analyze the scraped data

## Prerequisites

- Kubernetes cluster (local or cloud-based)
- kubectl configured to communicate with your cluster
- Container registry for storing your Docker images

## Building and Pushing Images

Before deploying to Kubernetes, you need to build and push the Docker images:

```bash
# Build images
docker build -t protego-hw-api:latest -f api/Dockerfile .
docker build -t protego-hw-scraper:latest -f scraper/Dockerfile .
docker build -t protego-hw-analytics:latest -f analytics/Dockerfile .

# Tag images for your registry (replace with your registry)
docker tag protego-hw-api:latest your-registry/protego-hw-api:latest
docker tag protego-hw-scraper:latest your-registry/protego-hw-scraper:latest
docker tag protego-hw-analytics:latest your-registry/protego-hw-analytics:latest

# Push images
docker push your-registry/protego-hw-api:latest
docker push your-registry/protego-hw-scraper:latest
docker push your-registry/protego-hw-analytics:latest
```

## Deployment

Update the image references in the deployment and cronjob YAML files to point to your registry, then deploy using:

```bash
kubectl apply -k .
```

Or apply individual files:

```bash
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f postgres-pvc.yaml
kubectl apply -f postgres-deployment.yaml
kubectl apply -f postgres-service.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f api-service.yaml
kubectl apply -f api-ingress.yaml
kubectl apply -f scraper-cronjob.yaml
kubectl apply -f analytics-cronjob.yaml
```

## Accessing the API

The API is exposed through an Ingress resource. You can access it at:

```
http://api.protego-hw.local
```

Replace `api.protego-hw.local` with your actual domain or add it to your hosts file for local development.

## Monitoring CronJobs

To check the status of the CronJobs:

```bash
kubectl get cronjobs -n protego-hw
kubectl get jobs -n protego-hw
```

To view logs from a job:

```bash
kubectl logs job/scraper-<job-id> -n protego-hw
kubectl logs job/analytics-<job-id> -n protego-hw
```

## Configuration

- Update `configmap.yaml` for non-sensitive configuration
- Update `secret.yaml` for sensitive data (use proper secret management in production)
- Adjust resource requests/limits in deployment files based on your workload requirements
