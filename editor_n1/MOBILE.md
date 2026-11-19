# Uso pelo celular

A interface Gradio foi ajustada para telas estreitas. Isso **não** significa que o aplicativo esteja hospedado.

## Teste na mesma rede Wi-Fi
1. Instale Python, FFmpeg e dependências no notebook ou servidor.
2. Em `app.py`, altere `server_name="127.0.0.1"` para `server_name="0.0.0.0"` apenas se você confiar na rede local.
3. Execute `python app.py`.
4. No celular conectado ao mesmo Wi-Fi, abra `http://IP-DO-NOTEBOOK:7860`.
5. Caso não abra, confira o firewall do notebook.

**Atenção:** não exponha essa interface na internet sem autenticação, HTTPS, limites de upload e controle de recursos. Hospedagem pública e armazenamento de vídeos exigem configuração adicional.

## Situação da IA
O planejamento emocional agora aparece na interface depois de editar o vídeo. As sugestões são baseadas em palavras-chave, não em análise profunda de cenas. A trilha e o vídeo de apoio ainda são arquivos enviados manualmente. A busca Pexels existe como adaptador opcional, mas ainda não está ligada ao botão de edição.

## Testes
Dentro de `editor_n1`, execute `python -m unittest discover -s tests`. Teste também um vídeo real curto com FFmpeg instalado.
