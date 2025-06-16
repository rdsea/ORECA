import subprocess

import yaml
from pydantic import BaseModel, model_validator


class DelayConfig(BaseModel):
    latency: str  # e.g., "100ms"
    correlation: str | None = None
    jitter: str | None = None


class LossConfig(BaseModel):
    loss: str  # e.g., "40"
    correlation: str | None = None


class BandwidthConfig(BaseModel):
    rate: str  # e.g., "1mbps"
    limit: int | None = None
    buffer: int | None = None
    peakrate: int | None = None
    minburst: int | None = None


class TargetSelector(BaseModel):
    namespace: str
    label_selectors: dict[str, str]


class NetworkChaosConfig(BaseModel):
    name: str
    namespace: str = "default"
    target: TargetSelector
    duration: str

    delay: DelayConfig | None = None
    loss: LossConfig | None = None
    bandwidth: BandwidthConfig | None = None

    @model_validator(mode="before")
    def validate_at_least_one_fault(cls, values):
        if not any(values.get(key) for key in ["delay", "loss", "bandwidth"]):
            raise ValueError(
                "At least one of 'delay', 'loss', or 'bandwidth' must be provided."
            )
        return values


def chaos_config_to_yaml(config: NetworkChaosConfig) -> str:
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

    # Bandwidth is a separate action type
    if config.bandwidth:
        metadata["spec"]["action"] = "bandwidth"
        metadata["spec"]["bandwidth"] = config.bandwidth.dict(exclude_none=True)
    else:
        # If delay or loss are set, use netem
        netem = {}
        if config.delay:
            netem["delay"] = config.delay.dict(exclude_none=True)
        if config.loss:
            netem["loss"] = config.loss.dict(exclude_none=True)

        if not netem:
            raise ValueError(
                "If 'bandwidth' is not defined, at least 'delay' or 'loss' must be."
            )

        metadata["spec"]["action"] = "netem"
        metadata["spec"]["netem"] = netem

    return yaml.dump(metadata, sort_keys=False)


class ChaosNetworkInjector:
    def __init__(self, config: NetworkChaosConfig):
        """
        :param config: A validated Pydantic config for the network chaos
        """
        if not isinstance(config, NetworkChaosConfig):
            raise TypeError("config must be an instance of NetworkChaosConfig")
        self.config = config

    def generate_yaml(self) -> str:
        return chaos_config_to_yaml(self.config)

    def apply(self):
        yaml_content = self.generate_yaml()
        command = f"kubectl apply -f - <<EOF\n{yaml_content}EOF"
        try:
            print(f"Applying Chaos Mesh experiment: {self.config.name}")
            subprocess.run(command, shell=True, check=True, executable="/bin/bash")
            print("✅ Chaos experiment applied successfully.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"❌ Failed to apply chaos experiment:\n{e}")

    def delete(self):
        """
        Clean up the experiment from the cluster.
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
