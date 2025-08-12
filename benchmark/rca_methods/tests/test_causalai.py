import os
from pathlib import Path

import pandas as pd
import pytest
from rca_methods.causalai import CausalAI
from rca_methods.utility import download_data, read_data


@pytest.fixture
def sample_data():
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    data_path = base_path / "data.csv"
    if not data_path.exists():
        download_data(local_path=data_path)
    return read_data(data_path)


# def test_causalai_top_root_causes(sample_data):
#     anomaly_detected_timestamp = 1692569339
#     result = causalai(sample_data, inject_time=anomaly_detected_timestamp, dataset="ob")
#
#     root_causes = result["ranks"]
#     print(root_causes[:5])


@pytest.fixture
def own_sample_data() -> pd.DataFrame:
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    data_path = base_path / "network_delay_preprocessing.csv"
    return read_data(data_path)


@pytest.fixture
def create_causalai() -> CausalAI:
    return CausalAI()


def test_causalai_top_root_causes_own(own_sample_data, create_causalai):
    injection_time = 1753213321
    result = create_causalai.run(
        own_sample_data, top_k=5, injection_time=injection_time
    )

    print(result[:5])
