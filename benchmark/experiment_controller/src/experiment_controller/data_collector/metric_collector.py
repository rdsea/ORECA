import logging
import os
from datetime import datetime
from pathlib import Path

import pandas as pd
from prometheus_api_client import PrometheusConnect

from experiment_controller.logger import logger

# Node-level metrics
RAW_METRICS = [
    'node_cpu_seconds_total{job="node-exporter", mode=~"idle|iowait|steal"}',
    'node_memory_MemAvailable_bytes{job="node-exporter"}',
    'node_memory_MemTotal_bytes{job="node-exporter"}',
    'node_disk_read_bytes_total{job="node-exporter", device=~"(/dev/)?(mmcblk.p.+|nvme.+|rbd.+|sd.+|vd.+|xvd.+|dm-.+|md.+|dasd.+)"}',
    'node_disk_written_bytes_total{job="node-exporter", device=~"(/dev/)?(mmcblk.p.+|nvme.+|rbd.+|sd.+|vd.+|xvd.+|dm-.+|md.+|dasd.+)"}',
    'node_disk_io_time_seconds_total{job="node-exporter", device=~"(/dev/)?(mmcblk.p.+|nvme.+|rbd.+|sd.+|vd.+|xvd.+|dm-.+|md.+|dasd.+)"}',
    'node_network_receive_bytes_total{job="node-exporter", device!="lo"}',
    'node_network_transmit_bytes_total{job="node-exporter", device!="lo"}',
    'node_namespace_pod_container:container_cpu_usage_seconds_total:sum_rate5m{container!="",namespace="default",pod!=""}',
    'container_memory_working_set_bytes{job="kubelet", metrics_path="/metrics/cadvisor", namespace="default", container!="", image!=""}',
    'namespace_workload_pod:kube_pod_owner:relabel{namespace="default"}',
    'container_network_receive_bytes_total{job="kubelet", metrics_path="/metrics/cadvisor",namespace="default"}',
    'container_network_transmit_bytes_total{job="kubelet", metrics_path="/metrics/cadvisor",namespace="default"}',
    'probe_icmp_duration_seconds{phase="rtt"}',
    'container_sockets{namespace="default"}',
    'container_blkio_device_usage_total{job="kubelet", metrics_path="/metrics/cadvisor",namespace="default"}',
]
NODE_METRICS = [
    "node:cpu_usage",
    "node:memory_usage_percentage",
    "node:disk_read",
    "node:disk_written",
    "node:disk_io_time",
    "node:network_receive",
    "node:network_transmit",
]

# Pod-level metrics
POD_METRICS = [
    "pod:cpu_usage",
    "pod:memory_usage",
]

# Service-level metrics
SERVICE_METRICS = [
    "service:cpu_usage",
    "service:memory_usage",
    "service:network_receive",
    "service:network_transmit",
    "service:io",
    "service:rtt",
    "service:p95_latency",
    "service:p75_latency",
    "service:p50_latency",
    "service:request_rate_per_second",
    "service:error_rate",
]

# All metrics combined
ALL_METRICS = NODE_METRICS + POD_METRICS + SERVICE_METRICS + RAW_METRICS


def time_format_transform(time_to_transform):
    """Transform time data from int or string to datetime object.

    Args:
        time_to_transform (int | str): The time to transform.

    Returns:
        datetime: The transformed time as a datetime object.
    """
    # transform time data from int to datetime
    if isinstance(time_to_transform, int):
        time_to_transform = datetime.fromtimestamp(time_to_transform)
    elif isinstance(time_to_transform, str):
        time_to_transform = int(time_to_transform)
        time_to_transform = datetime.fromtimestamp(time_to_transform)
    return time_to_transform


