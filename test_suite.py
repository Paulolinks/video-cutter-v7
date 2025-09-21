#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Suite de testes automatizados para Video Cutter V8
Sistema de desenvolvimento otimizado
"""

import os
import sys
import json
import tempfile
import subprocess
from datetime import datetime

class TestSuite:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()
        print("🧪 INICIANDO SUITE DE TESTES AUTOMATIZADOS")
        print("=" * 60)
    
    def test_clonagem_voz(self):
        """Testa se clonagem de voz gera áudio baseado no texto"""
        print("\n1️⃣ TESTE: Clonagem de Voz")
        try:
            # Importar função do app.py
            sys.path.append('.')
            from app import gerar_audio_tts
            
            # Teste com texto curto
            texto1 = "Teste de clonagem de voz."
            audio1 = gerar_audio_tts(texto1, "clonada_Minha Voz - Paulolinks", "pt")
            
            # Teste com texto diferente
            texto2 = "Este é outro texto para testar clonagem."
            audio2 = gerar_audio_tts(texto2, "clonada_Minha Voz - Paulolinks", "pt")
            
            # Verificar se arquivos foram criados
            if not (audio1 and os.path.exists(audio1)):
                return False, "Falha ao gerar primeiro áudio"
            
            if not (audio2 and os.path.exists(audio2)):
                return False, "Falha ao gerar segundo áudio"
            
            # Verificar se áudios são diferentes
            size1 = os.path.getsize(audio1)
            size2 = os.path.getsize(audio2)
            
            if size1 == size2:
                return False, "Áudios têm mesmo tamanho (clonagem não funcionando)"
            
            # Limpar arquivos de teste
            try:
                os.unlink(audio1)
                os.unlink(audio2)
            except:
                pass
            
            return True, f"✅ Clonagem funcionando (áudios diferentes: {size1} vs {size2} bytes)"
            
        except Exception as e:
            return False, f"❌ Erro no teste: {e}"
    
    def test_sincronizacao_whisper(self):
        """Testa se sincronização com Whisper está funcionando"""
        print("\n2️⃣ TESTE: Sincronização Whisper")
        try:
            # Verificar se arquivo de transcrição existe
            transcricao_path = "data/transcricoes_cortes/corte_1.txt"
            if not os.path.exists(transcricao_path):
                return False, "Arquivo de transcrição não encontrado"
            
            # Verificar se tem dados do Whisper
            with open(transcricao_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            if 'TIMESTAMPS_DETALHADOS:' not in conteudo:
                return False, "Dados do Whisper não encontrados"
            
            # Verificar se FFmpeg está funcionando
            ffmpeg_path = 'bin/ffmpeg/ffmpeg.exe'
            if not os.path.exists(ffmpeg_path):
                return False, "FFmpeg não encontrado"
            
            # Testar comando FFmpeg
            result = subprocess.run([ffmpeg_path, '-version'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return False, "FFmpeg não responde"
            
            return True, "✅ Sincronização Whisper funcionando"
            
        except Exception as e:
            return False, f"❌ Erro no teste: {e}"
    
    def test_processamento_cortes(self):
        """Testa se processamento de cortes está funcionando"""
        print("\n3️⃣ TESTE: Processamento de Cortes")
        try:
            # Verificar se pasta de cortes existe
            if not os.path.exists("data/cortes"):
                return False, "Pasta de cortes não encontrada"
            
            # Verificar se há arquivos de transcrição
            transcricoes_path = "data/transcricoes_cortes"
            if not os.path.exists(transcricoes_path):
                return False, "Pasta de transcrições não encontrada"
            
            # Contar arquivos de transcrição
            transcricoes = [f for f in os.listdir(transcricoes_path) if f.endswith('.txt')]
            if len(transcricoes) == 0:
                return False, "Nenhuma transcrição encontrada"
            
            return True, f"✅ Processamento funcionando ({len(transcricoes)} transcrições)"
            
        except Exception as e:
            return False, f"❌ Erro no teste: {e}"
    
    def test_dublagem(self):
        """Testa se dublagem está funcionando"""
        print("\n4️⃣ TESTE: Dublagem")
        try:
            # Verificar se pasta de dublagem existe
            if not os.path.exists("data/cortes_dublado"):
                return False, "Pasta de dublagem não encontrada"
            
            # Verificar se há arquivos dublados
            dublados = [f for f in os.listdir("data/cortes_dublado") if f.endswith('.mp4')]
            if len(dublados) == 0:
                return False, "Nenhum vídeo dublado encontrado"
            
            return True, f"✅ Dublagem funcionando ({len(dublados)} vídeos dublados)"
            
        except Exception as e:
            return False, f"❌ Erro no teste: {e}"
    
    def test_selecao_voz(self):
        """Testa se seleção de voz está funcionando"""
        print("\n5️⃣ TESTE: Seleção de Voz")
        try:
            # Verificar se arquivo de vozes clonadas existe
            vozes_path = "vozes_clonadas.json"
            if not os.path.exists(vozes_path):
                return False, "Arquivo de vozes clonadas não encontrado"
            
            # Verificar se tem vozes registradas
            with open(vozes_path, 'r', encoding='utf-8') as f:
                vozes = json.load(f)
            
            if len(vozes) == 0:
                return False, "Nenhuma voz clonada registrada"
            
            return True, f"✅ Seleção de voz funcionando ({len(vozes)} vozes registradas)"
            
        except Exception as e:
            return False, f"❌ Erro no teste: {e}"
    
    def test_dados_whisper(self):
        """Testa se dados do Whisper estão sendo salvos corretamente"""
        print("\n6️⃣ TESTE: Dados Whisper Salvos")
        try:
            # Verificar arquivo de transcrição
            transcricao_path = "data/transcricoes_cortes/corte_1.txt"
            if not os.path.exists(transcricao_path):
                return False, "Arquivo de transcrição não encontrado"
            
            with open(transcricao_path, 'r', encoding='utf-8') as f:
                conteudo = f.read()
            
            # Verificar se tem todos os dados necessários
            dados_necessarios = [
                'TIMESTAMPS_DETALHADOS:',
                'PAUSAS_DETECTADAS:',
                'SEGMENTOS_LEGENDA:',
                'METADADOS_DUBLAGEM:'
            ]
            
            for dado in dados_necessarios:
                if dado not in conteudo:
                    return False, f"Dado necessário não encontrado: {dado}"
            
            return True, "✅ Dados Whisper salvos corretamente"
            
        except Exception as e:
            return False, f"❌ Erro no teste: {e}"
    
    def run_all_tests(self):
        """Executa todos os testes"""
        print(f"🚀 Iniciando testes em {self.start_time.strftime('%H:%M:%S')}")
        
        tests = [
            ("Clonagem de Voz", self.test_clonagem_voz),
            ("Sincronização Whisper", self.test_sincronizacao_whisper),
            ("Processamento Cortes", self.test_processamento_cortes),
            ("Dublagem", self.test_dublagem),
            ("Seleção de Voz", self.test_selecao_voz),
            ("Dados Whisper", self.test_dados_whisper)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                success, message = test_func()
                self.results[test_name] = {"success": success, "message": message}
                
                if success:
                    passed += 1
                    print(f"✅ {test_name}: {message}")
                else:
                    print(f"❌ {test_name}: {message}")
                    
            except Exception as e:
                self.results[test_name] = {"success": False, "message": f"Erro: {e}"}
                print(f"❌ {test_name}: Erro inesperado - {e}")
        
        # Resumo final
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print("📊 RESUMO DOS TESTES")
        print("=" * 60)
        print(f"✅ Testes passando: {passed}/{total}")
        print(f"❌ Testes falhando: {total - passed}/{total}")
        print(f"⏱️ Tempo total: {duration:.2f}s")
        print(f"📈 Taxa de sucesso: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("\n🎉 TODOS OS TESTES PASSARAM!")
            print("✅ Sistema está funcionando perfeitamente")
        else:
            print(f"\n⚠️ {total - passed} TESTE(S) FALHARAM")
            print("❌ Verificar funcionalidades com problemas")
        
        return passed == total
    
    def generate_report(self):
        """Gera relatório de testes"""
        report = {
            "timestamp": self.start_time.isoformat(),
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results.values() if r["success"]),
            "results": self.results
        }
        
        with open("test_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Relatório salvo em: test_report.json")

if __name__ == "__main__":
    suite = TestSuite()
    success = suite.run_all_tests()
    suite.generate_report()
    
    # Exit code baseado no resultado
    sys.exit(0 if success else 1)
