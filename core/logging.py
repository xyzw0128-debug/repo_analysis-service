import json
import logging


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            'level': record.levelname,
            'message': record.getMessage(),
            'name': getattr(record, 'name', None),
        }
        for k, v in record.__dict__.items():
            if k not in {'args','asctime','created','exc_info','exc_text','filename','funcName','levelname','levelno','lineno','module','msecs','message','msg','name','pathname','process','processName','relativeCreated','stack_info','thread','threadName'}:
                payload[k] = v
        return json.dumps(payload)


def _configure_root() -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    h = logging.StreamHandler()
    h.setFormatter(JsonFormatter())
    root.addHandler(h)
    root.setLevel(logging.INFO)


class BoundAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get('extra', {})
        kwargs['extra'] = {**extra, 'logger_name': self.extra['logger_name']}
        return msg, kwargs


def get_logger(name: str):
    _configure_root()
    return BoundAdapter(logging.getLogger(name), {'logger_name': name})
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
import structlog


def configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.JSONRenderer(),
        ]
    )


def get_logger(name: str):
    return structlog.get_logger(name)
