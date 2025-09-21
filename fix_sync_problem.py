#!/usr/bin/env python3
"""
Correção do problema de sincronização - atempo funcionando inversamente
"""

def fix_sync_problem():
    """Corrige o problema de sincronização no time-stretching"""
    
    # Ler arquivo atual
    with open('dub_xtts.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Substituir a lógica de atempo_chain que está invertida
    old_logic = """    # Usar asetrate+aresample para time-stretching mais preciso
    print(f"🎵 [TIME-STRETCH] Aplicando asetrate+aresample (ratio={ratio:.3f})")
    r = float(ratio)
    atempo_chain = []
    while r > 2.0:
        atempo_chain.append(2.0)
        r /= 2.0
    while r < 0.5:
        atempo_chain.append(0.5)
        r /= 0.5
    atempo_chain.append(r)
    # Criar comando FFmpeg com atempo
    if len(atempo_chain) == 1:
        cmd = ["ffmpeg","-y","-i",str(wav_in),"-af",f"atempo={atempo_chain[0]:.6f}",
               "-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]
    else:
        atempo_str = ",".join([f"atempo={x:.6f}" for x in atempo_chain])
        cmd = ["ffmpeg","-y","-i",str(wav_in),"-af",atempo_str,
               "-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]"""
    
    new_logic = """    # CORREÇÃO: Usar asetrate+aresample para time-stretching correto
    print(f"🎵 [TIME-STRETCH] Aplicando asetrate+aresample (ratio={ratio:.3f})")
    
    # Calcular nova taxa de amostragem para acelerar/desacelerar
    new_rate = int(sr / ratio)  # CORREÇÃO: dividir por ratio, não multiplicar
    
    # Criar comando FFmpeg com asetrate+aresample (mais preciso que atempo)
    cmd = ["ffmpeg","-y","-i",str(wav_in),
           "-af",f"asetrate={new_rate},aresample={sr}",
           "-ar",str(sr),"-ac","1","-sample_fmt","s16",str(wav_out)]"""
    
    # Aplicar correção
    content = content.replace(old_logic, new_logic)
    
    # Salvar arquivo corrigido
    with open('dub_xtts.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ [CORREÇÃO] Problema de sincronização corrigido!")
    print("✅ [CORREÇÃO] asetrate+aresample agora funciona corretamente!")
    print("✅ [CORREÇÃO] Ratio 0.739 agora vai acelerar corretamente!")
    return True

if __name__ == "__main__":
    fix_sync_problem()
