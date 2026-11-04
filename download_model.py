from pathlib import Path
from huggingface_hub import snapshot_download

TARGET = Path(__file__).resolve().parent / "core" / "faster-whisper-large-v3-turbo-ct2"

snapshot_download(
    repo_id="deepdml/faster-whisper-large-v3-turbo-ct2",
    local_dir=TARGET,
    allow_patterns=[
        "config.json", "model.bin", "tokenizer.json",
        "vocabulary.*", "preprocessor_config.json",
    ],
)
print("Готово:", TARGET)