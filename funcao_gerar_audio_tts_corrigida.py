def gerar_audio_tts(texto, voice, lang_target):
    """Gera áudio usando TTS (Text-to-Speech) - versão corrigida"""
    try:
        import tempfile
        import subprocess
        import os
        
        print(f"Gerando áudio TTS para: {texto[:50]}...")
        print(f"Idioma: {lang_target}, Voz: {voice}")
        
        # Criar arquivo temporário para áudio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            audio_path = temp_file.name
        
        # Método 1: PowerShell TTS (mais confiável no Windows)
        try:
            print("Usando PowerShell TTS...")
            
            # Escapar aspas no texto
            texto_escapado = texto.replace('"', '\\"').replace("'", "\\'")
            
            # Comando PowerShell com voz em português
            if lang_target == "pt":
                # Usar pyttsx3 com configuração especial para português
                print("Tentando pyttsx3 para português...")
                try:
                    import pyttsx3
                    engine = pyttsx3.init()
            
                    # Listar vozes disponíveis
                    voices = engine.getProperty('voices')
                    print(f"🔍 Vozes disponíveis: {len(voices)}")
                    for i, voice in enumerate(voices):
                        print(f"  {i}: {voice.name} - {voice.languages}")
                    
                    # Tentar encontrar voz em português
                    voz_selecionada = None
                    for voice in voices:
                        if any('pt' in lang.lower() or 'portuguese' in lang.lower() for lang in voice.languages):
                            voz_selecionada = voice
                            print(f"✅ Voz em português encontrada: {voice.name}")
                            break
        
                    # Se não encontrou voz em português, pular pyttsx3 e ir direto para Edge TTS
                    if not voz_selecionada:
                        print("❌ Nenhuma voz em português encontrada no pyttsx3, pulando para Edge TTS...")
                        raise Exception("Nenhuma voz em português disponível")
                    
                    if voz_selecionada:
                        engine.setProperty('voice', voz_selecionada.id)
                    
                    # Configurar para melhor pronúncia em português
                    engine.setProperty('rate', 120)  # Velocidade mais lenta para português
                    engine.setProperty('volume', 1.0)  # Volume máximo
                    
                    # Salvar áudio
                    engine.save_to_file(texto, audio_path)
                    engine.runAndWait()
                    
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        print(f"✅ Áudio pyttsx3 gerado: {audio_path} ({os.path.getsize(audio_path)} bytes)")
                        return audio_path
                    else:
                        print("❌ pyttsx3 falhou, tentando Edge TTS...")
        
                except Exception as e:
                    print(f"Erro com pyttsx3: {e}, tentando PowerShell...")
                
                # Fallback: Usar Edge TTS (Microsoft) para português
                print("Tentando Edge TTS para português...")
                try:
                    import edge_tts
                    import asyncio
        
                    # Vozes em português disponíveis no Edge TTS
                    vozes_pt = [
                        'pt-BR-ValerioNeural',    # Voz masculina GRAVE e natural
                        'pt-BR-HumbertoNeural',   # Voz masculina grave e profissional
                    ]
                    
                    # Usar voz masculina GRAVE (ValerioNeural)
                    voz_selecionada = vozes_pt[0]
                    print(f"🎤 Usando voz: {voz_selecionada}")
                    
                    # Criar áudio com Edge TTS
                    async def gerar_audio():
                        communicate = edge_tts.Communicate(
                            texto, 
                            voz_selecionada,
                            rate="+0%",
                            pitch="+0Hz",
                            volume="+0%"
                        )
                        await communicate.save(audio_path)
                    
                    # Executar função assíncrona
                    asyncio.run(gerar_audio())
                    
                    if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                        print(f"✅ Áudio Edge TTS gerado: {audio_path} ({os.path.getsize(audio_path)} bytes)")
                        return audio_path
                    else:
                        print("❌ Edge TTS falhou, tentando PowerShell...")
                        
                except ImportError:
                    print("Edge TTS não instalado, tentando PowerShell...")
                except Exception as e:
                    print(f"Erro com Edge TTS: {e}, tentando PowerShell...")
                
                # Último fallback: PowerShell
                print("Usando PowerShell com configuração para português...")
                cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.SetOutputToWaveFile("{audio_path}"); $speak.Rate = -2; $speak.Volume = 100; $speak.Speak("{texto_escapado}")'
            else:
                cmd = f'Add-Type -AssemblyName System.Speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.SetOutputToWaveFile("{audio_path}"); $speak.Speak("{texto_escapado}")'
            
            print(f"Executando comando: {cmd[:100]}...")
            
            result = subprocess.run(['powershell', '-Command', cmd], 
                                  capture_output=True, text=True, timeout=30)
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"✅ Áudio PowerShell gerado: {audio_path} ({os.path.getsize(audio_path)} bytes)")
                return audio_path
            else:
                print(f"❌ PowerShell falhou - arquivo não criado ou vazio")
                
        except Exception as e:
            print(f"Erro com PowerShell: {e}")
        
        # Método 2: pyttsx3 (fallback)
        try:
            print("Tentando pyttsx3...")
            import pyttsx3
            
            engine = pyttsx3.init()
            
            # Configurar voz
            voices = engine.getProperty('voices')
            if voices:
                # Tentar encontrar voz apropriada
                for voice_obj in voices:
                    voice_name = voice_obj.name.lower()
                    if lang_target == 'en' and ('english' in voice_name or 'en' in voice_name):
                        engine.setProperty('voice', voice_obj.id)
                        break
                    elif lang_target == 'es' and ('spanish' in voice_name or 'es' in voice_name):
                        engine.setProperty('voice', voice_obj.id)
                        break
                    elif lang_target == 'pt' and ('portuguese' in voice_name or 'pt' in voice_name):
                        engine.setProperty('voice', voice_obj.id)
                        break
            
            # Configurar velocidade
            engine.setProperty('rate', 150)
            engine.setProperty('volume', 0.9)
            
            # Salvar áudio
            engine.save_to_file(texto, audio_path)
            engine.runAndWait()
            
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                print(f"✅ Áudio pyttsx3 gerado: {audio_path}")
                return audio_path
            
        except Exception as e:
            print(f"Erro com pyttsx3: {e}")
        
        # Método 3: Criar arquivo de áudio silencioso como fallback
        try:
            print("Criando áudio silencioso como fallback...")
            import numpy as np
            import wave
            
            # Configurações do áudio
            sample_rate = 44100
            duration = 2.0  # 2 segundos de silêncio
            samples = int(sample_rate * duration)
            
            # Gerar silêncio
            silence = np.zeros(samples, dtype=np.int16)
            
            # Salvar como WAV
            with wave.open(audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(silence.tobytes())
            
            print(f"✅ Áudio silencioso criado: {audio_path}")
            return audio_path
            
        except Exception as e:
            print(f"Erro ao criar áudio silencioso: {e}")
        
        print("❌ Todos os métodos TTS falharam")
        return None
                
    except Exception as e:
        print(f"Erro geral no TTS: {e}")
        return None
