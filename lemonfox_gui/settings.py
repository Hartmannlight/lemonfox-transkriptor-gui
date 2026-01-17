import json
from dataclasses import dataclass, asdict
from pathlib import Path

APP_DIR = Path.home() / ".lemonfox_transkriptor_gui"
SETTINGS_PATH = APP_DIR / "settings.json"


@dataclass
class AppSettings:
    api_token: str = ""
    api_base: str = "https://api.lemonfox.ai"
    language: str = ""
    response_format: str = "json"
    prompt: str = ""
    translate: bool = False
    speaker_labels: bool = False
    min_speakers: str = ""
    max_speakers: str = ""
    word_timestamps: bool = False
    callback_url: str = ""
    audio_dir: str = str(APP_DIR / "audio")
    text_dir: str = str(APP_DIR / "text")
    sample_rate: str = "16000"
    channels: str = "1"


def load_settings():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    if SETTINGS_PATH.exists():
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            return AppSettings(**data)
        except Exception:
            pass
    return AppSettings()


def save_settings(settings: AppSettings):
    APP_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(asdict(settings), ensure_ascii=True, indent=2), encoding="utf-8")
