#!/usr/bin/env python3
"""
Instala PyTorch com suporte CUDA para ativar a GPU
"""

def install_pytorch_cuda():
    """Instala PyTorch com suporte CUDA"""
    
    print("🔧 [CUDA] Verificando CUDA disponível...")
    
    # Verificar se CUDA está disponível no sistema
    import subprocess
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ [CUDA] NVIDIA GPU detectada!")
            print("📊 [CUDA] Informações da GPU:")
            print(result.stdout)
        else:
            print("❌ [CUDA] NVIDIA GPU não detectada!")
            print("💡 [CUDA] Instale drivers NVIDIA primeiro")
            return False
    except FileNotFoundError:
        print("❌ [CUDA] nvidia-smi não encontrado!")
        print("💡 [CUDA] Instale drivers NVIDIA primeiro")
        return False
    
    print("\n🔧 [CUDA] Instalando PyTorch com suporte CUDA...")
    print("⚠️ [CUDA] Isso pode demorar alguns minutos...")
    
    # Comando para instalar PyTorch com CUDA
    cmd = [
        "pip", "uninstall", "torch", "torchvision", "torchaudio", "-y"
    ]
    
    print(f"🔄 [CUDA] Executando: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"📊 [CUDA] Uninstall result: {result.returncode}")
    
    # Instalar PyTorch com CUDA 11.8 (compatível com a maioria das GPUs)
    cmd_install = [
        "pip", "install", 
        "torch", "torchvision", "torchaudio", 
        "--index-url", "https://download.pytorch.org/whl/cu118"
    ]
    
    print(f"🔄 [CUDA] Executando: {' '.join(cmd_install)}")
    result = subprocess.run(cmd_install, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ [CUDA] PyTorch com CUDA instalado com sucesso!")
        
        # Testar CUDA
        print("\n🧪 [CUDA] Testando CUDA...")
        test_cmd = [
            "python", "-c", 
            "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available()); print('CUDA version:', torch.version.cuda if torch.cuda.is_available() else 'N/A')"
        ]
        
        result = subprocess.run(test_cmd, capture_output=True, text=True)
        print("📊 [CUDA] Resultado do teste:")
        print(result.stdout)
        
        if "CUDA available: True" in result.stdout:
            print("🎉 [CUDA] GPU ATIVADA COM SUCESSO!")
            return True
        else:
            print("❌ [CUDA] GPU ainda não ativada")
            return False
    else:
        print(f"❌ [CUDA] Erro na instalação: {result.stderr}")
        return False

if __name__ == "__main__":
    install_pytorch_cuda()
