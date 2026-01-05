# Kubernetes Deployment Instructions
This directory contains the Kubernetes manifests and instructions to deploy the project's services and components in a Kubernetes cluster.

## Prerequisites
- A running Google Cloud Kubernetes cluster
- kubectl configured to interact with your cluster
- Docker installed for building container images
- Access to Google Container Registry (GCR) for pushing Docker images
- Google Cloud SDK installed and authenticated
- Access to the Google Cloud project where the cluster is hosted

## Component Overview
The following components are defined in the Kubernetes manifests:
- **Admin Service**: `/k8s/admin-api.yaml` - Deployment and service for the Admin component.
- **FER Service**: `/k8s/face-emotion.yaml` - Deployment and service for the FER component.
- **VER Service**: `/k8s/voice-emotion.yaml` - Deployment and service for the VER component.
- **Aggregator Service**: `/k8s/aggregator.yaml` - StatefulSet and service for the Aggregator component.
- **Ingress Controller**: `/k8s/ingress.yaml` - Ingress resource for routing traffic to the services. Currently configured for NGINX Ingress Controller.
- **Build and Push Script**: `/k8s/build-push.sh` - Script to build and push Docker images of components to GCR.

## Deployment Steps
1. **Build Docker Images**: Build the Docker images for each service using the provided Dockerfiles. Tag the images appropriately for GCR, or use the provided `/k8s/build-push.sh` script to build and push images.
	
	- build and push manually:
	```bash
	docker buildx build --platform linux/amd64,linux/arm64 -f "<Dockerfile-path>" -t gcr.io/[PROJECT-ID]/[IMAGE-NAME]:[TAG] . --push
	```

	- or use the provided script `/k8s/build-push.sh` but **before running update it with your project ID, repo name and region**:
	```bash
	./k8s/build-push.sh <fer/ver/aggregator/admin/trainer>
	```

2. **Deploy to Kubernetes**: Apply the Kubernetes manifests to deploy the services to your cluster.

	```bash
	kubectl apply -f /k8s/
	```

	If only the image has been updated and no changes were made to the manifests - rollout restart the deployments:
	```bash
	kubectl rollout restart deployment/<deployment-name>
	```

3. **Verify Deployment**: Check the status of the pods and services to ensure they are running correctly.

	```bash
	# For Deployments
	kubectl rollout restart deployment/<deployment-name>

	# For StatefulSets
	kubectl rollout restart statefulset/<statefulset-name>

	kubectl get pods
	kubectl get services
	```
