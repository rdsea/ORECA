import subprocess

from loguru import logger

from deployments.applications.kubectl import KubeCtl


class Helm:
    """A wrapper for the Helm CLI."""

    @staticmethod
    def install(
        release_name: str,
        chart_path: str,
        namespace: str,
        version: str | None = None,
        values: str | None = None,
        locally: bool = False,
    ):
        """Install a Helm chart.

        Args:
            release_name (str): The name of the release.
            chart_path (str): The path to the Helm chart.
            namespace (str): The namespace to install the chart in.
            version (str, optional): The version of the chart. Defaults to None.
            values (str, optional): The path to the configuration file. Defaults to None.
            locally (bool, optional): Whether the chart is locally available or from a repo. Defaults to False.
        """
        print("== Helm Install ==")

        # Install dependencies for chart before installation
        if locally:
            dependency_command = f"helm dependency update {chart_path}"
            dependency_process = subprocess.Popen(
                dependency_command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            dependency_output, dependency_error = dependency_process.communicate()

        command = f"helm install {release_name} {chart_path} -n {namespace} --create-namespace {f'-f {values}' if values else ''}"

        if version:
            command += f" --version {version}"

        print(command)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()

        if error:
            print(error.decode("utf-8"))
        else:
            print(output.decode("utf-8"))

    @staticmethod
    def uninstall(release_name: str, namespace: str):
        """Uninstall a Helm chart.

        Args:
            release_name (str): The name of the release.
            namespace (str): The namespace to uninstall the chart from.
        """
        print("== Helm Uninstall ==")

        if not Helm.exists_release(release_name, namespace):
            print(f"Release {release_name} does not exist. Skipping uninstall.")
            return

        command = f"helm uninstall {release_name} -n {namespace}"
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, error = process.communicate()

        if error:
            logger.error(error.decode("utf-8"))
            raise Exception("Helm uninstall failed")
        else:
            logger.info(output.decode("utf-8"))

    @staticmethod
    def exists_release(release_name: str, namespace: str) -> bool:
        """Check if a Helm release exists.

        Args:
            release_name (str): The name of the release.
            namespace (str): The namespace to check in.

        Returns:
            bool: True if the release exists, False otherwise.
        """
        command = f"helm list -n {namespace}"
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()

        if error:
            print(error.decode("utf-8"))
            return False
        else:
            return release_name in output.decode("utf-8")

    @staticmethod
    def assert_if_deployed(namespace: str):
        """Assert if all services in the application are deployed.

        Args:
            namespace (str): The namespace to check.

        Raises:
            Exception: If the services are not deployed.
        """
        kubectl = KubeCtl()
        try:
            kubectl.wait_for_ready(namespace)
        except Exception as e:
            raise e

        return True

    @staticmethod
    def upgrade(**args):
        """Upgrade a Helm chart.

        Args:
            release_name (str): The name of the release.
            chart_path (str): The path to the Helm chart.
            namespace (str): The namespace to upgrade the chart in.
            values_file (str): The path to the values.yaml file.
            set_values (dict): Key-value pairs for --set options.
        """
        print("== Helm Upgrade ==")
        release_name = args.get("release_name")
        chart_path = args.get("chart_path")
        namespace = args.get("namespace")
        values_file = args.get("values_file")
        set_values = args.get("set_values", {})

        command = [
            "helm",
            "upgrade",
            release_name,
            chart_path,
            "-n",
            namespace,
            "-f",
            values_file,
        ]

        # Add --set options if provided
        for key, value in set_values.items():
            command.append("--set")
            command.append(f"{key}={value}")

        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, error = process.communicate()

        if error:
            print("Error during helm upgrade:")
            print(error.decode("utf-8"))
        else:
            print("Helm upgrade successful!")
            print(output.decode("utf-8"))

    @staticmethod
    def add_repo(name: str, url: str):
        """Add a Helm repository.

        Args:
            name (str): The name of the repository.
            url (str): The URL of the repository.
        """
        print(f"== Helm Repo Add: {name} ==")
        command = f"helm repo add {name} {url}"
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output, error = process.communicate()

        if error:
            print(f"Error adding helm repo {name}: {error.decode('utf-8')}")
        else:
            print(f"Helm repo {name} added successfully: {output.decode('utf-8')}")

    @staticmethod
    def update_repo():
        """Update the Helm repositories."""
        print("== Helm Repo Update ==")
        command = "helm repo update"
        process = subprocess.Popen(
            command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, error = process.communicate()

        if error:
            print("Error updating helm repo")
        else:
            print("Helm repo updated")


# Example usage
if __name__ == "__main__":
    sn_configs = {
        "release_name": "test-social-network",
        "chart_path": "/home/oppertune/DeathStarBench/socialNetwork/helm-chart/socialnetwork",
        "namespace": "social-network",
    }
    Helm.install(**sn_configs)
    Helm.uninstall(**sn_configs)
