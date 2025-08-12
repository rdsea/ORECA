import logging

logger = logging.getLogger(f"{__name__}")

c_handler = logging.StreamHandler()
c_handler.setLevel(logging.WARNING)
c_format = logging.Formatter(
    "%(module)s : %(asctime)s : %(levelname)s  - %(message)s",
)
c_handler.setFormatter(c_format)
logger.addHandler(c_handler)
