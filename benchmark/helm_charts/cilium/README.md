# Deploy Cilium cluster mesh

- [link](https://docs.cilium.io/en/stable/network/clustermesh/clustermesh/)

## Prerequisites

- Remember that each cluster should have unique podCIDR: following setting in cilium helm value, for each cluster, use the CIDR that match the cluster id. For example, cluster id 1 => XXX.XXX.XXX.XXX/8