class MetricCollector:
    """A wrapper for the Prometheus API client."""

    def __init__(self, url: str):
        """Initialize the Prometheus API client.

        Args:
            url (str): The URL of the Prometheus server.
        """
        self.client = PrometheusConnect(url, disable_ssl=True)

    def query_range(
        self,
        metric_list: list[str],
        start_time: int | datetime | str,
        end_time: int | datetime | str,
        step: str = "10s",
        save_path: str | Path = ".",
        experiment_name: str | None = None,
        save_to_file: bool = True,
        metric_type: str = "processed",  # Added metric_type parameter to differentiate handling
    ):
        """Query a range of metrics from Prometheus.

        Args:
            metric_list (list[str]): A list of metrics to query.
            start_time (int | datetime | str): The start time of the query range.
            end_time (int | datetime | str): The end time of the query range.
            step (str, optional): The step size for the query. Defaults to "10s".
            save_path (str, optional): The path to save the metrics to. Defaults to ".".
            save_to_file (bool, optional): Whether to save the metrics to a file. Defaults to True.
            metric_type (str, optional): The type of metrics to process ("processed" for NODE/POD/SERVICE, "raw" for raw metrics). Defaults to "processed".

        Returns:
            pd.DataFrame: A DataFrame containing the queried metrics.
        """
        if experiment_name:
            if metric_type == "raw":
                save_path = os.path.join(
                    save_path, f"{experiment_name}_raw_metrics.csv"
                )
            else:
                save_path = os.path.join(save_path, f"{experiment_name}.csv")
        else:
            if metric_type == "raw":
                save_path = os.path.join(save_path, "raw_metrics.csv")
            else:
                save_path = os.path.join(save_path, "metric.csv")

        start_time = time_format_transform(start_time)
        end_time = time_format_transform(end_time)
        return_pd = pd.DataFrame()

        for metric in metric_list:
            logger.debug(f"Querying metric {metric}")
            query = f"{metric}"
            data_raw = self.client.custom_query_range(
                query, start_time, end_time, step=step
            )
            logger.debug(data_raw)
            if len(data_raw) == 0:
                logger.debug(f"No data for metric {metric}")
                continue
            timestamp_list = []
            value_list = []

            # Handle raw metrics separately - just save the raw data without processing
            if metric in RAW_METRICS and metric_type == "raw":
                job_list = []
                instance_list = []
                device_list = []
                container_list = []
                namespace_list = []
                pod_list = []

                for data in data_raw:
                    for d in data["values"]:
                        timestamp_list.append(int(d[0]))
                        value_list.append(round(float(d[1]), 3))

                        # Extract common labels
                        job = data["metric"].get("job", "unknown")
                        instance = data["metric"].get("instance", "unknown")
                        device = data["metric"].get("device", "unknown")
                        container = data["metric"].get("container", "unknown")
                        namespace = data["metric"].get("namespace", "unknown")
                        pod = data["metric"].get("pod", "unknown")

                        job_list.append(job)
                        instance_list.append(instance)
                        device_list.append(device)
                        container_list.append(container)
                        namespace_list.append(namespace)
                        pod_list.append(pod)

                dt = pd.DataFrame(
                    {
                        "timestamp": timestamp_list,
                        "metric_name": [metric] * len(timestamp_list),
                        "job": job_list,
                        "instance": instance_list,
                        "device": device_list,
                        "container": container_list,
                        "namespace": namespace_list,
                        "pod": pod_list,
                        "value": value_list,
                    }
                )

                if return_pd.empty:
                    return_pd = dt
                else:
                    return_pd = pd.concat([return_pd, dt], ignore_index=True)

            elif metric in NODE_METRICS:
                instance_list = []
                disk_list = []
                network_interface_list = []
                for data in data_raw:
                    for d in data["values"]:
                        if "disk" in metric:
                            disk_list.append(data["metric"]["device"])
                        elif "network" in metric:
                            network_interface_list.append(data["metric"]["device"])
                        timestamp_list.append(int(d[0]))
                        value_list.append(round(float(d[1]), 3))
                        instance_list.append(data["metric"]["instance"])

                dt = pd.DataFrame(
                    {
                        "timestamp": timestamp_list,
                        "instance": instance_list,
                        "value": value_list,
                    }
                )

                if "disk" in metric:
                    dt["disk_name"] = disk_list
                    dt["node_metric"] = (
                        dt["instance"].str.replace(":9100", "", regex=False)
                        + f"_{metric}_"
                        + dt["disk_name"]
                    )
                elif "network" in metric:
                    dt["network_interface"] = network_interface_list
                    dt["node_metric"] = (
                        dt["instance"].str.replace(":9100", "", regex=False)
                        + f"_{metric}_"
                        + dt["network_interface"]
                    )
                else:
                    dt["node_metric"] = (
                        dt["instance"].str.replace(":9100", "", regex=False)
                        + f"_{metric}"
                    )

                pivoted = dt.pivot(
                    index="timestamp", columns="node_metric", values="value"
                ).reset_index()

            elif metric in POD_METRICS:
                pod_list = []
                for data in data_raw:
                    for d in data["values"]:
                        timestamp_list.append(int(d[0]))
                        value_list.append(round(float(d[1]), 3))
                        pod_list.append(data["metric"]["pod"])
                dt = pd.DataFrame(
                    {
                        "timestamp": timestamp_list,
                        "pod": pod_list,
                        "value": value_list,
                    }
                )

                dt["pod_metric"] = dt["pod"] + f"_{metric}"

                pivoted = dt.pivot(
                    index="timestamp", columns="pod_metric", values="value"
                ).reset_index()
            elif metric in SERVICE_METRICS:
                service_name_list = []
                span_name = ""
                try:
                    for data in data_raw:
                        for d in data["values"]:
                            if "span_name" in data["metric"]:
                                if "span_kind" in data["metric"]:
                                    span_name = f"{data['metric']['span_kind']}_{(data['metric']['span_name']).replace(' ', '_')}"
                                else:
                                    span_name = data["metric"]["span_name"]
                            if "workload" in data["metric"]:
                                service_name_list.append(data["metric"]["workload"])
                            elif "service" in data["metric"]:
                                # service_name_list.append(data["metric"]["service"])
                                service_name_list.append(
                                    f"{data['metric']['service']}_{span_name}"
                                    if span_name
                                    else data["metric"]["service"]
                                )
                            timestamp_list.append(int(d[0]))
                            value_list.append(float(d[1]))
                    dt = pd.DataFrame(
                        {
                            "timestamp": timestamp_list,
                            "service_name": service_name_list,
                            "value": value_list,
                        }
                    )
                    dt["service_metric"] = dt["service_name"] + f"_{metric}"

                    pivoted = dt.pivot(
                        index="timestamp", columns="service_metric", values="value"
                    ).reset_index()
                except Exception:
                    logger.exception("Fail when processing SERVICE_METRICS")
            else:
                raise ValueError(f"Unknown metric category: {metric}")

            # Apply pivot/merge logic for processed metrics that are not raw
            if metric_type != "raw" and metric not in RAW_METRICS:
                if return_pd.empty:
                    return_pd = pivoted  # First metric
                else:
                    logger.debug(pivoted.columns)
                    logger.debug(return_pd.columns)
                    return_pd = pd.merge(
                        return_pd, pivoted, on="timestamp", how="outer"
                    )
            # For raw metrics, we already have the data in return_pd directly

        if save_to_file:
            # For raw metrics, always include header as the structure is different and typically saved to separate file
            # For processed metrics, include header only if file doesn't exist yet (first write)
            include_header = (
                not os.path.exists(save_path) if metric_type != "raw" else True
            )
            return_pd.to_csv(save_path, index=False, header=include_header)
            logging.info(f"METRIC SAVE TO {save_path}")
        logging.info("QUERY DONE")
        return return_pd

    def query_all(
        self,
        start_time: int | datetime | str,
        end_time: int | datetime | str,
        step: str = "10s",
    ):
        """Query all metrics from Prometheus.

        Args:
            start_time (int | datetime | str): The start time of the query range.
            end_time (int | datetime | str): The end time of the query range.
            step (str, optional): The step size for the query. Defaults to "10s".

        Returns:
            pd.DataFrame: A DataFrame containing the queried metrics.
        """
        return self.query_range(
            ALL_METRICS, start_time, end_time, step, save_to_file=False
        )
