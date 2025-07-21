import json

import pandas as pd
from confluent_kafka import Consumer

MULTIPLY = 3
METRICS = [
    # "node:usage_per_cpu_core",
    # "node:memory_usage_percentage",
    # "node:disk_read",
    # "node:disk_written",
    # "node:disk_io_time",
    # "node:network_receive",
    # "node:network_transmit",
    # "pod:cpu_usage",
    # "pod:memory_usage",
    # "service:cpu_usage",
    # "service:memory_usage",
    # "service:network_receive",
    # "service:network_transmit",
    # "service:io",
    "service:p95_latency",
    "service:p75_latency",
    "service:p50_latency",
    # "service:request_rate_per_second",
    # "service:error_rate",
]

conf = {
    "bootstrap.servers": "redpanda-0.redpanda.redpanda.svc.cluster.local:9093, redpanda-1.redpanda.redpanda.svc.cluster.local:9093, redpanda-2.redpanda.redpanda.svc.cluster.local:9093",
    "security.protocol": "SASL_SSL",
    "sasl.mechanisms": "PLAIN",
    "sasl.username": "alice",
    "sasl.password": "redpanda",
    "ssl.ca.location": "/etc/tls/certs/ca.crt",
    "group.id": "my-consumer-group",
    "auto.offset.reset": "latest",
    "enable.auto.commit": True,
    "enable.ssl.certificate.verification": False,
}

consumer = Consumer(conf)
consumer.subscribe(["prometheus-metric"])

# Initialize dict of empty DataFrames keyed by metric name
dfs = {metric: pd.DataFrame() for metric in METRICS}

# ...

try:
    print("Consuming messages... Press Ctrl+C to stop.")
    while True:
        msg = consumer.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print(f"Consumer error: {msg.error()}")
            continue

        data = json.loads(msg.value().decode("utf-8"))
        metric_name = data.get("name")
        if metric_name not in METRICS:
            continue

        labels = data.get("labels", {})
        flat_data = {
            **labels,
            "name": metric_name,
            "timestamp": pd.to_datetime(data["timestamp"]),
            "value": float(data["value"]),
        }

        service_name = flat_data["service_name"]

        df = dfs[metric_name]

        # Filter df to get previous values only for this service_name

        if not df.empty:
            df_service = df[df["service_name"] == service_name]
            mean = df_service["value"].mean()
            std = df_service["value"].std()

            lower_bound = mean - MULTIPLY * std
            upper_bound = mean + MULTIPLY * std

            is_anomaly = (flat_data["value"] < lower_bound) or (
                flat_data["value"] > upper_bound
            )
        else:
            is_anomaly = False

        # Append new record to the main metric df
        dfs[metric_name] = pd.concat([df, pd.DataFrame([flat_data])], ignore_index=True)

        # Optional: keep sorted by timestamp
        dfs[metric_name] = dfs[metric_name].sort_values("timestamp")

        print(
            f"[{metric_name}] Service: {service_name} | New value: {flat_data['value']:.3f} - {'ANOMALY 🚨' if is_anomaly else 'Normal ✅'}"
        )

        # time.sleep(0.1)

except KeyboardInterrupt:
    print("Stopping consumer...")

finally:
    consumer.close()
