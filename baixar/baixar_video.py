# baixar/baixar_video.py  (somente a função)
import os, sys, shutil, subprocess

def baixar_video(video_url):
    # --- caminhos e pastas ---
    base_dir   = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # ffmpeg (busca robusta)
    def _find_ffmpeg(base_dir: str) -> str:
        candidatos = [
            os.environ.get("IMAGEIO_FFMPEG_EXE"),
            os.path.join(base_dir, "bin", "ffmpeg", "ffmpeg.exe"),
            os.path.join(base_dir, "bin", "ffmep",  "ffmpeg.exe"),
            shutil.which("ffmpeg"),
        ]
        for c in candidatos:
            if c and os.path.exists(c):
                return os.path.abspath(c)
        # varredura final em bin/
        bin_dir = os.path.join(base_dir, "bin")
        if os.path.isdir(bin_dir):
            for raiz, _, arquivos in os.walk(bin_dir):
                for arq in arquivos:
                    if arq.lower().startswith("ffmpeg") and arq.lower().endswith(".exe"):
                        return os.path.abspath(os.path.join(raiz, arq))
        raise FileNotFoundError("ffmpeg.exe não encontrado (coloque em bin/ffmpeg/).")

    ffmpeg_bin = _find_ffmpeg(base_dir)
    ffmpeg_dir = os.path.dirname(ffmpeg_bin)

    os.makedirs(os.path.join(base_dir, "data", "videos"), exist_ok=True)
    output_path  = os.path.join(base_dir, "data", "videos", "video.mp4")

    # --- cookies (opcional) ---
    cookies_path = os.path.join(base_dir, "cookies.txt")
    usa_cookies  = os.path.exists(cookies_path)

    if not usa_cookies:
        print("⚠️ Aviso: O arquivo 'cookies.txt' não foi encontrado.")
        print("🔐 Alguns vídeos exigem login no YouTube para serem baixados.")
        print("➡️ Para resolver isso, siga os passos:")
        print("1. Acesse o site https://youtube.com e faça login.")
        print("2. Instale a extensão 'Get cookies.txt' no Chrome ou Brave:")
        print("   👉 https://chrome.google.com/webstore/detail/get-cookiestxt/lgmpcagfacmejljfelfcmlokjbjboobg")
        print("3. Gere o cookies.txt e salve na mesma pasta do app.")
        print("⚠️ Sem esse arquivo, vídeos protegidos por login ou verificação podem falhar.")

    # PATH do subprocesso (ffmpeg + Scripts do venv)
    env = os.environ.copy()
    venv_scripts = os.path.join(base_dir, ".venv", "Scripts")
    env["PATH"] = ffmpeg_dir + os.pathsep + venv_scripts + os.pathsep + env.get("PATH", "")

    def run(cmd):
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
            return True
        except subprocess.CalledProcessError as e:
            return e.stderr or e.stdout or str(e)

    # yt-dlp via python do venv (não depende de PATH)
    yt = [sys.executable, "-m", "yt_dlp"]

    # variações para contornar bloqueios/PO token
    variantes = [
        [],  # normal
        ["--extractor-args", "youtube:player_client=android"],
        ["--extractor-args", "youtube:po_token=web"],
        ["--extractor-args", "youtube:player_client=ios"],
    ]

    ultimo_erro = None
    for extra in variantes:
        # 1) MP4 direto (itag 22)
        cmd1 = yt + ["--ffmpeg-location", ffmpeg_dir, "-f", "22", "-o", output_path, video_url]
        if usa_cookies:
            cmd1[len(yt):len(yt)] = ["--cookies", cookies_path]
        if extra:
            cmd1[len(yt):len(yt)] = extra
        r = run(cmd1)
        if r is True:
            break  # sucesso

        # 2) bestvideo+bestaudio com merge mp4
        cmd2 = yt + [
            "--ffmpeg-location", ffmpeg_dir,
            "-f", "bv*+ba/best", "--merge-output-format", "mp4",
            "-o", output_path, video_url
        ]
        if usa_cookies:
            cmd2[len(yt):len(yt)] = ["--cookies", cookies_path]
        if extra:
            cmd2[len(yt):len(yt)] = extra
        r = run(cmd2)
        if r is True:
            break

        ultimo_erro = r

    if not os.path.exists(output_path):
        raise Exception(f"❌ Erro ao baixar o vídeo (todas as estratégias):\n{ultimo_erro or 'sem detalhes'}")

    return output_path
