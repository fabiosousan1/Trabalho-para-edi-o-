# Editor Magnético N1, integrações cinematográficas

## Estado real
O editor local existente permanece como protótipo. Esta branch adiciona um **planejador de cenas** e um **adaptador opcional de busca Pexels**. Nenhuma integração com Runway ou ElevenLabs está autenticada, nem há geração automática de imagens, trilhas ou efeitos cinematográficos por esses serviços.

## Fluxo planejado
1. Upload do vídeo em interface web para celular.
2. Faster-Whisper transcreve e fornece tempos da fala.
3. `cinematic_plan.py` sugere humor, trilha, tipo de imagem e efeito para cada segmento. A classificação é heurística e precisa de revisão.
4. `providers.py` pode consultar vídeos de apoio no Pexels se uma chave de API estiver configurada no servidor. Não baixa vídeos automaticamente.
5. FFmpeg poderá combinar as cenas aprovadas com a fala original e renderizar MP4.

## Teste do planejador
```bash
cd editor_n1
echo '[{"start":0,"end":4,"text":"Você pode recomeçar hoje"},{"start":4,"end":8,"text":"Esse erro pode ensinar muito"}]' > segments.json
python cinematic_plan.py segments.json
```

## Segurança e direitos
Não coloque chaves de API no GitHub nem no código do navegador. Use variáveis de ambiente no servidor. Confira direitos de imagem, música e termos de licença de cada material antes de publicar. Evite clonar voz ou imagem de celebridades sem autorização.

## Próximas tarefas
- Expor o planejador na interface Gradio.
- Implementar download seguro de vídeos aprovados do Pexels e sincronização por segmento.
- Adicionar biblioteca de trilhas próprias e ajuste automático de volume.
- Criar testes com vídeos reais, limites de tamanho, autenticação e fila.
- Hospedar o processamento num servidor com FFmpeg. GitHub Pages sozinho não executa Python nem FFmpeg.
