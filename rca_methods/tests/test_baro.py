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
