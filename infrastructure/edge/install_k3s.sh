#!/bin/bash
# Install k3s master
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC='--flannel-backend=none --disable-network-policy --write-kubeconfig-mode "0644" --disable servicelb,traefik' sh -

# Intall k3s agent
curl -sfL https://get.k3s.io | K3S_URL=https:// K3S_TOKEN="<token>" <server_ip >:6443 sh -

# Copy kubeconfig and set permission
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config && chown "$USER" ~/.kube/config && chmod 600 ~/.kube/config && export KUBECONFIG=~/.kube/config
