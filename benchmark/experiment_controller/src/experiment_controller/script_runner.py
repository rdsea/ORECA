import logging
import subprocess

from tenacity import (
    before_sleep_log,
    retry,
    stop_after_attempt,
    wait_exponential_jitter,
)

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
        logger.info(f"Starting script executio for script path {script_path}")
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

    @retry(
        wait=wait_exponential_jitter(exp_base=2, initial=5, max=30),
        reraise=True,
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def run_retry(self, script_path: str):
        """Runs a shell script with automatic retries using stamina.

        Args:
            script_path (str): Path to the script to execute.

        Raises:
            RuntimeError: If all attempts fail.
        """
        self.run(script_path)
        logger.info("Script executed successfully: %s", script_path)
