import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from prometheus_api_client import PrometheusConnect

from rca_methods.observer import (
    monitor_config,
    root_path,
)

NODE_METRICS = [
    "node:cpu_usage",
    "node:memory_usage_percentage",
    "node:disk_read",
    "node:disk_written",
    "node:disk_io_time",
    "node:network_receive",
    "node:network_transmit",
]
POD_METRICS = [
    "pod:cpu_usage",
    "pod:memory_usage",
]

SERVICE_METRICS = [
    "service:cpu_usage",
    "service:memory_usage",
    "service:network_receive",
    "service:network_transmit",
    "service:io",
    "service:p95_latency",
    "service:p75_latency",
    "service:p50_latency",
    "service:request_rate_per_second",
    "service:error_rate",
]

ALL_METRICS = NODE_METRICS + POD_METRICS + SERVICE_METRICS


def time_format_transform(time_to_transform):
    # transform time data from int to datetime
    if isinstance(time_to_transform, int):
        time_to_transform = datetime.fromtimestamp(time_to_transform)
    elif isinstance(time_to_transform, str):
        time_to_transform = int(time_to_transform)
        time_to_transform = datetime.fromtimestamp(time_to_transform)
    return time_to_transform


class PrometheusAPI:
    def __init__(self, url: str):
        self.client = PrometheusConnect(url, disable_ssl=True)

    # start_time: Union[int, datetime]
    # The start_time can be either int or datetime or string
    def query_range(
        self,
        metric_list: list[str],
        start_time: int | datetime | str,
        end_time: int | datetime | str,
        step: str = "10s",
        save_path: str = ".",
        save_to_file: bool = True,
    ):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_path = os.path.join(save_path, f"metric_{timestamp}.csv")
        start_time = time_format_transform(start_time)
        end_time = time_format_transform(end_time)
        return_pd = pd.DataFrame()
        for metric in metric_list:
            query = f"{metric}"
            data_raw = self.client.custom_query_range(
                query, start_time, end_time, step=step
            )
            if len(data_raw) == 0:
                continue
            timestamp_list = []
            value_list = []
            if metric in NODE_METRICS:
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
                for data in data_raw:
                    for d in data["values"]:
                        if "workload" in data["metric"]:
                            service_name_list.append(data["metric"]["workload"])
                        elif "service_name" in data["metric"]:
                            service_name_list.append(data["metric"]["service_name"])
                        timestamp_list.append(int(d[0]))
                        value_list.append(round(float(d[1]), 3))
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
            else:
                raise ValueError(f"Unknown metric category: {metric}")

            if return_pd.empty:
                return_pd = pivoted  # First metric
            else:
                return_pd = pd.merge(return_pd, pivoted, on="timestamp", how="outer")

        if save_to_file:
            if os.path.exists(save_path):
                with open(save_path, "a", encoding="utf-8", newline="") as f:
                    return_pd.to_csv(f, header=False, index=False)
            else:
                return_pd.to_csv(save_path, index=False)
            logging.info(f"METRIC SAVE TO {save_path}")
        logging.info("QUERY DONE")
        return return_pd

    def query_all(
        self,
        start_time: int | datetime | str,
        end_time: int | datetime | str,
        step: str = "10s",
    ):
        return self.query_range(
            ALL_METRICS, start_time, end_time, step, save_to_file=False
        )


if __name__ == "__main__":
    prom = PrometheusAPI(monitor_config["prometheus_url"])

    # Define time range for exporting metrics
    end_time = datetime.now()
    start_time = end_time - timedelta(minutes=15)
    # injection_time = 1753213321

    # Define the save path for metrics
    save_path = root_path / "metrics_output"

    prom.query_range(ALL_METRICS, start_time, end_time, step="5s")
