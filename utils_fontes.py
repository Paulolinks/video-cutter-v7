# utils_fontes.py
import os, glob, re
from typing import List, Dict

def _fonts_dir():
    return os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")

def listar_fontes_windows() -> List[str]:
    patterns = ("*.ttf", "*.otf", "*.ttc")
    fdir = _fonts_dir()
    out, seen = [], set()
    for p in patterns:
        for fp in glob.glob(os.path.join(fdir, p)):
            if fp not in seen:
                seen.add(fp); out.append(fp)
    return out

def _nome_e_peso(path: str):
    """Tenta extrair nome legível e peso (OS/2.usWeightClass) via fonttools."""
    try:
        from fontTools.ttLib import TTFont
        tt = TTFont(path, lazy=True)
        # Nome de família (nameID=1)
        name = None
        for rec in tt["name"].names:
            if rec.nameID == 1:  # Family
                name = rec.toUnicode()
                break
        # Peso
        weight = 400
        if "OS/2" in tt and hasattr(tt["OS/2"], "usWeightClass"):
            weight = int(tt["OS/2"].usWeightClass)
        # Itálico
        italic = False
        try:
            italic = (tt["post"].italicAngle != 0) or bool(tt["head"].macStyle & 0b10)
        except Exception:
            pass
        return (name or os.path.basename(path), weight, italic)
    except Exception:
        return (os.path.basename(path), 400, False)

def listar_fontes_legiveis() -> List[Dict]:
    """Retorna [{'name': Nome, 'path': Caminho, 'weight': peso, 'italic': bool}]"""
    out = []
    for p in listar_fontes_windows():
        n, w, it = _nome_e_peso(p)
        out.append({"name": n, "path": p, "weight": w, "italic": it})
    return out

# ---- Filtro de fontes BOAS para leitura em vídeo ----
_BAD_WORDS = re.compile(
    r"(thin|hairline|extralight|ultralight|light|semilight|"
    r"narrow|condensed|cond|extended|italic|oblique)",
    re.I
)

_FAVORITAS = re.compile(
    r"(impact|arial\s*black|franklin\s*gothic\s*heavy|anton|bebas|oswald|"
    r"montserrat|poppins|roboto\s*(bold|black)|segoe\s*ui\s*semibold|"
    r"open\s*sans\s*(extrabold|bold)|noto\s*sans\s*(bold|black)|verdana\s*bold|"
    r"tahoma\s*bold|trebuchet\s*ms\s*bold)",
    re.I
)

def _eh_boa(f):
    name = f["name"]
    if _BAD_WORDS.search(name):   # elimina “fininhas/condensadas/itálicas”
        return False
    # bom peso OU nome sugere família “impactante”
    return f["weight"] >= 600 or bool(_FAVORITAS.search(name))

def listar_fontes_legiveis_filtradas(limit: int = 50) -> List[Dict]:
    fontes = [f for f in listar_fontes_legiveis() if _eh_boa(f)]
    # ordena dando prioridade às favoritas e maior peso
    def key(f):
        fav = 0 if _FAVORITAS.search(f["name"]) else 1
        return (fav, -f["weight"], f["name"].lower())
    fontes.sort(key=key)







    
    # garante que Impact e Arial Black, se existirem, fiquem no topo
    topo = []
    for preferida in ("Impact", "Arial Black"):
        for f in fontes:
            if f["name"].lower() == preferida.lower():
                topo.append(f); break
    # remove duplicatas mantendo ordem
    seen, final = set(), []
    for f in topo + fontes:
        if f["path"] not in seen:
            seen.add(f["path"]); final.append(f)
    if limit:
        final = final[:limit]
    return final

def resolver_fonte(valor: str) -> str:
    """Aceita nome (ex. 'Impact') OU caminho; retorna caminho absoluto."""
    if valor and os.path.isfile(valor):
        return os.path.abspath(valor)
    alvo = (valor or "").strip().lower()
    for f in listar_fontes_legiveis():
        nm = f["name"].lower()
        if nm == alvo or nm.startswith(alvo):
            return os.path.abspath(f["path"])
    # fallback
    return os.path.join(_fonts_dir(), "arial.ttf")

def ffmpeg_fontfile_safe(path: str) -> str:
    return path.replace("\\", "/").replace(":", r"\:")
