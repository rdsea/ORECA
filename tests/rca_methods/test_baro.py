import os
from pathlib import Path

import pytest

from rca_methods.baro import baro
from rca_methods.utility import download_data, read_data


@pytest.fixture
def sample_data():
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    data_path = base_path / "data.csv"
    if not data_path.exists():
        download_data(local_path=data_path)
    return read_data(data_path)


def test_baro_top_root_causes(sample_data):
    anomaly_detected_timestamp = 1692569339
    result = baro(sample_data, anomaly_detected_timestamp)

    root_causes = result["ranks"]

    assert root_causes[:5] == [
        "emailservice_mem",
        "recommendationservice_mem",
        "cartservice_mem",
        "checkoutservice_latency",
        "cartservice_latency",
    ]


"time,adservice_cpu,cartservice_cpu,checkoutservice_cpu,currencyservice_cpu,emailservice_cpu,frontend_cpu,main_cpu,paymentservice_cpu,productcatalogservice_cpu,recommendationservice_cpu,redis_cpu,shippingservice_cpu,adservice_mem,cartservice_mem,checkoutservice_mem,currencyservice_mem,emailservice_mem,frontend_mem,main_mem,paymentservice_mem,productcatalogservice_mem,recommendationservice_mem,redis_mem,shippingservice_mem,adservice_workload,cartservice_workload,checkoutservice_workload,currencyservice_workload,emailservice_workload,frontend_workload,frontend-external_workload,paymentservice_workload,productcatalogservice_workload,recommendationservice_workload,shippingservice_workload,frontend_error,frontend-external_error,adservice_latency-50,cartservice_latency-50,checkoutservice_latency-50,currencyservice_latency-50,emailservice_latency-50,frontend_latency-50,paymentservice_latency-50,productcatalogservice_latency-50,recommendationservice_latency-50,shippingservice_latency-50,adservice_latency-90,cartservice_latency-90,checkoutservice_latency-90,currencyservice_latency-90,emailservice_latency-90,frontend_latency-90,paymentservice_latency-90,productcatalogservice_latency-90,recommendationservice_latency-90,shippingservice_latency-90"
