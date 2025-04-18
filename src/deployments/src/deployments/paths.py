import os
from pathlib import Path

HOME_DIR = Path(os.path.expanduser("~"))
BASE_DIR = Path(__file__).resolve().parent
BASE_PARENT_DIR = Path(__file__).resolve().parent.parent.parent.parent

# Targe microservice and its utilities directories
TARGET_MICROSERVICES = BASE_PARENT_DIR / "applications"

# Data directories
DATA_DIR = BASE_DIR / "data_dir"
RESULTS_DIR = DATA_DIR / "results"
PLOTS_DIR = DATA_DIR / "plots"

# Cache directories
CACHE_DIR = HOME_DIR / "cache_dir"

print(TARGET_MICROSERVICES)
# Fault scripts
# FAULT_SCRIPTS = BASE_DIR / "generators" / "fault" / "script"

# Metadata files
# SOCIAL_NETWORK_METADATA = BASE_DIR / "service" / "metadata" / "social-network.json"
# HOTEL_RES_METADATA = BASE_DIR / "service" / "metadata" / "hotel-reservation.json"
PROMETHEUS_METADATA = BASE_DIR / "service" / "metadata" / "prometheus.json"
# TRAIN_TICKET_METADATA = BASE_DIR / "service" / "metadata" / "train-ticket.json"
# ASTRONOMY_SHOP_METADATA = BASE_DIR / "service" / "metadata" / "astronomy-shop.json"
# TIDB_METADATA = BASE_DIR / "service" / "metadata" / "tidb-with-operator.json"
# FLIGHT_TICKET_METADATA = BASE_DIR / "service" / "metadata" / "flight-ticket.json"
