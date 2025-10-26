import os
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import requests
from requests.exceptions import RequestException

from experiment_controller.logger import logger


class TraceCollector:
    """A wrapper for the Tempo API client."""

    def __init__(self, url: str):
        """Initialize the Tempo API client.

        Args:
            url (str): The URL of the Tempo server (without protocol, e.g. tempo:3200).
        """
        self.api_url = url
        self.search_url = f"{self.api_url}/api/search"
        self.trace_url = f"{self.api_url}/api/traces"

    def query_range(
        self,
        start_time: int | datetime | str,
        end_time: int | datetime | str,
        service_name: str | None = None,
        limit: int = 100,
        save_path: str | Path = ".",
        experiment_name: str | None = None,
        save_to_file: bool = True,
        time_unit: str = "s",  # "s" for seconds, "ms" for milliseconds, "ns" for nanoseconds
    ) -> pd.DataFrame:
        """Query a range of traces from Tempo and export all spans to CSV."""
        if experiment_name:
            save_path = os.path.join(save_path, f"{experiment_name}_traces.csv")
        else:
            save_path = os.path.join(save_path, "traces.csv")

        start_time = self._time_format_transform(start_time)
        end_time = self._time_format_transform(end_time)

        multiplier = {"s": 1, "ms": 1e3, "ns": 1e9}[time_unit]

        params: dict[str, Any] = {
            "start": int(start_time.timestamp() * multiplier),
            "end": int(end_time.timestamp() * multiplier),
            "limit": limit,
        }
        if service_name:
            params["serviceName"] = service_name

        logger.info(f"Querying Tempo /api/search with params: {params}")

        try:
            response = requests.get(self.search_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            traces = data.get("traces", [])

            if not traces:
                logger.warning("No traces found in the given range.")
                return pd.DataFrame()

            trace_ids = [t["traceID"] for t in traces]
            logger.info(
                f"Found {len(trace_ids)} traces, fetching spans via /api/traces/..."
            )

            all_spans = []
            for trace_id in trace_ids:
                trace_spans = self._fetch_trace_details(trace_id)
                if trace_spans:
                    all_spans.extend(trace_spans)

            if not all_spans:
                logger.warning("No spans found in the retrieved traces.")
                return pd.DataFrame()

            df = pd.DataFrame(all_spans)

            if save_to_file:
                if os.path.exists(save_path):
                    df.to_csv(save_path, mode="a", index=False, header=False)
                else:
                    df.to_csv(save_path, index=False)
                logger.info(f"✅ Traces saved to {save_path}")

            logger.info(f"Retrieved {len(df)} spans from {len(trace_ids)} traces.")
            return df

        except RequestException as e:
            logger.error(f"Error querying Tempo API: {e}")
            return pd.DataFrame()

    def _fetch_trace_details(self, trace_id: str) -> list[dict[str, Any]]:
        """Fetch spans from Tempo's /api/traces/{trace_id} endpoint (OTLP JSON format)."""
        try:
            url = f"{self.trace_url}/{trace_id}"
            r = requests.get(url, timeout=30)
            r.raise_for_status()
            data = r.json()

            spans = []

            for batch in data.get("batches", []):
                # Extract service name from resource attributes
                resource_attrs = batch.get("resource", {}).get("attributes", [])
                service_name = ""
                for attr in resource_attrs:
                    if attr.get("key") == "service.name":
                        service_name = attr["value"].get("stringValue", "")
                        break

                for scope_span in batch.get("scopeSpans", []):
                    for span in scope_span.get("spans", []):
                        spans.append(
                            {
                                "trace_id": span.get("traceId", ""),
                                "span_id": span.get("spanId", ""),
                                "parent_span_id": span.get("parentSpanId", ""),
                                "operation_name": span.get("name", ""),
                                "service_name": service_name,
                                "span_kind": span.get("kind", ""),
                                "start_time_unix_nano": span.get(
                                    "startTimeUnixNano", ""
                                ),
                                "end_time_unix_nano": span.get("endTimeUnixNano", ""),
                                "duration_ns": str(
                                    int(span.get("endTimeUnixNano", "0"))
                                    - int(span.get("startTimeUnixNano", "0"))
                                )
                                if span.get("endTimeUnixNano")
                                and span.get("startTimeUnixNano")
                                else "",
                                "attributes": span.get("attributes", []),
                            }
                        )

            if not spans:
                logger.warning(
                    f"No spans found in trace {trace_id}. Keys: {list(data.keys())}"
                )

            return spans

        except RequestException as e:
            logger.error(f"Error fetching trace {trace_id}: {e}")
            return []

    def _calc_duration(self, span: dict[str, Any]) -> int | None:
        """Calculate span duration in nanoseconds."""
        try:
            start = int(span.get("startTimeUnixNano", 0))
            end = int(span.get("endTimeUnixNano", 0))
            return end - start if end > start else None
        except Exception:
            return None

    def _extract_service_name(self, attrs: list[dict[str, Any]]) -> str:
        """Extract service.name from attributes."""
        for attr in attrs:
            if attr.get("key") == "service.name":
                return attr.get("value", {}).get("stringValue", "")
        return ""

    def _time_format_transform(self, time_to_transform) -> datetime:
        """Transform time data from int or string to datetime object."""
        if isinstance(time_to_transform, int):
            if time_to_transform > 1e10:  # nanoseconds
                time_to_transform /= 1e9
            return datetime.fromtimestamp(time_to_transform)
        elif isinstance(time_to_transform, str):
            return datetime.fromtimestamp(int(time_to_transform))
        elif isinstance(time_to_transform, datetime):
            return time_to_transform
        raise ValueError(f"Unsupported time format: {time_to_transform}")
