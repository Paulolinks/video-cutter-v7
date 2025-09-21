#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de verificação automática de funcionalidades críticas
Executar ANTES de qualquer modificação no código
"""

def verificar_funcionalidades_criticas():
    """Verifica se todas as funcionalidades críticas estão presentes"""
    
    print("🔍 VERIFICAÇÃO DE FUNCIONALIDADES CRÍTICAS")
    print("=" * 50)
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    funcionalidades_ok = True
    
    # 1. Verificar sincronização com Whisper
    if 'TIMESTAMPS_DETALHADOS' in content and 'fator_velocidade' in content:
        print("✅ Sincronização com Whisper: OK")
    else:
        print("❌ Sincronização com Whisper: FALTANDO")
        funcionalidades_ok = False
    
    # 2. Verificar clonagem de voz
    if 'vozes_clonadas.json' in content and 'clonada_' in content:
        print("✅ Clonagem de voz: OK")
    else:
        print("❌ Clonagem de voz: FALTANDO")
        funcionalidades_ok = False
    
    # 3. Verificar ajuste de velocidade com FFmpeg
    if 'atempo=' in content and 'ffmpeg' in content.lower():
        print("✅ Ajuste de velocidade FFmpeg: OK")
    else:
        print("❌ Ajuste de velocidade FFmpeg: FALTANDO")
        funcionalidades_ok = False
    
    # 4. Verificar processamento de dados do Whisper
    if 'duracao_total_whisper' in content and 'timestamps_whisper' in content:
        print("✅ Processamento dados Whisper: OK")
    else:
        print("❌ Processamento dados Whisper: FALTANDO")
        funcionalidades_ok = False
    
    print("\n" + "=" * 50)
    if funcionalidades_ok:
        print("🎯 TODAS AS FUNCIONALIDADES CRÍTICAS ESTÃO PRESENTES")
        print("✅ PODE PROSSEGUIR COM MODIFICAÇÕES")
    else:
        print("⚠️ ALGUMAS FUNCIONALIDADES CRÍTICAS ESTÃO FALTANDO")
        print("❌ NÃO PROSSEGUIR SEM RESTAURAR FUNCIONALIDADES")
    
    return funcionalidades_ok

if __name__ == "__main__":
    verificar_funcionalidades_criticas()
