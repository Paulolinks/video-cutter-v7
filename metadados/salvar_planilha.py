
import os, pandas as pd

PLANILHA_DIR = os.path.join("data","planilhas")
PLANILHA = os.path.join(PLANILHA_DIR, "publicar.xlsx")
CSV      = os.path.join(PLANILHA_DIR, "publicar.csv")

COLS = ["arquivo","titulo","legenda","hashtags","duracao","drive_id","origem","idioma"]

def carregar_df():
    if os.path.exists(PLANILHA):
        return pd.read_excel(PLANILHA)
    if os.path.exists(CSV):
        return pd.read_csv(CSV)
    return pd.DataFrame(columns=COLS)

def salvar_linha(**kwargs):
    df = carregar_df()
    for c in COLS:
        kwargs.setdefault(c, "")
    df = pd.concat([df, pd.DataFrame([kwargs])], ignore_index=True)
    os.makedirs(PLANILHA_DIR, exist_ok=True)
    df.to_excel(PLANILHA, index=False)
    df.to_csv(CSV, index=False)
