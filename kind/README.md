## Deployment Steps

### 1. Build the Custom KIND Image

The Dockerfile in this directory is designed specifically for Ubuntu running under WSL2 (amd64). **Please refer to this Dockerfile** to build an image that is compatible with your own machine

Build the custom image using:

```bash
docker build -t your_dockerhub_username/aiopslab-kind:latest -f kind/Dockerfile .
```

> **Note:** Replace `your_dockerhub_username` with your Docker Hub account if pushing the image.

### 2. (Optional) Push the Image to Dockerhub

If you wish to publish your custom image and have it referenced by the kind configuration file, push it to Docker Hub:

```bash
docker push your_dockerhub_username/aiopslab-kind:latest
```

Remember to update the `kind-config.yaml` file with your image name if you are using your own published image.

After finishing cluster creation, proceed to the next "Update config.yml" step.

---

## **Troubleshooting**

- **Cluster Creation Failures:**  
  Check that Docker is correctly installed and that your system has enough resources (CPU, memory). Examine the output of `kind export logs <cluster-name>` for details.

- **Deployment Problems:**  
  Use `kubectl logs <pod-name>` to view pod logs and diagnose application issues. Make sure that your `kind-config.yaml` file references the correct image.

---
