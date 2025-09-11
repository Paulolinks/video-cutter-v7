
from .salvar_planilha import carregar_df, PLANILHA

def anexar_id_no_registro(caminho_arquivo: str, file_id: str):
    """Atualiza a planilha metadados com o ID de upload do Google Drive."""
    import pandas as pd
    df = carregar_df()
    idx = df.index[df["arquivo"] == caminho_arquivo]
    if len(idx):
        df.loc[idx, "drive_id"] = file_id
        df.to_excel(PLANILHA, index=False)
