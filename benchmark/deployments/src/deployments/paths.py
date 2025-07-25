import os
from pathlib import Path

# Define base directories
HOME_DIR = Path(os.path.expanduser("~"))
BASE_DIR = Path(__file__).resolve().parent
BASE_PARENT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Target microservice and its utilities directories
TARGET_MICROSERVICES = BASE_PARENT_DIR / "applications"

# Helm charts directory
HELM_CHARTS = BASE_PARENT_DIR / "helm_charts"

# Data directories for results and plots
DATA_DIR = BASE_DIR / "data_dir"
RESULTS_DIR = DATA_DIR / "results"
PLOTS_DIR = DATA_DIR / "plots"

# Cache directory
CACHE_DIR = HOME_DIR / "cache_dir"

# Metadata files for various services
PROMETHEUS_METADATA = BASE_DIR / "service" / "metadata" / "prometheus.json"
LOKI_METADATA = BASE_DIR / "service" / "metadata" / "loki.json"
ALLOY_METADATA = BASE_DIR / "service" / "metadata" / "alloy.json"
JAEGER_METADATA = BASE_DIR / "service" / "metadata" / "jaeger.json"
GRAFANA_METADATA = BASE_DIR / "service" / "metadata" / "grafana.json"
CHAOS_MESH_METADATA = BASE_DIR / "service" / "metadata" / "chaos-mesh.json"
