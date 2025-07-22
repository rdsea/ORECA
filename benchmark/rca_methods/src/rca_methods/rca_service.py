import os
from datetime import datetime, timedelta

import pandas as pd
import yaml
from fastapi import FastAPI
from pydantic import BaseModel

from rca_methods.observer import monitor_config
from rca_methods.observer.metric_api import PrometheusAPI
from rca_methods.rca_factory import RCAFactory

prom = PrometheusAPI(monitor_config["prometheus_url"])
app = FastAPI()

METRICS = [
    "node:cpu_usage",
    "node:memory_usage_percentage",
    "node:disk_read",
    "node:disk_written",
    "node:disk_io_time",
    "node:network_receive",
    "node:network_transmit",
    "pod:cpu_usage",
    "pod:memory_usage",
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


class RCARequest(BaseModel):
    injection_time: int | None = None
    experiment: str


class RCAResponse(BaseModel):
    root_causes: list[tuple[str, float]]


with open("config.yaml") as f:
    config: dict = yaml.safe_load(f)

rca_type = config.get("rca_method", "dummy")
top_k = config.get("top_k", 5)
rca_chosen = RCAFactory.create(rca_type)


@app.post("/find_rca", response_model=RCAResponse)
def find_rca(request: RCARequest):
    obs_data = query_data(request.injection_time)
    root_causes = rca_chosen.run(
        obs_data,
        top_k,
        request.injection_time,
    )
    os.mkdir("./results")
    with open(f"{request.experiment}.txt", "w") as f:
        f.write(f"{root_causes}")
    return RCAResponse(root_causes=root_causes)


def query_data(injection_time: int | None) -> pd.DataFrame:
    end_time = datetime.now()
    if injection_time:
        start_time = datetime.fromtimestamp(injection_time) - timedelta(minutes=5)
    else:
        start_time = end_time - timedelta(minutes=10)
    return prom.query_range(METRICS, start_time, end_time, save_to_file=False)
