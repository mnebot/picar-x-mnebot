"""
Configuració centralitzada de logging per al projecte Picar-X.
Escriu a consola (amb colors) i a fitxer (format JSON per Loki).
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formatador que escriu logs en format JSON per facilitar el parsing a Loki."""

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "logger": record.name,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False) + "\n"


class ColoredStreamHandler(logging.StreamHandler):
    """Handler que aplica colors als nivells de log a la consola."""

    COLORS = {
        logging.DEBUG: "\033[1;30m",    # Gray
        logging.INFO: "\033[0m",         # Default
        logging.WARNING: "\033[0;33m",   # Yellow
        logging.ERROR: "\033[0;31m",     # Red
        logging.CRITICAL: "\033[1;31m",  # Bold Red
    }
    RESET = "\033[0m"

    def emit(self, record):
        try:
            msg = self.format(record)
            color = self.COLORS.get(record.levelno, self.RESET)
            stream = self.stream
            stream.write(color + msg + self.RESET + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


_configured = False


def setup_logging(log_file=None, level=None):
    """
    Configura el logging global del projecte.

    Variables d'entorn:
        PICARX_LOG_FILE: Ruta al fitxer de logs (per defecte: logs/app.log)
        PICARX_LOG_LEVEL: Nivell de log (DEBUG, INFO, WARNING, ERROR; per defecte: INFO)
        PICARX_LOG_CONSOLE: "1" per habilitar sortida a consola (per defecte: habilitat)
        PICARX_LOG_FILE_ENABLED: "1" per escriure a fitxer (per defecte: habilitat)

    Returns:
        logging.Logger: Logger del mòdul principal
    """
    if log_file is None:
        log_file = os.environ.get("PICARX_LOG_FILE", "logs/app.log")
    if level is None:
        level_str = os.environ.get("PICARX_LOG_LEVEL", "INFO").upper()
        level = getattr(logging, level_str, logging.INFO)
    console_enabled = os.environ.get("PICARX_LOG_CONSOLE", "1") == "1"
    file_enabled = os.environ.get("PICARX_LOG_FILE_ENABLED", "1") == "1"

    global _configured  # noqa: PLW0603
    if _configured:
        return logging.getLogger("picarx")

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if console_enabled:
        console_handler = ColoredStreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        root_logger.addHandler(console_handler)

    if file_enabled:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, mode=0o755, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(JsonFormatter())
        root_logger.addHandler(file_handler)

    _configured = True  # noqa: PLW0602
    return logging.getLogger("picarx")
