import logging
import os
from pathlib import Path

import pandas as pd
import pytest
from rca_methods.baro import Baro
from rca_methods.utility import download_data, read_data


@pytest.fixture
def sample_data():
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    data_path = base_path / "data.csv"
    if not data_path.exists():
        download_data(local_path=data_path)
    return read_data(data_path)


@pytest.fixture
def own_sample_data() -> pd.DataFrame:
    base_path = Path(os.path.dirname(os.path.abspath(__file__)))
    data_path = base_path / "cpu_3x_rqs.csv"
    return read_data(data_path)


@pytest.fixture
def create_baro() -> Baro:
    return Baro()


def test_own_baro_top_root_causes(own_sample_data, create_baro):
    injection_time = 1753213321
    result = create_baro.run(own_sample_data, top_k=5, injection_time=injection_time)
    # previous = [
    #     "efficientnetb0-7c8ddf759c-nbwsz_pod:memory_usage",
    #     "XXX.XXX.XXX.XXX_node:network_transmit_lxc14a3877ba9b4",
    #     "XXX.XXX.XXX.XXX_node:disk_read_sda",
    #     "XXX.XXX.XXX.XXX_node:network_receive_lxc14a3877ba9b4",
    #     "XXX.XXX.XXX.XXX_node:disk_read_dm-0",
    # ]
    logging.info(f"Own result {result}")


# def test_baro_top_root_causes(sample_data, create_baro):
#     anomaly_detected_timestamp = 1692569339
#     data = sample_data
#     data["timestamp"] = data["time"]
#
#     data = data.loc[:, ~data.columns.str.endswith("_latency-50")]
#     data = data.rename(
#         columns={
#             c: c.replace("_latency-90", "_latency")
#             for c in data.columns
#             if c.endswith("_latency-90")
#         }
#     )
#     result = create_baro.run(data, injection_time=anomaly_detected_timestamp)
#
#     logging.info(result)
#
#     assert result[:5] == [
#         "emailservice_mem",
#         "recommendationservice_mem",
#         "cartservice_mem",
#         "checkoutservice_latency",
#         "cartservice_latency",
#     ]


# def test_baro_top_root_causes_origin(sample_data):
#     anomaly_detected_timestamp = 1692569339
#     data = sample_data
#     # NOTE: this follows the preprocessing original paper
#     data = data.loc[:, ~data.columns.str.endswith("_latency-50")]
#     data = data.rename(
#         columns={
#             c: c.replace("_latency-90", "_latency")
#             for c in data.columns
#             if c.endswith("_latency-90")
#         }
#     )
#     result = baro(data, anomaly_detected_timestamp)
#
#     # print(result)
#     root_causes = result["ranks"]
#     logging.info(root_causes[:5])
#     assert root_causes[:5] == [
#         "emailservice_mem",
#         "recommendationservice_mem",
#         "cartservice_mem",
#         "checkoutservice_latency",
#         "cartservice_latency",
#     ]
