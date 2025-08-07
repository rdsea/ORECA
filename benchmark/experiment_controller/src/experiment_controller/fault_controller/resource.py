import logging
import subprocess

import yaml

from experiment_controller.config.resource_fault_config import ResourcesChaosConfig


def resource_stress_config_to_yaml(config: ResourcesChaosConfig) -> str:
    """
    Convert a ResourcesChaosConfig object to a YAML string for Chaos Mesh.

    Args:
        config (ResourcesChaosConfig): Validated config object.

    Returns:
        str: YAML string.
    """
    if config.io_chaos is not None:
        io_chaos_config = config.io_chaos
        # Generate IOChaos YAML
        spec = {
            "action": io_chaos_config.action,
            "mode": "all",
            "selector": {
                "namespaces": [config.target.namespace],
                "labelSelectors": config.target.label_selectors,
            },
            "path": io_chaos_config.path,
            "percent": io_chaos_config.percent,
            "duration": config.duration,
        }

        if io_chaos_config.delay is not None:
            spec["delay"] = io_chaos_config.delay
        if io_chaos_config.errno is not None:
            spec["errno"] = io_chaos_config.errno
        if io_chaos_config.methods is not None:
            spec["methods"] = io_chaos_config.methods

        return yaml.dump(
            {
                "apiVersion": "chaos-mesh.org/v1alpha1",
                "kind": "IOChaos",
                "metadata": {"name": config.name, "namespace": config.namespace},
                "spec": spec,
            },
            sort_keys=False,
        )
    else:
        spec = {
            "selector": {
                "namespaces": [config.target.namespace],
                "labelSelectors": config.target.label_selectors,
            },
            "mode": "all",
            "duration": config.duration,
        }

        if config.stress_cpu is not None:
            spec["stressors"] = spec.get("stressors", {})
            spec["stressors"]["cpu"] = config.stress_cpu.dict(exclude_none=True)

        if config.stress_memory is not None:
            spec["stressors"] = spec.get("stressors", {})
            spec["stressors"]["memory"] = config.stress_memory.dict(exclude_none=True)

        return yaml.dump(
            {
                "apiVersion": "chaos-mesh.org/v1alpha1",
                "kind": "StressChaos",
                "metadata": {"name": config.name, "namespace": config.namespace},
                "spec": spec,
            },
            sort_keys=False,
        )


class ChaosResourceController:
    """controller for CPU/Memory stress using Chaos Mesh."""

    def __init__(self, config: ResourcesChaosConfig):
        """Initialize the injector.

        Args:
            config (ResourcesChaosConfig): The configuration for the resource chaos experiment.
        """
        if not isinstance(config, ResourcesChaosConfig):
            raise TypeError("config must be an instance of ResourcesChaosConfig")
        self.config = config

    def generate_yaml(self) -> str:
        """Generate the YAML for the Chaos Mesh experiment.

        Returns:
            str: The YAML for the experiment.
        """
        return resource_stress_config_to_yaml(self.config)

    def apply(self):
        """Apply the Chaos Mesh experiment."""
        yaml_content = self.generate_yaml()
        command = f"kubectl apply -f - <<EOF\n{yaml_content}EOF"
        try:
            print(f"🔥 Applying StressChaos experiment: {self.config.name}")
            logging.info(command)
            subprocess.run(command, shell=True, check=True, executable="/bin/bash")
            print("✅ StressChaos applied successfully.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"❌ Failed to apply StressChaos:\n{e}")

    def delete(self):
        """Delete the Chaos Mesh experiment."""
        try:
            subprocess.run(
                [
                    "kubectl",
                    "delete",
                    "stresschaos",
                    self.config.name,
                    "-n",
                    self.config.namespace,
                ],
                check=True,
            )
            print("🧹 StressChaos experiment deleted successfully.")
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"❌ Failed to delete StressChaos:\n{e}")
