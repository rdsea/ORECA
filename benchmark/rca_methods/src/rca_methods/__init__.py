def hello() -> str:
    """Returns a greeting string."""
    return "Hello from rca-methods!"


def rca(func):
    """Decorator to wrap RCA algorithms, providing fault tolerance.

    If the wrapped RCA algorithm fails, this decorator catches the exception
    and returns a dummy result to prevent the entire process from crashing.

    Args:
        func (Callable): The RCA algorithm function to be wrapped.

    Returns:
        Callable: The wrapped function with fault tolerance.
    """

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
