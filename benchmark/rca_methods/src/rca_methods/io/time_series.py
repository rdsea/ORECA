import pandas as pd

KPI_COLUMN = ["latency", "request_rate_per_second", "error_rate"]


def drop_constant(df: pd.DataFrame) -> pd.DataFrame:
    """Drops columns from a DataFrame that have only one unique value (constant columns).

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with constant columns dropped.
    """
    return df.loc[:, (df != df.iloc[0]).any()]


def drop_near_constant(df: pd.DataFrame, threshold: float = 0.1) -> pd.DataFrame:
    """Drops columns from a DataFrame that are nearly constant.

    A column is considered nearly constant if the proportion of its values that are
    different from the first value is below a given threshold.

    Args:
        df (pd.DataFrame): The input DataFrame.
        threshold (float, optional): The threshold for considering a column as near constant. Defaults to 0.1.

    Returns:
        pd.DataFrame: The DataFrame with nearly constant columns dropped.
    """
    return df.loc[:, (df != df.iloc[0]).mean() > threshold]


def drop_time(df: pd.DataFrame) -> pd.DataFrame:
    """Drops 'time' or 'Time' columns from a DataFrame if they exist.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with 'time' or 'Time' columns dropped.
    """
    if "time" in df:
        df = df.drop(columns=["time"])
    elif "Time" in df:
        df = df.drop(columns=["Time"])
    return df


def drop_extra(df: pd.DataFrame) -> pd.DataFrame:
    """Drops specific columns from a DataFrame based on predefined patterns.

    This function removes columns that contain 'frontend-external' or start with
    'main_', 'PassthroughCluster_', 'redis_', 'rabbitmq', 'queue', or 'session'.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with specified extra columns dropped.
    """
    # remove cols has "frontend-external" in name
    # remove cols start with "main_", "PassthroughCluster_", etc.
    for col in df.columns:
        if (
            "frontend-external" in col
            or col.startswith("main_")
            or col.startswith("PassthroughCluster_")
            or col.startswith("redis_")
            or col.startswith("rabbitmq")
            or col.startswith("queue")
            or col.startswith("session")
            or col.startswith("istio-proxy")
        ):
            df = df.drop(columns=[col])

    return df


def convert_mem_mb(df: pd.DataFrame) -> pd.DataFrame:
    """Converts memory-related columns (ending with '_mem') from bytes to MBs.

    Args:
        df (pd.DataFrame): The input DataFrame.

    Returns:
        pd.DataFrame: The DataFrame with memory columns converted to MBs.
    """

    # Convert memory to MBs
    def update_mem(x):
        if not x.name.endswith("_mem"):
            return x
        x /= 1e6
        # x = x.astype(int)
        return x

    return df.apply(update_mem)


def preprocess_sock_shop(df: pd.DataFrame) -> pd.DataFrame:
    """Preprocesses the Sock Shop dataset by dropping constant, near-constant, and specific latency columns.

    Args:
        df (pd.DataFrame): The input Sock Shop DataFrame.

    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """
    df = convert_mem_mb(drop_near_constant(drop_constant(drop_time(df))))

    # drop columns that endswith lat_50 and lat_99 column if exists
    for col in df.columns:
        if col.endswith("lat_50") or col.endswith("lat_99"):
            df = df.drop(columns=[col])

    return df


def select_useful_cols(data: pd.DataFrame) -> list[str]:
    """Selects useful columns from the DataFrame based on specific criteria.

    Columns are considered useful if they are 'time', or if they represent CPU,
    memory, or latency metrics with sufficient variance.

    Args:
        data (pd.DataFrame): The input DataFrame.

    Returns:
        list[str]: A list of names of the useful columns.
    """
    selected_cols = []
    for c in data.columns:
        # keep time
        if "time" in c:
            selected_cols.append(c)

        # cpu
        if c.endswith("_cpu") and data[c].std() > 1:
            selected_cols.append(c)

        # mem
        if c.endswith("_mem") and data[c].std() > 1:
            selected_cols.append(c)

        # latency
        # if ("lat50" in c or "latency" in c) and (data[c] * 1000).std() > 10:
        if "lat50" in c and (data[c] * 1000).std() > 10:
            selected_cols.append(c)
    return selected_cols


def normalize_ts(data: pd.DataFrame) -> pd.DataFrame:
    """Normalizes time series data by subtracting the mean and dividing by the standard deviation.

    The 'time' column is excluded from normalization.

    Args:
        data (pd.DataFrame): The input DataFrame containing time series data.

    Returns:
        pd.DataFrame: The DataFrame with normalized time series data.
    """
    # minus mean and divide std for metrics, except time
    for c in data.columns:
        if c == "time":
            continue
        data[c] = (data[c] - data[c].mean()) / data[c].std()
    return data


def preprocess(
    data: pd.DataFrame, dataset: str | None = None, dk_select_useful: bool = False
) -> pd.DataFrame:
    """Preprocesses the input DataFrame based on the dataset type and selection criteria.

    Args:
        data (pd.DataFrame): The input DataFrame.
        dataset (str | None, optional): The name of the dataset (e.g., "causalrca-sock-shop"). Defaults to None.
        dk_select_useful (bool, optional): Whether to select only useful columns. Defaults to False.

    Returns:
        pd.DataFrame: The preprocessed DataFrame.
    """
    # data.drop(columns=["timestamp"], inplace=True)
    if dataset == "causalrca-sock-shop":
        data = drop_time(data)
    elif dataset is not None:
        data = drop_constant(drop_time(data))
        data = convert_mem_mb(data)

        if dk_select_useful is True:
            data = drop_extra(data)
            data = drop_near_constant(data)
            data = data[select_useful_cols(data)]

    len(data.columns)
    # print(f"Drop {before_cols_num - after_cols_num} cols. Left {after_cols_num} cols.")
    return data


def drop_kpi(dataset: pd.DataFrame) -> pd.DataFrame:
    dataset = dataset.drop(
        columns=[
            col for col in dataset.columns if any(word in col for word in KPI_COLUMN)
        ]
    )
    return dataset
