import logging


class _NameFilter(logging.Filter):
    def __init__(self, logger_name: str):
        super().__init__()
        self.logger_name = logger_name

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "name"):
            record.name = self.logger_name
        record.logger_name = self.logger_name
        return True


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('{"level":"%(levelname)s","name":"%(logger_name)s","msg":"%(message)s"}'))
        logger.addHandler(handler)
    if not any(isinstance(f, _NameFilter) for f in logger.filters):
        logger.addFilter(_NameFilter(name))
    return logger
