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
