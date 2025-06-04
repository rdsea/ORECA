import yaml


class Config:
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        with open(self.config_path) as file:
            return yaml.safe_load(file)

    def get(self, key, default=None):
        return self.config.get(key, default)
