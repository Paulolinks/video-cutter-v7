# nao esta utilizando mais






import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.fx.all import fadein, fadeout

def legendar_video_com_texto(video_path, texto_legenda, saida_path):
    # Carregar vídeo original
    clip = VideoFileClip(video_path)

    # Trocar FONTE - COR das legendas
    # Criar texto (você pode trocar fonte se quiser)
    legenda = TextClip(
        texto_legenda,
        fontsize=60,
        color='yellow',
        font='Arial-Bold',
        stroke_color='black',
        stroke_width=2,
        method='caption',
        size=(clip.w * 0.9, None),
    ).set_position(("center", "bottom")).set_duration(clip.duration)

    # Adicionar entrada/saída suave
    legenda = fadein(legenda, 0.5)
    legenda = fadeout(legenda, 0.5)

    # Combinar vídeo + legenda
    final = CompositeVideoClip([clip, legenda])


    # Executar teste de velocidade de renderização
    #codec="libx264",
    # Exportar
    final.write_videofile(
        saida_path,
        codec="libx264",
        audio_codec="aac",
        threads=os.cpu_count(),      # usa todos núcleos    threads=4, 
        preset="ultrafast"
    )

def legendar_cortes_em_lote(cortes, traducoes):
    os.makedirs("data/final", exist_ok=True)

    for i, corte in enumerate(cortes):
        entrada = f"data/cortes/corte_{i+1}.mp4"
        saida = f"data/final/corte_{i+1}_legendado.mp4"
        texto = traducoes[i] if i < len(traducoes) else "Legenda não encontrada"

        print(f"🎬 Legendando: {entrada}")
        legendar_video_com_texto(entrada, texto, saida)

# Exemplo de uso
if __name__ == "__main__":
    # Legendas traduzidas na ordem dos cortes (pode vir do mesmo `partes`)
    traducoes = [
        "Esta mulher é tão incrível, mano.",
        "A publicidade tem seus carros e roupas de perseguição...",
        "Você pode construir um muro financeiro em torno de sua família.",
        "Os homens do Titanic não pareciam morrer naquele dia.",
        "Um irlandês quando um caso em que seu título mundial se mantinha?",
        "Um irlandês quando uma briga no UFC realizou?",
        "Homens fracos criam tempos difíceis."
    ]

    cortes = list(range(1, len(traducoes) + 1))
    legendar_cortes_em_lote(cortes, traducoes)
