# Setup k8s for edge-cloud

## K8s in GCP

- Run the Terraform script, maybe you will need to rerun it if it fails

```bash
terraform apply
```

- Install the openyurt following [instruction](https://openyurt.io/docs/installation/manually-setup)

```bash
helm repo add openyurt https://openyurtio.github.io/openyurt-helm
helm upgrade --install yurt-manager -n kube-system openyurt/yurt-manager
```

- If fail with error, try to check if the yurt-manager is up or not. Can try to follow this [issue](https://github.com/openyurtio/openyurt/issues/2267)

```bash
Error: UPGRADE FAILED: failed to create resource: Internal error occurred: failed calling webhook "mutate.apps.v1alpha1.yurtstaticset.openyurt.io": failed to call webhook: Post "https://yurt-manager-webhook-service.kube-system.svc:443/mutate-apps-openyurt-io-v1alpha1-yurtstaticset?timeout=10s": dial tcp <INTERNAL_SERVICE_IP>:443: connect: connection refused
```
