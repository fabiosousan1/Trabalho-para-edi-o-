# Edição: vídeo com referência de estilo

Edição de um vídeo vertical (478x850, ~96 s) seguindo o estilo do vídeo de referência (720x1280, ~26 s).

## Estilo observado na referência
- Legendas curtas em caixa escura, aparecendo em blocos rápidos.
- Textos de destaque em laranja e em caixa, entrando sobre o rosto.
- Zoom rápido (punch-in) em momentos de ênfase.
- Efeitos de impacto (ex.: quadro de linhas radiais com a palavra "IMPACTO") e ondas de áudio em laranja.
- Painel de lista de efeitos no topo como elemento visual recorrente.

## O que já está pronto
- `plano.json`: parâmetros da edição (zoom a cada 6 s, legenda em caixa, 9:16, 30 fps).
- `render.py`: lê o plano, aplica zoom periódico e grava as legendas de `legendas.srt`.

## Como usar
1. Coloque os vídeos em `../videos/` (relativo a esta pasta), com os nomes definidos em `plano.json`. Não são versionados aqui por tamanho.
2. Crie `legendas.srt` com a transcrição do vídeo principal. Sem ele, o render sai sem legendas.
3. Confira o comando sem renderizar: `python render.py plano.json --dry-run`
4. Renderize: `python render.py plano.json` (saída em `saida/edicao_9x16.mp4`).

## Pendente
- Transcrição para gerar as legendas reais (ainda não existe `legendas.srt`).
- Destaques em laranja, efeitos de impacto e painel de efeitos ainda não estão no plano.
- Cortes de pausas e ritmo: depende da transcrição.

## Efeitos no Remotion (`edicao/remotion/`)
Os 21 efeitos do painel do vídeo de referência estão em `remotion/src/effects.tsx`, com a linha do tempo em `remotion/src/timeline.ts`.
A base é o vídeo já cortado (`remotion/public/base.mp4`, gerado pela etapa de cortes do `render.py`; não é versionado).

Passos:
1. `cd edicao/remotion && npm install`
2. Gerar a base: rodar a etapa de cortes do `render.py` e copiar o resultado para `remotion/public/base.mp4`.
3. Render: `npx remotion render src/index.ts Edicao <saida.mp4> --browser-executable=<caminho do chrome> --concurrency=2`

A legenda continua pendente: entra depois, com o `legendas.srt` no tempo do vídeo já cortado.
