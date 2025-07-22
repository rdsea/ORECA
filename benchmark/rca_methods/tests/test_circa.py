import os
from pathlib import Path

import pytest
from rca_methods.circa import circa
from rca_methods.utility import download_data, read_data


@pytest.fixture
def sample_data():
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    data_path = base_path / "data.csv"
    if not data_path.exists():
        download_data(local_path=data_path)
    return read_data(data_path)


def test_circa_top_root_causes(sample_data):
    anomaly_detected_timestamp = 1692569339
    result = circa(sample_data, inject_time=anomaly_detected_timestamp, dataset="ob")

    root_causes = result["ranks"]
    print(root_causes[:5])
