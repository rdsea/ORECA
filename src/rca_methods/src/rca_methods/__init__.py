def hello() -> str:
    return "Hello from rca-methods!"


def rca(func):
    """RCA Wrapper to tolerate the case when the RCA algorithm fails."""

    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            from rca_methods.io.time_series import preprocess

            data = preprocess(
                data=args[0], dataset=kwargs.get("dataset"), dk_select_useful=False
            )
            dummy = data.columns.to_list()
            return {"adj": [], "node_names": dummy, "ranks": dummy}

    return wrapper
