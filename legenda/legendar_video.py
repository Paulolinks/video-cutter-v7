from deep_translator import GoogleTranslator

def legendar_com_traducao(partes, idioma):
    print("📝 Etapa de legenda (ainda sem renderizar o vídeo)")

    if idioma == "en":
        for parte in partes:
            traduzido = GoogleTranslator(source='en', target='pt').translate(parte["text"])
            print(f"🇬🇧 {parte['text']}\n🇧🇷 {traduzido}\n")
    else:
        for parte in partes:
            print(f"🇧🇷 {parte['text']}\n")
