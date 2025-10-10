from kubernetes import client
from kubernetes import config as kube_config

from experiment_controller.config.network_fault_config import NetworkChaosConfig
from experiment_controller.logger import logger


def chaos_config_to_yaml(config: NetworkChaosConfig) -> dict:
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
        metadata["spec"]["bandwidth"] = config.bandwidth.model_dump(exclude_none=True)
    else:
        if config.delay is not None:
            metadata["spec"]["delay"] = config.delay.model_dump(exclude_none=True)
        elif config.loss is not None:
            metadata["spec"]["loss"] = config.loss.model_dump(exclude_none=True)
        else:
            raise ValueError(
                "If 'bandwidth' is not specified, at least 'delay' or 'loss' must be."
            )

        metadata["spec"]["action"] = "netem"

    return metadata


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

    def generate_yaml(self) -> dict:
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
        body = self.generate_yaml()
        try:
            logger.info(f"🚀 Applying Chaos Mesh experiment: {self.config.name}")
            logger.debug(body)
            for environment in self.config.target.environment:
                try:
                    kube_config.load_kube_config(context=environment)
                except kube_config.ConfigException:
                    logger.exception(f"Failed to load kubeconfig for {environment}")
                    raise
                self.api = client.CustomObjectsApi()
                logger.debug(f"Applying chaos experiment to {environment}")
                self.api.create_namespaced_custom_object(
                    group="chaos-mesh.org",
                    version="v1alpha1",
                    namespace=self.config.namespace,
                    plural="networkchaos",
                    body=body,
                )
                logger.info(
                    f"✅ Chaos experiment applied successfully for environment {environment}"
                )
        except client.ApiException as e:
            raise RuntimeError(f"❌ Failed to apply chaos experiment:\n{e}")

    def delete(self):
        """
        Delete the chaos experiment from the Kubernetes cluster.

        Raises:
            RuntimeError: If kubectl fails to delete the experiment.
        """
        try:
            for environment in self.config.target.environment:
                try:
                    kube_config.load_kube_config(context=environment)
                except kube_config.ConfigException:
                    logger.exception(f"Failed to load kubeconfig for {environment}")
                    raise
                self.api = client.CustomObjectsApi()
                logger.debug(f"Applying chaos experiment to {environment}")
                self.api.delete_namespaced_custom_object(
                    group="chaos-mesh.org",
                    version="v1alpha1",
                    namespace=self.config.namespace,
                    plural="networkchaos",
                    name=self.config.name,
                )
                logger.info(
                    f"🧹 Chaos experiment deleted successfully for environment {environment}"
                )
        except client.ApiException as e:
            logger.exception("Chaos Network clean failed")
            raise RuntimeError(f"❌ Failed to delete chaos experiment:\n{e}")
