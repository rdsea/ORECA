#### Install the Prometheus PV:

- Change the `local.path` field in PersistentVolume definition of `prometheus-pv.yml` to specify the directory on the host node's filesystem where the actual data for the PersistentVolume will be stored.
- Change the `nodeAffinity` to ensure the PV is bound to Pods scheduled on the node, e.g., `yinfangchen-1` node.
- Apply the Prometheus PV:

```shell
kubectl apply -f prometheus-pv.yml -n observe
```

#### Install Prometheus:

```shell
cd prometheus/
helm install prometheus prometheus/ -n observe
```

#### Uninstall Prometheus:

```shell
helm uninstall prometheus -n observe
```

## Popular metrics

### Node

- CPU usage over time:

```promql
100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[1m]))
       * 100)
```

- Load average:

```promql
node_load1
node_load5
node_load15
```

- Memory usage:

```promql
100 -
(
  avg(node_memory_MemAvailable_bytes{job="node-exporter", instance="XXX.XXX.XXX.XXX:9100"}) /
  avg(node_memory_MemTotal_bytes{job="node-exporter", instance="XXX.XXX.XXX.XXX:9100"})
* 100
)
```

- Disk usage

```promql
rate(node_disk_read_bytes_total{job="node-exporter", instance="XXX.XXX.XXX.XXX:9100", device=~"(/dev/)?(mmcblk.p.+|nvme.+|rbd.+|sd.+|vd.+|xvd.+|dm-.+|md.+|dasd.+)"}[1m])

rate(node_disk_written_bytes_total{job="node-exporter", instance="XXX.XXX.XXX.XXX:9100", device=~"(/dev/)?(mmcblk.p.+|nvme.+|rbd.+|sd.+|vd.+|xvd.+|dm-.+|md.+|dasd.+)"}[1m])

rate(node_disk_io_time_seconds_total{job="node-exporter", instance="XXX.XXX.XXX.XXX:9100", device=~"(/dev/)?(mmcblk.p.+|nvme.+|rbd.+|sd.+|vd.+|xvd.+|dm-.+|md.+|dasd.+)"}[1m])
```

- Network

```promql
rate(node_network_receive_bytes_total{job="node-exporter", instance="XXX.XXX.XXX.XXX:9100", device!="lo"}[1m]) * 8
rate(node_network_transmit_bytes_total{job="node-exporter", instance="XXX.XXX.XXX.XXX:9100", device!="lo"}[1m]) * 8
```

