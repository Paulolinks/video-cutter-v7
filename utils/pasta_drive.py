import json
from pathlib import Path

CONFIG_FILE = Path("pasta_id.json")

def salvar_pasta_id(folder_id):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"folder_id": folder_id}, f)

def carregar_pasta_id():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("folder_id")
    return None


# 1Xvh1Irayw0cpt1d_SG6uq9QV-GkpBXma