FROM debian:bullseye-slim

WORKDIR /anomaly_detections

COPY --from=ghcr.io/astral-sh/uv:0.7.21 /uv /uvx /bin/

COPY ./src /anomaly_detections/src

COPY ./pyproject.toml /anomaly_detections/pyproject.toml

COPY ./README.md /anomaly_detections/README.md

RUN uv sync --compile-bytecode --no-cache

ENV PATH="/anomaly_detections/.venv/bin:$PATH"

# CMD [ "python3 /anomaly_detections/src/anomaly_detections/spot/spot_anomaly_detections_test.py" ]
#
CMD ["tail", "-f", "/dev/null"]

