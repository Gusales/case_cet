import inspect
import logging
import logging.config

class ColoredFormatter(logging.Formatter):
    COLORS = {
        logging.DEBUG: '\033[37m',
        logging.INFO: '\033[32m',
        logging.WARNING: '\033[33m',
        logging.ERROR: '\033[31m',
        logging.CRITICAL: '\033[31;1m',
    }

    RESET = '\033[0m'

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        levelname_original = record.levelname
        msg_original = record.msg
        try:
            record.levelname = f"{color}{record.levelname}{self.RESET}"
            record.msg = f"{color}{record.msg}{self.RESET}"
            return super().format(record)
        finally:
            record.levelname = levelname_original
            record.msg = msg_original

handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter(
    fmt='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
))

logging.root.handlers = []
logging.root.addHandler(handler)
logging.root.setLevel(logging.INFO)

def set_level(level: int) -> None:
    """
    Ajusta o nível global dos logs. Use logging.DEBUG para enxergar o
    detalhe iteração a iteração do solver.
    """
    logging.root.setLevel(level)
    logging.getLogger('logger').setLevel(level)

class Logger(logging.LoggerAdapter):
    def __init__(self, cls=None):
        logger = logging.getLogger('logger')
        super().__init__(logger, {})
        self._cls_name = cls.__name__ if cls else None

    def process(self, msg, kwargs):
        if not self._cls_name:
            return msg, kwargs

        method_name = 'unknown'
        frame = inspect.currentframe()
        try:
            while frame is not None:
                frame = frame.f_back
                if frame is None:
                    break

                local_vars = frame.f_locals
                if 'self' in local_vars and local_vars['self'].__class__.__name__ == self._cls_name:
                    method_name = frame.f_code.co_name
                    break
        finally:
            del frame

        return f"- [{self._cls_name}.{method_name}] - {msg}", kwargs

    def get_logger(self):
        return self.logger
