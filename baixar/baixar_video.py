import os
import subprocess

def baixar_video(video_url):
    os.makedirs("data/videos", exist_ok=True)
    output_path = os.path.join("data/videos", "video.mp4")

    cookies_path = "cookies.txt"
    usa_cookies = os.path.exists(cookies_path)

    if not usa_cookies:
        print("⚠️ Aviso: O arquivo 'cookies.txt' não foi encontrado.")
        print("🔐 Alguns vídeos exigem login no YouTube para serem baixados.")
        print("➡️ Para resolver isso, siga os passos:")
        print("1. Acesse o site https://youtube.com e faça login.")
        print("2. Instale a extensão 'Get cookies.txt' no Chrome ou Brave:")
        print("   👉 https://chrome.google.com/webstore/detail/get-cookiestxt/lgmpcagfacmejljfelfcmlokjbjboobg")
        print("3. Gere o cookies.txt e salve na mesma pasta do app.")
        print("⚠️ Sem esse arquivo, vídeos protegidos por login ou verificação podem falhar.")


    def tentar_comando(comando):
        try:
            result = subprocess.run(
                comando,
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            return e.stderr or e.stdout or str(e)

    # Primeiro: tenta formato 22 (MP4 direto)
    comando1 = ["yt-dlp", "-f", "22", "-o", output_path]
    if usa_cookies:
        comando1.extend(["--cookies", "cookies.txt"])
    comando1.append(video_url)

    resultado = tentar_comando(comando1)

    # Se falhar, tenta bestvideo+bestaudio com merge para mp4
    if resultado is not True:
        comando2 = [
            "yt-dlp",
            "-f", "bestvideo+bestaudio",
            "--merge-output-format", "mp4",
            "-o", output_path
        ]
        if usa_cookies:
            comando2.extend(["--cookies", "cookies.txt"])
        comando2.append(video_url)

        resultado = tentar_comando(comando2)

        if resultado is not True:
            raise Exception(f"❌ Erro ao baixar o vídeo:\n{resultado}")

    # Verifica se o arquivo foi criado
    if not os.path.exists(output_path):
        raise Exception("❌ Download falhou: o arquivo do vídeo não foi criado.")

    return output_path
