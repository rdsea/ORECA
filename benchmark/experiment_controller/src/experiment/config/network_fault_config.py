from experiment.config.fault_config import FaultSpecificConfig, TargetSelector
from pydantic import BaseModel, model_validator


class DelayConfig(BaseModel):
    """
    Configuration for simulating network latency using Chaos Mesh.

    Attributes:
        latency (str):
            Required. The base network delay to inject (e.g., "100ms", "1s").
        correlation (str | None):
            Optional. Correlation between delays across packets ("0" = no correlation, "1" = full).
            Useful for simulating bursty or patterned network conditions.
        jitter (str | None):
            Optional. Amount of variability to introduce to the delay (e.g., "20ms").
            Adds randomness to better emulate real-world behavior.
    """

    latency: str
    correlation: str | None = None
    jitter: str | None = None


class LossConfig(BaseModel):
    """
    Configuration for simulating packet loss.

    Attributes:
        loss (str):
            Required. Percentage of packets to drop (e.g., "40").
        correlation (str | None):
            Optional. Correlation of packet loss ("0" = random, "1" = fully correlated).
    """

    loss: str
    correlation: str | None = None


class BandwidthConfig(BaseModel):
    """
    Configuration for bandwidth shaping.

    Attributes:
        rate (str):
            Required. Bandwidth rate (e.g., "1mbps").
        limit (int | None):
            Optional. Maximum number of bytes that can be queued.
        buffer (int | None):
            Optional. Maximum tokens in the token bucket.
        peakrate (int | None):
            Optional. Peak bandwidth rate in kbps.
        minburst (int | None):
            Optional. Minimum burst size in bytes.
    """

    rate: str
    limit: int | None = None
    buffer: int | None = None
    peakrate: int | None = None
    minburst: int | None = None


class NetworkChaosConfig(FaultSpecificConfig):
    """
    Full configuration for a Chaos Mesh NetworkChaos experiment.

    Supports applying delay, loss, or bandwidth shaping to network traffic.
    At least one of the three (delay, loss, bandwidth) must be provided.

    Attributes:
        namespace (str):
            Namespace where the experiment runs.
        target (TargetSelector):
            Selector to identify affected pods.
        delay (DelayConfig | None):
            Optional delay injection.
        loss (LossConfig | None):
            Optional packet loss injection.
        bandwidth (BandwidthConfig | None):
            Optional bandwidth control.
    """

    name: str
    namespace: str = "default"
    target: TargetSelector
    delay: DelayConfig | None = None
    duration: str
    loss: LossConfig | None = None
    bandwidth: BandwidthConfig | None = None

    @model_validator(mode="before")
    def validate_at_least_one_fault(cls, values):
        if not any(values.get(key) for key in ["delay", "loss", "bandwidth"]):
            raise ValueError(
                "You must provide at least one of: 'delay', 'loss', or 'bandwidth'."
            )
        return values
