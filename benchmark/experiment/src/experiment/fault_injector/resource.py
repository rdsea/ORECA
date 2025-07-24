import logging
import subprocess

import yaml

from experiment.config.resource_fault_config import StressChaosConfig


def stress_config_to_yaml(config: StressChaosConfig) -> str:
    """
    Convert a StressChaosConfig object to a YAML string for Chaos Mesh.

    Args:
        config (StressChaosConfig): Validated config object.

    Returns:
        str: YAML string.
    """
    spec = {
        "selector": {
            "namespaces": [config.target.namespace],
            "labelSelectors": config.target.label_selectors,
        },
        "mode": "all",
        "duration": config.duration,
    }

    if config.stress_cpu:
        spec["stressors"] = spec.get("stressors", {})
        spec["stressors"]["cpu"] = config.stress_cpu.dict(exclude_none=True)

    if config.stress_memory:
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


class ChaosStressInjector:
    """
    Injector for CPU/Memory stress using Chaos Mesh.

    Methods:
        generate_yaml(): Returns the YAML as a string.
        apply(): Applies the stress experiment.
        delete(): Deletes the stress experiment.
    """

    def __init__(self, config: StressChaosConfig):
        if not isinstance(config, StressChaosConfig):
            raise TypeError("config must be an instance of StressChaosConfig")
        self.config = config

    def generate_yaml(self) -> str:
        return stress_config_to_yaml(self.config)

    def apply(self):
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
