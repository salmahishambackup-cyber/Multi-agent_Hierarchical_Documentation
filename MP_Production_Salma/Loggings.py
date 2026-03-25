"""
Centralized logging and memory tracking.
Provides a PipelineLogger that wraps Python's logging module with:
  - Automatic memory usage in every log line
  - Structured step timing
  - Consistent formatting whether a logger is provided or not
"""

import os
import time
import logging
import tracemalloc
import psutil


def get_ram_gb():
    """Current process RSS in GB."""
    return psutil.Process(os.getpid()).memory_info().rss / 1024 ** 3

class PipelineLogger:
    """
    Unified logger that:
      - Prefixes every message with [RAM: X.XX GB]
      - Supports step timing via step_start / step_end
      - Falls back to print() if no stdlib logger is provided
    """

    def __init__(self, name="MatchingPair", logger=None, level=logging.INFO):
        if logger is not None:
            self._logger = logger
        else:
            self._logger = logging.getLogger(name)
            if not self._logger.handlers:
                handler = logging.StreamHandler()
                fmt = logging.Formatter(
                    "[%(asctime)s] [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
                handler.setFormatter(fmt)
                self._logger.addHandler(handler)
            self._logger.setLevel(level)

        self._step_timers = {}

    # ── Core log methods ──

    def _format(self, message):
        ram = get_ram_gb()
        return f"[RAM: {ram:.2f} GB] {message}"

    def info(self, message):
        self._logger.info(self._format(message))

    def warning(self, message):
        self._logger.warning(self._format(message))

    def error(self, message):
        self._logger.error(self._format(message))

    def critical(self, message):
        self._logger.critical(self._format(message))

    # ── Step timing ──

    def step_start(self, step_name):
        """Mark the beginning of a named pipeline step."""
        self._step_timers[step_name] = time.time()
        self.info(f"── {step_name} started ──")

    def step_end(self, step_name):
        """Mark the end of a named pipeline step and log elapsed time."""
        elapsed = time.time() - self._step_timers.pop(step_name, time.time())
        minutes = elapsed / 60
        self.info(f"── {step_name} finished in {minutes:.2f} min ──")

    # ── Tracemalloc helpers ──

    @staticmethod
    def start_tracing():
        tracemalloc.start()

    @staticmethod
    def stop_tracing():
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return current / 1024 ** 2, peak / 1024 ** 2
        return 0.0, 0.0