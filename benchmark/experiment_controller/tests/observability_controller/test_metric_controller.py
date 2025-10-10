import pytest
from experiment_controller.observability_controller.metric_controller import (
    MetricController,
    MetricControllerConfig,
)
from kubernetes import client, config


@pytest.fixture
def prometheus_release_name():
    """Helm release and namespace info."""
    return {"release": "prometheus", "namespace": "observe"}


def test_upgrade_and_verify_prometheus_config(prometheus_release_name):
    """
    Integration test:
    1. Applies Prometheus Helm upgrade using MetricController.
    2. Verifies the Prometheus CR in Kubernetes reflects updated scrape/evaluation intervals.
    """
    cfg = MetricControllerConfig(
        environment=["edge"],
        scrape_interval="5s",
        evaluation_interval="5s",
        custom_values={
            "prometheus.prometheusSpec.retention": "1d",
        },
    )
    controller = MetricController(cfg)

    controller.apply()

    for environment in cfg.environment:
        config.load_kube_config(context=environment)
        api = client.CustomObjectsApi()
        prom_cr = api.get_namespaced_custom_object(
            group="monitoring.coreos.com",
            version="v1",
            namespace=prometheus_release_name["namespace"],
            plural="prometheuses",
            name=f"prometheus-kube-prometheus-{prometheus_release_name['release']}",
        )

        spec = prom_cr.get("spec", {})

        assert spec.get("scrapeInterval") == "5s", "scrapeInterval not updated"
        assert spec.get("evaluationInterval") == "5s", "evaluationInterval not updated"

        retention = spec.get("retention", None)
        assert retention == "1d", f"Expected retention '1d', got {retention}"

        print("✅ Prometheus configuration successfully verified in cluster!")
