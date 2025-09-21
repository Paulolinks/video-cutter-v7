1) Princípios

Evoluir sem medo: remover/alterar é permitido se houver equivalência comprovada por testes.

Sync é contrato: dublagem deve respeitar a duração original (p95 do erro ≤ 40 ms por bloco).

Compatibilidade previsível: versões travadas por ambiente; atualizações passam pela matriz de CI.

2) Quando PODE remover/reescrever

Existe RFC curta (até 1 página) dizendo por quê e qual benefício.

Há testes de não-regressão (unit + integração + E2E curta) passando.

Há feature flag com fallback para o caminho antigo.

Canary validado com 1–2 vídeos reais.

Isto substitui a política rígida anterior “NUNCA remover”, que gerava dívida técnica e conflitos.

3) Gates de compatibilidade (bloqueiam merge)

PR falha se:

qualquer job da matriz (ex.: env-tts com Torch/XTTS) falhar;

p95 do erro de sync > 40 ms;

sample rates inconsistentes (ex.: TTS ≠ 24k antes do resample);

artefatos (áudio) não anexados ao PR.

4) Torch/XTTS e backends de TTS/ASR

Alterar Torch/torchaudio/XTTS somente via COMPATIBILITY_MATRIX.md + PR Renovate.

Se houver incompatibilidade (ex.: Torch 2.8 + XTTS), a CI de matriz impede merge; mantenha o par estável no env-tts até haver wheel compatível.

Novos backends (OpenVoice, etc.) entram via TTSAdapter e flag, com testes equivalentes.

5) Contratos de dados e áudio

Timestamps sempre em segundos (float), com start <= end, precisão 3 casas decimais.

TTSSegment deve incluir target_dur e wav_path existente, sr coerente.

Resample: único ponto na pipeline (evitar múltiplos resamples).

6) Qualidade mínima (SLOs)

Sync: p95 ≤ 40 ms; média ≤ 20 ms.

Áudio: pico ≤ -1 dBFS; LUFS de voz -23 a -14; sem clipping.

Render: nenhum pop/click entre blocos (crossfade min. 10–20 ms).

7) Observabilidade (obrigatório em PR)

JSON de métricas por bloco: {target_dur, tts_dur, rate, sr_in, sr_out, backend}.

Log de mix (ganhos, ducking aplicado).

2 artefatos WAV: antes (TTS bruto) e depois (ajustado).

8) Segurança & segredos

Chaves/API via .env e secret manager; nunca em repositório.

Áudios de voz do usuário ficam em storage com controle de acesso.

9) Processo de PR

Template exige: objetivo, risco, diff de deps, resultado dos testes, links para artefatos de áudio, e se há mudança na matriz.

Revisão por 1 pessoa (mínimo) + aprovação automática do bot da matriz.

10) Release & rollback

Canary obrigatório para alterações de ASR/TTS/time-stretch.

Rollback documentado e testado (feature flag + versão anterior disponível).