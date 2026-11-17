"""Consulta metadados públicos de um vídeo do YouTube sem baixar o vídeo."""
import json
import sys
import urllib.parse
import urllib.request

def analisar(url):
    endpoint = "https://www.youtube.com/oembed?" + urllib.parse.urlencode({"url": url, "format": "json"})
    request = urllib.request.Request(endpoint, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://www.youtube.com/shorts/kveX-g95sgg"
    try:
        dados = analisar(url)
        print(json.dumps({"url": url, "titulo": dados.get("title"), "canal": dados.get("author_name"), "thumbnail": dados.get("thumbnail_url")}, ensure_ascii=False, indent=2))
    except Exception as exc:
        print("Não foi possível consultar os dados públicos:", exc)
        sys.exit(1)
