🎯 Objetivo

Garantir evolução rápida sem quebrar sincronismo de áudio/vídeo e sem engessar novas funções (ex.: TTS/XTTS, OpenVoice, novos ASR). Esta instrução define como trabalhar, não o que não pode.

✅ Antes de começar (checklist curto)

Criar branch: feat/*, fix/* ou exp/*.

Ativar ambiente correto:

env-asr (WhisperX/stable-ts)

env-tts (XTTS/OpenVoice)

env-core (web/app/FFmpeg)

Rodar testes: make test (unit + integração rápida).

Baixar assets de teste (goldens curtos) com make assets.

Observação: esta página substitui a verificação manual rígida anterior; o script de verificação continua existindo, mas os testes são a proteção principal.

🧩 Ambientes & Matriz de compatibilidade

Mantemos um arquivo: COMPATIBILITY_MATRIX.md (editável) com pares biblioteca ↔ versões ↔ CUDA.

Cada ambiente tem seu constraints/lock (ex.: constraints-tts.txt, constraints-asr.txt) e/ou Docker base (CUDA fixa).

Atualizações passam por CI de matriz (explicado nas regras críticas).

Exemplo (trecho):

[XTTS v2.1.x] -> torch==2.3.1, torchaudio==2.3.1, CUDA 12.1
[WhisperX 3.x] -> torch==2.2.2, torchaudio==2.2.2, CUDA 12.1

🏗️ Padrão de arquitetura (plugável, sem lock-in)

Adapters:

ASRAdapter: WhisperX | stable-ts | (outros)

TTSAdapter: XTTS | OpenVoice | (outros)

TimeStretchAdapter: FFmpeg atempo | RubberBand

Feature flags para ativar/desativar backends em tempo de execução.

Contracts simples (pydantic/dataclasses) para mensagens entre etapas:

WordTimestamp { start, end, text, speaker? }

TTSSegment { text, target_dur, wav_path, sr }

🧪 Pirâmide de testes (o que roda localmente)

Unit: parsers (timestamps, SRT), cálculo de atempo, SR, normalização de texto.

Integração: texto → TTS → stretch → mix (com goldens de 10–20s).

E2E curta: corta um vídeo curto e valida p95 do erro de sync.

Smoke (rápido): sobe adapters, checa versões e SR.

Comando único:

make test          # roda unit + integração
make test-e2e      # roda E2E curta com métricas

🎚️ Áudio & Vídeo (regras práticas)

Sempre installe e execute tudo no venv

SR padrão: síntese do TTS em 24 kHz → resample para 48 kHz antes de mixar com o vídeo.

Duração-alvo por bloco: usar timestamps da fala original; speed do TTS ≈ ajuste grosso; time-stretch (FFmpeg/RubberBand) faz o ajuste fino (±20 ms).

Mix: voz original atenuada/mutada; ducking de música quando há dublagem.

🚦Fluxo de entrega (dev → main)

PR com resultado dos testes + artefatos (áudio antes/depois, JSON de métricas).

Canary: publicar build interno; validar 1–2 vídeos reais.

Stable: marcar release; atualizar COMPATIBILITY_MATRIX.md se versões mudaram.

🧰 Dependências

Usar uv/Poetry ou pip-tools com constraints por ambiente.

Nunca instalar “no susto”: toda troca de versão deve gerar PR automático (Renovate) e passar na matriz do CI.

🩹 Rollback

Sempre manter fallback via feature flag para ASR/TTS/time-stretch.

Release com “problema” regride para o último canary/stable em 1 comando (make rollback).