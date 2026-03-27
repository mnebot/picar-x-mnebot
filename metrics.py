"""
Mòdul de mètriques Prometheus per al projecte Picar-X.
Exposa l'endpoint /metrics al port configurable per Grafana Alloy.
"""
import os
import threading


def _is_enabled():
    """Comprova si les mètriques estan habilitades via variable d'entorn."""
    return os.environ.get("PICARX_METRICS_ENABLED", "0") == "1"


def _get_port():
    """Retorna el port de mètriques (variable d'entorn o per defecte 9090)."""
    return int(os.environ.get("PICARX_METRICS_PORT", "9090"))


def start_metrics_server():
    """
    Inicia el servidor HTTP de mètriques en un fil daemon.

    Només s'inicia si PICARX_METRICS_ENABLED=1.

    Variables d'entorn:
        PICARX_METRICS_ENABLED: "1" per habilitar (per defecte: "0")
        PICARX_METRICS_PORT: Port per l'endpoint (per defecte: 9090)
    """
    if not _is_enabled():
        return None

    try:
        from prometheus_client import Counter, Histogram, start_http_server
    except ImportError:
        return None

    port = _get_port()
    t = threading.Thread(target=lambda: start_http_server(port), daemon=True)
    t.start()
    return t


# Variables globals (inicialitzades per _init_metrics)
_stt_duration = None
_chat_duration = None
_tts_duration = None
_actions_total = None
_errors_total = None


def record_stt_duration(seconds):
    """Registra la durada d'una crida STT en segons."""
    global _stt_duration
    if _stt_duration is not None:
        _stt_duration.observe(seconds)


def record_chat_duration(seconds):
    """Registra la durada d'una crida GPT en segons."""
    global _chat_duration
    if _chat_duration is not None:
        _chat_duration.observe(seconds)


def record_tts_duration(seconds):
    """Registra la durada d'una crida TTS en segons."""
    global _tts_duration
    if _tts_duration is not None:
        _tts_duration.observe(seconds)


def record_action_executed(action):
    """Registra l'execució d'una acció."""
    global _actions_total
    if _actions_total is not None:
        _actions_total.labels(action=action).inc()


def record_error(module):
    """Registra un error al mòdul indicat."""
    global _errors_total
    if _errors_total is not None:
        _errors_total.labels(module=module).inc()


def _init_metrics():
    """Inicialitza les mètriques Prometheus si estan habilitades."""
    global _stt_duration, _chat_duration, _tts_duration, _actions_total, _errors_total
    if not _is_enabled():
        return
    try:
        from prometheus_client import Counter, Histogram

        _stt_duration = Histogram(
            "picarx_stt_duration_seconds",
            "Durada de les crides STT en segons",
        )
        _chat_duration = Histogram(
            "picarx_chat_duration_seconds",
            "Durada de les crides GPT en segons",
        )
        _tts_duration = Histogram(
            "picarx_tts_duration_seconds",
            "Durada de les crides TTS en segons",
        )
        _actions_total = Counter(
            "picarx_actions_executed_total",
            "Accions executades",
            ["action"],
        )
        _errors_total = Counter(
            "picarx_errors_total",
            "Errors per mòdul",
            ["module"],
        )
    except ImportError:
        pass


_init_metrics()
