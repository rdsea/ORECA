import subprocess

from pydantic import BaseModel

from experiment_controller.logger import logger


class PrometheusConfig(BaseModel):
    scrape_interval: str | None = None
    evaluation_interval: str | None = None
    custom_values: dict[str, str] = {}


class MetricControllerConfig(BaseModel):
    environment: dict[str, PrometheusConfig]


class MetricController:
    def __init__(self, config: MetricControllerConfig):
        self.config = config

    def apply(self):
        """
        Upgrade Prometheus global config in clusters that match the given environment.
        Includes configurable Helm chart values via 'custom_values'.
        """
        for environment_name, prometheus_config in self.config.environment.items():
            has_scrape = prometheus_config.scrape_interval is not None
            has_eval = prometheus_config.evaluation_interval is not None
            has_custom = bool(prometheus_config.custom_values)

            if not (has_scrape or has_eval or has_custom):
                logger.warning(
                    f"⚠️ No Prometheus configuration changes found for environment '{environment_name}'. Skipping."
                )
                continue
            logger.info(
                f"Starting Prometheus config upgrade for environment: {environment_name}"
            )

            helm_cmd = [
                "helm",
                "upgrade",
                "prometheus",
                "prometheus-community/kube-prometheus-stack",
                "--kube-context",
                environment_name,
                "-n",
                "observe",
                "--wait",
                "--reuse-values",
            ]

            if prometheus_config.scrape_interval is not None:
                helm_cmd += [
                    "--set",
                    f"prometheus.prometheusSpec.scrapeInterval={prometheus_config.scrape_interval}",
                ]

            if prometheus_config.evaluation_interval is not None:
                helm_cmd += [
                    "--set",
                    f"prometheus.prometheusSpec.evaluationInterval={prometheus_config.evaluation_interval}",
                ]

            # Apply additional custom Helm values
            for key, value in (prometheus_config.custom_values or {}).items():
                if value is not None:
                    helm_cmd += ["--set", f"{key}={value}"]

            logger.debug("Executing Helm command: %s", " ".join(helm_cmd))

            try:
                subprocess.run(helm_cmd, check=True)
                logger.info(
                    f"✅ Metric config successfully upgraded for environment '{environment_name}'."
                )
            except subprocess.CalledProcessError as e:
                logger.error(
                    f"❌ Helm upgrade failed for environment '{environment_name}': {e}"
                )
                raise
            except Exception as e:
                logger.exception(f"Unexpected error during Metric upgrade: {e}")
                raise
