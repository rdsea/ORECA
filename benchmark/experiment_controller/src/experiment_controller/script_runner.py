import subprocess
import time

from experiment_controller.logger import logger


class ScriptRunner:
    """Executes local shell scripts and streams output continuously."""

    def run(self, script_path: str):
        """Runs a shell script and logs its output in real time.

        Args:
            script_path (str): The path to the script to execute.

        Raises:
            RuntimeError: If the script fails to execute.
        """
        try:
            process = subprocess.Popen(
                ["bash", script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # line-buffered
            )

            # Stream stdout
            if process.stdout is not None:
                for line in process.stdout:
                    logger.info("stdout: %s", line.rstrip())

            # Stream stderr
            if process.stderr is not None:
                for line in process.stderr:
                    logger.warning("stderr: %s", line.rstrip())

            process.wait()

            if process.returncode != 0:
                raise RuntimeError(
                    f"Script failed with code {process.returncode}: {script_path}"
                )

        except OSError as e:
            logger.error("Execution failed: %s", e)
            raise RuntimeError(f"Failed to execute script: {script_path}") from e

    def run_retry(self, script_path: str, retries: int = 3, delay: int = 30):
        """Runs a shell script with retries.

        Args:
            script_path (str): Path to the script to execute.
            retries (int): Number of total attempts.
            delay (int): Delay in seconds between retries.

        Raises:
            RuntimeError: If all attempts fail.
        """
        for attempt in range(1, retries + 1):
            try:
                self.run(script_path)
                logger.info("Script executed successfully on attempt %d", attempt)
                return
            except RuntimeError:
                if attempt < retries:
                    logger.warning(
                        "Attempt %d/%d failed. Retrying in %d seconds...",
                        attempt,
                        retries,
                        delay,
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        "All %d attempts failed for script: %s", retries, script_path
                    )
                    raise
