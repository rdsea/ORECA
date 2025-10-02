from kubernetes import client

from experiment_controller.config.resource_fault_config import ResourcesChaosConfig
from experiment_controller.logger import logger


def resource_stress_config_to_yaml(config: ResourcesChaosConfig) -> dict:
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

        return {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "IOChaos",
            "metadata": {"name": config.name, "namespace": config.namespace},
            "spec": spec,
        }
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
            spec["stressors"]["cpu"] = config.stress_cpu.model_dump(exclude_none=True)

        if config.stress_memory is not None:
            spec["stressors"] = spec.get("stressors", {})
            spec["stressors"]["memory"] = config.stress_memory.model_dump(
                exclude_none=True
            )

        return {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "StressChaos",
            "metadata": {"name": config.name, "namespace": config.namespace},
            "spec": spec,
        }


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
        config.load_kube_config()
        self.api = client.CustomObjectsApi()

    def generate_yaml(self) -> dict:
        """Generate the YAML for the Chaos Mesh experiment.

        Returns:
            str: The YAML for the experiment.
        """
        return resource_stress_config_to_yaml(self.config)

    def apply(self):
        """Apply the Chaos Mesh experiment."""
        body = self.generate_yaml()
        try:
            print(f"🔥 Applying resource chaos experiment: {self.config.name}")
            logger.info(body)
            self.api.create_namespaced_custom_object(
                group="chaos-mesh.org",
                version="v1alpha1",
                namespace=self.config.namespace,
                plural="stresschaos",
                body=body,
            )
            print("✅ Chaos applied successfully.")
        except client.ApiException as e:
            raise RuntimeError(f"❌ Failed to apply chaos:\n{e}")

    def delete(self):
        """Delete the Chaos Mesh experiment."""
        if self.config.io_chaos is not None:
            resource_type = "iochaos"
        else:
            resource_type = "stresschaos"
        try:
            self.api.delete_namespaced_custom_object(
                group="chaos-mesh.org",
                version="v1alpha1",
                namespace=self.config.namespace,
                plural=resource_type,
                name=self.config.name,
            )
            print(f"🧹 {resource_type} experiment deleted successfully.")
        except client.ApiException as e:
            raise RuntimeError(f"❌ Failed to delete {resource_type}:\n{e}")
