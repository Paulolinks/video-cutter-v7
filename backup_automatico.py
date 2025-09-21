#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de backup automático para Video Cutter V8
Cria backup antes de modificações importantes
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path

class BackupAutomatico:
    def __init__(self):
        self.backup_dir = "backups_automaticos"
        self.ensure_backup_dir()
    
    def ensure_backup_dir(self):
        """Cria diretório de backups se não existir"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            print(f"📁 Diretório de backup criado: {self.backup_dir}")
    
    def criar_backup_antes_modificacao(self, arquivo_principal="app.py", motivo="modificacao"):
        """Cria backup automático antes de modificações"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{motivo}_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Criar diretório do backup
            os.makedirs(backup_path, exist_ok=True)
            
            # Arquivos importantes para backup
            arquivos_importantes = [
                "app.py",
                "main.py", 
                "cortes/cortar_video.py",
                "templates/index.html",
                "vozes_clonadas.json",
                "config.json"
            ]
            
            arquivos_backupados = []
            
            for arquivo in arquivos_importantes:
                if os.path.exists(arquivo):
                    # Manter estrutura de diretórios
                    dest_path = os.path.join(backup_path, arquivo)
                    dest_dir = os.path.dirname(dest_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    
                    shutil.copy2(arquivo, dest_path)
                    arquivos_backupados.append(arquivo)
            
            # Criar arquivo de metadados do backup
            metadata = {
                "timestamp": timestamp,
                "motivo": motivo,
                "arquivos_backupados": arquivos_backupados,
                "tamanho_total": self.calcular_tamanho_backup(backup_path)
            }
            
            with open(os.path.join(backup_path, "backup_metadata.json"), "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Backup criado: {backup_name}")
            print(f"📁 Local: {backup_path}")
            print(f"📊 Arquivos: {len(arquivos_backupados)}")
            
            return backup_path
            
        except Exception as e:
            print(f"❌ Erro ao criar backup: {e}")
            return None
    
    def calcular_tamanho_backup(self, backup_path):
        """Calcula tamanho total do backup"""
        total_size = 0
        for root, dirs, files in os.walk(backup_path):
            for file in files:
                file_path = os.path.join(root, file)
                total_size += os.path.getsize(file_path)
        return total_size
    
    def listar_backups(self):
        """Lista todos os backups disponíveis"""
        if not os.path.exists(self.backup_dir):
            return []
        
        backups = []
        for item in os.listdir(self.backup_dir):
            backup_path = os.path.join(self.backup_dir, item)
            if os.path.isdir(backup_path):
                metadata_file = os.path.join(backup_path, "backup_metadata.json")
                if os.path.exists(metadata_file):
                    try:
                        with open(metadata_file, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                        backups.append({
                            "nome": item,
                            "caminho": backup_path,
                            "metadata": metadata
                        })
                    except:
                        backups.append({
                            "nome": item,
                            "caminho": backup_path,
                            "metadata": {"timestamp": "desconhecido"}
                        })
        
        return sorted(backups, key=lambda x: x["metadata"].get("timestamp", ""), reverse=True)
    
    def restaurar_backup(self, backup_name):
        """Restaura backup específico"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if not os.path.exists(backup_path):
                print(f"❌ Backup não encontrado: {backup_name}")
                return False
            
            # Ler metadados
            metadata_file = os.path.join(backup_path, "backup_metadata.json")
            if os.path.exists(metadata_file):
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                
                print(f"🔄 Restaurando backup: {backup_name}")
                print(f"📅 Data: {metadata.get('timestamp', 'desconhecida')}")
                print(f"📝 Motivo: {metadata.get('motivo', 'desconhecido')}")
                
                # Restaurar arquivos
                arquivos_restaurados = 0
                for arquivo in metadata.get("arquivos_backupados", []):
                    src_path = os.path.join(backup_path, arquivo)
                    if os.path.exists(src_path):
                        # Criar diretório de destino se necessário
                        dest_dir = os.path.dirname(arquivo)
                        if dest_dir:
                            os.makedirs(dest_dir, exist_ok=True)
                        
                        shutil.copy2(src_path, arquivo)
                        arquivos_restaurados += 1
                
                print(f"✅ Backup restaurado: {arquivos_restaurados} arquivos")
                return True
            else:
                print(f"❌ Metadados do backup não encontrados")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao restaurar backup: {e}")
            return False
    
    def limpar_backups_antigos(self, manter_ultimos=5):
        """Remove backups antigos, mantendo apenas os mais recentes"""
        try:
            backups = self.listar_backups()
            if len(backups) <= manter_ultimos:
                print(f"📊 Total de backups: {len(backups)} (dentro do limite de {manter_ultimos})")
                return
            
            # Remover backups antigos
            backups_para_remover = backups[manter_ultimos:]
            for backup in backups_para_remover:
                backup_path = backup["caminho"]
                shutil.rmtree(backup_path)
                print(f"🗑️ Backup removido: {backup['nome']}")
            
            print(f"✅ Limpeza concluída: {len(backups_para_remover)} backups removidos")
            
        except Exception as e:
            print(f"❌ Erro na limpeza: {e}")
    
    def status_backups(self):
        """Mostra status dos backups"""
        backups = self.listar_backups()
        
        print("📊 STATUS DOS BACKUPS")
        print("=" * 50)
        print(f"📁 Diretório: {self.backup_dir}")
        print(f"📊 Total de backups: {len(backups)}")
        
        if backups:
            print("\n📋 BACKUPS DISPONÍVEIS:")
            for i, backup in enumerate(backups[:5], 1):  # Mostrar apenas os 5 mais recentes
                metadata = backup["metadata"]
                timestamp = metadata.get("timestamp", "desconhecido")
                motivo = metadata.get("motivo", "desconhecido")
                arquivos = len(metadata.get("arquivos_backupados", []))
                tamanho = metadata.get("tamanho_total", 0)
                
                print(f"  {i}. {backup['nome']}")
                print(f"     📅 {timestamp} | 📝 {motivo} | 📊 {arquivos} arquivos | 💾 {tamanho/1024:.1f}KB")
        else:
            print("❌ Nenhum backup encontrado")

def main():
    """Função principal para uso via linha de comando"""
    import sys
    
    backup_system = BackupAutomatico()
    
    if len(sys.argv) < 2:
        print("Uso: python backup_automatico.py [comando]")
        print("Comandos:")
        print("  criar [motivo]  - Cria backup automático")
        print("  listar          - Lista backups disponíveis")
        print("  restaurar [nome] - Restaura backup específico")
        print("  limpar          - Remove backups antigos")
        print("  status          - Mostra status dos backups")
        return
    
    comando = sys.argv[1].lower()
    
    if comando == "criar":
        motivo = sys.argv[2] if len(sys.argv) > 2 else "manual"
        backup_system.criar_backup_antes_modificacao(motivo=motivo)
    
    elif comando == "listar":
        backups = backup_system.listar_backups()
        for backup in backups:
            print(f"📁 {backup['nome']}")
    
    elif comando == "restaurar":
        if len(sys.argv) < 3:
            print("❌ Especifique o nome do backup para restaurar")
            return
        backup_system.restaurar_backup(sys.argv[2])
    
    elif comando == "limpar":
        backup_system.limpar_backups_antigos()
    
    elif comando == "status":
        backup_system.status_backups()
    
    else:
        print(f"❌ Comando desconhecido: {comando}")

if __name__ == "__main__":
    main()
