import subprocess

from experiment_controller.logger import logger


class ScriptRunner:
    """Executes local shell scripts."""

    def run(self, script_path: str):
        """Runs a shell script and logs its output.

        Args:
            script_path (str): The path to the script to execute.

        Raises:
            RuntimeError: If the script fails to execute.
        """
        try:
            result = subprocess.run(
                ["bash", script_path],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.info("stdout: %s", result.stdout.strip())
            if result.stderr:
                logger.warning("stderr (non-fatal): %s", result.stderr.strip())
        except subprocess.CalledProcessError as e:
            logger.error("Script failed with code %s", e.returncode)
            logger.error("stderr: %s", e.stderr.strip())
            raise RuntimeError(f"Failed to execute script: {script_path}") from e
