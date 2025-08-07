import logging
import subprocess

import yaml

from experiment_controller.config.network_fault_config import NetworkChaosConfig


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

    if config.bandwidth is not None:
        metadata["spec"]["action"] = "bandwidth"
        metadata["spec"]["bandwidth"] = config.bandwidth.dict(exclude_none=True)
    else:
        if config.delay is not None:
            metadata["spec"]["delay"] = config.delay.dict(exclude_none=True)
        elif config.loss is not None:
            metadata["spec"]["loss"] = config.loss.dict(exclude_none=True)
        else:
            raise ValueError(
                "If 'bandwidth' is not specified, at least 'delay' or 'loss' must be."
            )

        metadata["spec"]["action"] = "netem"

    return yaml.dump(metadata, sort_keys=False)


class ChaosNetworkController:
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
        Initialize the controller with a validated network chaos configuration.

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
            logging.info(command)
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
