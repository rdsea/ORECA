FROM debian:bullseye-slim

WORKDIR /rca_methods

COPY --from=ghcr.io/astral-sh/uv:0.7.21 /uv /uvx /bin/

COPY ./src /rca_methods/src

COPY ./pyproject.toml /rca_methods/pyproject.toml

COPY ./README.md /rca_methods/README.md

RUN uv sync --compile-bytecode --no-cache

ENV PATH="/rca_methods/.venv/bin:$PATH"

# CMD [ "python3 /rca_methods/src/anomaly_detections/spot/spot_anomaly_detections_test.py" ]
#
CMD ["tail", "-f", "/dev/null"]

