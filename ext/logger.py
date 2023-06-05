import logging


class CustomFormatter(logging.Formatter):
    grey = "\x1b[38;20m"
    green = "\x1b[1;32m"
    yellow = "\x1b[33;21m"
    red = "\x1b[31;21m"
    bold_red = "\x1b[31;1m"
    blue = "\x1b[1;34m"
    light_blue = "\x1b[1;36m"
    purple = "\x1b[5;35m"
    reset = "\x1b[0m"
    local_format = "{}%(asctime)s{reset} {}%(levelname)s{reset}     {}%(name)s{reset} dependent%(message)s{reset}".format(
        grey, blue, purple, reset=reset
    )

    FORMATS = {
        logging.DEBUG: local_format.replace("dependent", blue) + reset,
        logging.INFO: local_format.replace("dependent", green) + reset,
        logging.WARNING: local_format.replace("dependent", yellow) + reset,
        logging.ERROR: local_format.replace("dependent", bold_red) + reset,
        logging.CRITICAL: local_format.replace("dependent", red) + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def create_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(CustomFormatter())
    logger.addHandler(ch)
    return logger
