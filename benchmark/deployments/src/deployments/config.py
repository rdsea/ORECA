import yaml


class Config:
    """A class to manage configuration loading from a YAML file."""

    def __init__(self, config_path):
        """Initialize the Config object.

        Args:
            config_path (str): The path to the YAML configuration file.
        """
        self.config_path = config_path
        self.config = self._load_config()

    def _load_config(self):
        """Load the configuration from the YAML file.

        Returns:
            dict: The loaded configuration.
        """
        with open(self.config_path) as file:
            return yaml.safe_load(file)

    def get(self, key, default=None):
        """Get a configuration value by key.

        Args:
            key (str): The key of the configuration value.
            default (any, optional): The default value to return if the key is not found. Defaults to None.

        Returns:
            any: The configuration value or the default value.
        """
        return self.config.get(key, default)
