import json
import os
from dataclasses import asdict, dataclass

from platformdirs import user_config_dir

CONFIG_DIR = user_config_dir("sdrmon", "sdrmon")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")


@dataclass
class SDRmonConfig:
    preferred_device: str = ""
    center_frequency: int = 100_000_000
    sample_rate: int = 2_000_000
    gain: float = 0.0
    audio_output: str = ""
    mode: str = "wfm"
    volume: float = 0.5
    squelch: float = -50.0
    dark_mode: bool = True

    @classmethod
    def load(cls) -> "SDRmonConfig":
        if not os.path.exists(CONFIG_FILE):
            return cls()
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
            # Only keep known keys
            known = {k: v for k, v in data.items() if k in cls.__dataclass_fields__}
            return cls(**known)
        except Exception:
            return cls()

    def save(self) -> None:
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(asdict(self), f, indent=4)
