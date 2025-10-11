import subprocess

from pydantic import BaseModel

from experiment_controller.logger import logger


class MetricControllerConfig(BaseModel):
    environment: list[str]
    scrape_interval: str = "30s"
    evaluation_interval: str = "30s"
    custom_values: dict[str, str] = {}


class MetricController:
    def __init__(self, config: MetricControllerConfig):
        self.config = config

    def apply(self):
        """
        Upgrade Prometheus global config in clusters that match the given environment.
        Includes configurable Helm chart values via 'custom_values'.
        """
        for environment in self.config.environment:
            logger.info(
                f"Starting Prometheus config upgrade for environment: {environment}"
            )

            helm_cmd = [
                "helm",
                "upgrade",
                "prometheus",
                "prometheus-community/kube-prometheus-stack",
                "--kube-context",
                environment,
                "-n",
                "observe",
                "--wait",
                "--set",
                f"prometheus.prometheusSpec.scrapeInterval={self.config.scrape_interval}",
                "--set",
                f"prometheus.prometheusSpec.evaluationInterval={self.config.evaluation_interval}",
            ]

            # Apply any additional Helm values from config
            for key, value in self.config.custom_values.items():
                helm_cmd += ["--set", f"{key}={value}"]

            logger.debug("Executing Helm command: %s", " ".join(helm_cmd))

            try:
                subprocess.run(helm_cmd, check=True)
                logger.info(
                    f"✅ Metric config successfully upgraded for environment '{environment}'."
                )
            except subprocess.CalledProcessError as e:
                logger.error(
                    f"❌ Helm upgrade failed for environment '{environment}': {e}"
                )
                raise
            except Exception as e:
                logger.exception(f"Unexpected error during Metric upgrade: {e}")
                raise
