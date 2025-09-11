
import os, shutil
from slugify import slugify

def renomear_video(path_antigo: str, titulo: str, destino_dir: str | None = None) -> str:
    """Renomeia o arquivo de vídeo com base no título (slug), evitando conflitos."""
    base = os.path.dirname(path_antigo) if not destino_dir else destino_dir
    root, ext = os.path.splitext(os.path.basename(path_antigo))
    slug = slugify(titulo)[:70] or "video"
    novo = os.path.join(base, f"{slug}{ext}")
    i = 2
    while os.path.exists(novo):
        novo = os.path.join(base, f"{slug}-{i}{ext}")
        i += 1
    os.makedirs(base, exist_ok=True)
    if os.path.abspath(path_antigo) != os.path.abspath(novo):
        shutil.move(path_antigo, novo)
    return novo
