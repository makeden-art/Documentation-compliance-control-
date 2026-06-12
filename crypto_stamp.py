import hashlib
import json
from pathlib import Path
from datetime import datetime

# Реестр можно хранить в файле или SQLite. Пока храним в JSON.
REGISTRY_FILE = Path(__file__).parent / "stamp_registry.json"

def init_registry():
    if not REGISTRY_FILE.exists():
        REGISTRY_FILE.write_text(json.dumps({}))

def compute_file_hash(file_path: str) -> str:
    """Вычисляет SHA-256 хеш файла"""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Читаем чанками по 64КБ для экономии памяти
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def register_stamp(file_name: str, file_hash: str) -> dict:
    """Регистрирует файл в базе проверенных (штампует)"""
    init_registry()
    data = json.loads(REGISTRY_FILE.read_text())
    
    stamp_info = {
        "file_name": file_name,
        "hash": file_hash,
        "timestamp": datetime.now().isoformat(),
        "status": "passed_normocontrol"
    }
    
    # Ключом выступает хеш файла, так как мы проверяем именно по хешу
    data[file_hash] = stamp_info
    REGISTRY_FILE.write_text(json.dumps(data, indent=2))
    return stamp_info

def verify_stamp(file_path: str) -> dict:
    """Проверяет подлинность файла по хешу"""
    init_registry()
    file_hash = compute_file_hash(file_path)
    
    data = json.loads(REGISTRY_FILE.read_text())
    if file_hash in data:
        return {"valid": True, "info": data[file_hash]}
    
    return {"valid": False, "error": "Метка сорвана или файл не проходил проверку"}
