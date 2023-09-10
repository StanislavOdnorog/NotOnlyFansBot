import logging

logger = logging.getLogger()

logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
file_handler = logging.FileHandler(".log", mode="a")

console_handler.setLevel(logging.DEBUG)
file_handler.setLevel(logging.DEBUG)

fmt = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
)

console_handler.setFormatter(fmt)
file_handler.setFormatter(fmt)

logger.addHandler(console_handler)
logger.addHandler(file_handler)
