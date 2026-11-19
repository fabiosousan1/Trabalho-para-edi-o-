# Editor Magnético N1, versão inicial

## O que faz
Recebe um vídeo com voz em português, transcreve com Faster-Whisper local, identifica trechos falados, remove pausas longas, aplica tratamento básico de imagem e voz, gera legendas ASS e exporta MP4 1080x1920. Permite música de fundo e uma cena de apoio fornecidas pelo usuário.

## Instalação (Windows, macOS ou Linux)
Instale Python 3.11+ e FFmpeg com ffmpeg e ffprobe disponíveis no PATH.

```bash
cd editor_n1
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:7860. A primeira transcrição baixa o modelo base. O processamento roda no seu computador e pode ser demorado sem GPU.

## Limitações
Esta versão não compreende o roteiro para escolher cenas nem gera personagens ou imagens por IA. A cena de apoio é enviada pelo usuário e aparece entre 2 e 4 segundos, sem sincronização semântica. Não há geração automática de trilha, efeitos especiais avançados, detecção de erros de fala ou revisão humana dos cortes. A edição de silêncio pode cortar uma fala em casos difíceis. Recomenda-se revisar o resultado antes de publicar.

Não use música, imagens ou vozes de terceiros sem autorização. Não hospede publicamente sem autenticação, limites de tamanho e isolamento do processamento.
