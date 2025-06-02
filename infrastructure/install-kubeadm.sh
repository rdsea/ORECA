#!/bin/bash

sudo apt install netcat-openbsd

# Install kubeadm
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg

sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.30/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg

echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.30/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list

sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl

sudo systemctl enable --now kubelet

# Install containerd https://www.hostafrica.com/blog/servers/kubernetes-cluster-debian-11-containerd/
cat <<EOF | sudo tee /etc/modules-load.d/containerd.conf
overlay
br_netfilter
EOF

sudo modprobe overlay
sudo modprobe br_netfilter

cat <<EOF | sudo tee /etc/sysctl.d/99-kubernetes-cri.conf
net.bridge.bridge-nf-call-iptables = 1
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-ip6tables = 1
EOF

sudo sysctl --system

sudo apt-get install containerd -y

sudo mkdir -p /etc/containerd
containerd config default | tee /etc/containerd/config.toml >/dev/null 2>&1

cat <<EOF | sudo tee /etc/containerd/config.toml
version = 2

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc]
runtime_type = "io.containerd.runc.v2"

[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]
SystemdCgroup = true
EOF

sudo systemctl restart containerd
kubeadm join REDACTED_IP:6443 --token c65ii1.8o3tx1fr65shl3pj --discovery-token-ca-cert-hash sha256:2b823d173adc961220afee4075925ba5b019002db35213f98aea87035dea7101 --kubernetes-version=v1.30.10

curl -sfL https://get.k3s.io | K3S_URL=https://REDACTED_IP:6443 K3S_TOKEN=K103ee3a74481c78fb2ff428953509022b3f26eb7c123342d5f5abfe90a82592c36::server:232672d66eea77692c852e8a2894b02b sh -s - --docker
