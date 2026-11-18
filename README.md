# Editor Magnético N1

Primeira versão de edição automática de vídeos, preservando o editor HTML experimental já existente em `index.html`.

## O que faz

- Upload de MP4, MOV, MKV ou WebM (até 200 MB e 3 minutos)
- Detecção de pausas longas com FFmpeg e remoção opcional
- Transcrição em português com faster-whisper, incluindo tempos por palavra
- Legendas ASS sobre o vídeo
- Conversão para vídeo vertical 1080 x 1920 com áudio AAC e MP4 H.264
- Download do resultado e leitura da transcrição

## Como executar

É necessário Docker instalado. Na raiz do repositório:

```bash
docker build -t editor-magnetico-n1 .
docker run --rm -p 8000:8000 editor-magnetico-n1
```

Acesse http://localhost:8000 no navegador. A primeira edição pode demorar enquanto o modelo de transcrição é baixado. O servidor precisa de internet na primeira execução.

Alternativa local: instale FFmpeg no sistema, rode `pip install -r requirements.txt` e `uvicorn server:app --reload`.

## Atenção

GitHub Pages hospeda páginas estáticas, mas não executa Python, FFmpeg ou Whisper. Para edição real, é necessário hospedar o backend em um servidor ou executar localmente. O upload é enviado ao servidor configurado e os vídeos ficam na pasta `jobs/`. Não exponha publicamente sem autenticação, limpeza automática dos arquivos, limites de uso e proteção contra abuso. Esta versão processa as tarefas na própria requisição, sem fila, e não deve ser usada em produção sem melhorias.

## Próximas etapas

Testes com vídeos reais; correções de sincronização; fila de processamento; autenticação; limpeza de arquivos; visualização de progresso; animações de legenda, zoom e efeitos visuais de referência.
