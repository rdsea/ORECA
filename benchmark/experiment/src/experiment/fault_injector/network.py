import subprocess

import yaml
from pydantic import BaseModel, model_validator

from experiment.config.fault_config import FaultSpecificConfig


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


class TargetSelector(BaseModel):
    """
    Selector for target pods to apply chaos.

    Attributes:
        namespace (str):
            Kubernetes namespace of the target pods.
        label_selectors (dict[str, str]):
            Label selectors to match target pods.
    """

    namespace: str
    label_selectors: dict[str, str]


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

    namespace: str = "default"
    target: TargetSelector
    delay: DelayConfig | None = None
    loss: LossConfig | None = None
    bandwidth: BandwidthConfig | None = None

    @model_validator(mode="before")
    def validate_at_least_one_fault(cls, values):
        if not any(values.get(key) for key in ["delay", "loss", "bandwidth"]):
            raise ValueError(
                "You must provide at least one of: 'delay', 'loss', or 'bandwidth'."
            )
        return values


def chaos_config_to_yaml(config: NetworkChaosConfig) -> str:
    """
    Convert a validated NetworkChaosConfig object into a Chaos Mesh YAML string.

    Args:
        config (NetworkChaosConfig): Validated config object.

    Returns:
        str: YAML string representation for Chaos Mesh.
    """
    metadata = {
        "apiVersion": "chaos-mesh.org/v1alpha1",
        "kind": "NetworkChaos",
        "metadata": {"name": config.name, "namespace": config.namespace},
        "spec": {
            "mode": "all",
            "selector": {
                "namespaces": [config.target.namespace],
                "labelSelectors": config.target.label_selectors,
            },
            "duration": config.duration,
        },
    }

    if config.bandwidth:
        metadata["spec"]["action"] = "bandwidth"
        metadata["spec"]["bandwidth"] = config.bandwidth.dict(exclude_none=True)
    else:
        netem = {}
        if config.delay:
            netem["delay"] = config.delay.dict(exclude_none=True)
        if config.loss:
            netem["loss"] = config.loss.dict(exclude_none=True)

        if not netem:
            raise ValueError(
                "If 'bandwidth' is not specified, at least 'delay' or 'loss' must be."
            )

        metadata["spec"]["action"] = "netem"
        metadata["spec"]["netem"] = netem

    return yaml.dump(metadata, sort_keys=False)


class ChaosNetworkInjector:
    """
    Utility for applying and removing Chaos Mesh network experiments via kubectl.

    Methods:
        generate_yaml():
            Returns the experiment YAML as a string.
        apply():
            Applies the chaos experiment to the cluster.
        delete():
            Removes the experiment from the cluster.
    """

    def __init__(self, config: NetworkChaosConfig):
        """
        Initialize the injector with a validated network chaos configuration.

        Args:
            config (NetworkChaosConfig): Validated network chaos configuration.

        Raises:
            TypeError: If the provided config is not a NetworkChaosConfig.
        """
        if not isinstance(config, NetworkChaosConfig):
            raise TypeError("config must be an instance of NetworkChaosConfig")
        self.config = config

    def generate_yaml(self) -> str:
        """
        Generate the YAML string for the configured chaos experiment.

        Returns:
            str: Chaos Mesh experiment YAML.
        """
        return chaos_config_to_yaml(self.config)

    def apply(self):
        """
        Apply the chaos experiment to the Kubernetes cluster using kubectl.

        Raises:
            RuntimeError: If kubectl fails to apply the experiment.
        """
        yaml_content = self.generate_yaml()
        command = f"kubectl apply -f - <<EOF\n{yaml_content}EOF"
        try:
            print(f"🚀 Applying Chaos Mesh experiment: {self.config.name}")
            subprocess.run(command, shell=True, check=True, executable="/bin/bash")
            print("✅ Chaos experiment applied successfully.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"❌ Failed to apply chaos experiment:\n{e}")

    def delete(self):
        """
        Delete the chaos experiment from the Kubernetes cluster.

        Raises:
            RuntimeError: If kubectl fails to delete the experiment.
        """
        try:
            subprocess.run(
                [
                    "kubectl",
                    "delete",
                    "networkchaos",
                    self.config.name,
                    "-n",
                    self.config.namespace,
                ],
                check=True,
            )
            print("🧹 Chaos experiment deleted successfully.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"❌ Failed to delete chaos experiment:\n{e}")
