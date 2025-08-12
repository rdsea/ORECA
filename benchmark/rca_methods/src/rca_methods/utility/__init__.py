import json
import os
import sys
from pathlib import Path

# import zipfile
# from os.path import join
import numpy as np
import pandas as pd
import requests

# from sklearn.preprocessing import StandardScaler
from tqdm import tqdm

ENCODING = "utf-8"


def is_py310() -> bool:
    """Checks if the current Python version is 3.10.

    Returns:
        bool: True if Python version is 3.10, False otherwise.
    """
    return sys.version_info.major == 3 and sys.version_info.minor == 10


def is_py38() -> bool:
    """Checks if the current Python version is 3.8.

    Returns:
        bool: True if Python version is 3.8, False otherwise.
    """
    return sys.version_info.major == 3 and sys.version_info.minor == 8


def dump_json(filename: str, data):
    """Dumps data into a JSON file.

    Args:
        filename (str): The path to the JSON file.
        data: The data to be dumped.
    """
    with open(filename, "w", encoding=ENCODING) as obj:
        json.dump(data, obj, ensure_ascii=False, indent=2, sort_keys=True)


def load_json(filename: str):
    """Loads data from a JSON file.

    Args:
        filename (str): The path to the JSON file.

    Returns:
        Any: The loaded data.
    """
    with open(filename, encoding=ENCODING) as obj:
        return json.load(obj)


def convert_adjacency_matrix(
    adj: np.ndarray, node_names: list[str]
) -> tuple[np.ndarray, list[str]]:
    """Converts a metric-level adjacency matrix to a service-level adjacency matrix.

    Args:
        adj (np.ndarray): The metric-level adjacency matrix.
        node_names (list[str]): A list of node names corresponding to the adjacency matrix.

    Returns:
        tuple[np.ndarray, list[str]]: A tuple containing the service-level adjacency matrix and a list of service names.
    """
    services = list({name.split("_")[0] for name in node_names})
    # print(services)
    num_services = len(services)

    service_adj = np.zeros((num_services, num_services))

    for i in range(adj.shape[0]):
        for j in range(adj.shape[0]):
            if adj[i][j] == 1:
                service_adj[services.index(node_names[i].split("_")[0])][
                    services.index(node_names[j].split("_")[0])
                ] = 1

    # remove cycles
    for i in range(num_services):
        service_adj[i][i] = 0

    return service_adj, services  # services is node_names but for services


def download_data(remote_url: str | None = None, local_path: str | None = None):
    """Downloads data from a remote URL to a local path.

    Args:
        remote_url (str | None, optional): The URL of the remote file. Defaults to a sample CSV file.
        local_path (str | None, optional): The local path to save the file. Defaults to "data.csv".
    """
    if remote_url is None:
        remote_url = "https://github.com/phamquiluan/baro/releases/download/0.0.4/simple_data.csv"
    if local_path is None:
        local_path = "data.csv"

    response = requests.get(remote_url, stream=True)
    total_size_in_bytes = int(response.headers.get("content-length", 0))
    block_size = 1024  # 1 Kibibyte

    progress_bar = tqdm(
        desc=f"Downloading {local_path}",
        total=total_size_in_bytes,
        unit="iB",
        unit_scale=True,
    )

    with open(local_path, "wb") as ref:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            ref.write(data)

    progress_bar.close()
    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print("ERROR, something went wrong")


def download_metric_sample(
    remote_url: str | None = None, local_path: str | None = None
):
    """Downloads a sample metric case.

    Args:
        remote_url (str | None, optional): The URL of the remote file. Defaults to a sample CSV file.
        local_path (str | None, optional): The local path to save the file. Defaults to "data.csv".
    """
    if remote_url is None:
        remote_url = "https://github.com/phamquiluan/baro/releases/download/0.0.4/simple_data.csv"
    if local_path is None:
        local_path = "data.csv"

    download_data(remote_url, local_path)


def read_data(data_path: str | Path, strip: bool = True) -> pd.DataFrame:
    """Reads CSV data for root cause analysis and performs basic preprocessing.

    Args:
        data_path (str): The path to the CSV data file.
        strip (bool, optional): Whether to strip extra columns (currently unused). Defaults to True.

    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """
    data = pd.read_csv(data_path)
    os.path.dirname(data_path)

    ############# PREPROCESSING ###############
    if "time.1" in data:
        data = data.drop(columns=["time.1"])
    data = data.replace([np.inf, -np.inf], np.nan)
    data = data.ffill()
    data = data.fillna(0)

    # # remove latency-50 columns
    # data = data.loc[:, ~data.columns.str.endswith("latency-50")]
    # # rename latency-90 columns to latency
    # data = data.rename(
    #     columns={
    #         c: c.replace("_latency-90", "_latency")
    #         for c in data.columns
    #         if c.endswith("_latency-90")
    #     }
    # )

    return data
