"""Adaptadores opcionais. Não fazem chamadas pagas nem publicam arquivos sem configuração."""
import os
from pathlib import Path


def integrations():
    return {
        "ffmpeg": {"type": "local", "purpose": "cortes, composição e exportação"},
        "faster_whisper": {"type": "local", "purpose": "transcrição e legendas"},
        "pexels": {
            "type": "api_optional",
            "configured": bool(os.getenv("PEXELS_API_KEY")),
            "purpose": "buscar vídeos de apoio licenciados",
        },
        "runway": {
            "type": "future_paid_or_limited",
            "configured": False,
            "purpose": "gerar cenas com IA, requer integração oficial e créditos",
        },
        "elevenlabs": {
            "type": "future_paid_or_limited",
            "configured": False,
            "purpose": "efeitos sonoros gerados por IA",
        },
    }


def search_pexels(query, per_page=3):
    """Busca metadados, sem baixar nem usar material automaticamente."""
    import json
    import urllib.parse
    import urllib.request
    key = os.getenv("PEXELS_API_KEY")
    if not key:
        raise RuntimeError("Configure PEXELS_API_KEY no ambiente.")
    params = urllib.parse.urlencode({"query": query, "per_page": min(int(per_page), 10)})
    request = urllib.request.Request(
        "https://api.pexels.com/videos/search?" + params,
        headers={"Authorization": key, "User-Agent": "EditorMagneticoN1/1.0"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        data = json.load(response)
    return [{
        "id": v.get("id"), "url": v.get("url"),
        "duration": v.get("duration"), "user": v.get("user", {}).get("name"),
        "video_files": [{"link": f.get("link"), "quality": f.get("quality")}
                        for f in v.get("video_files", []) if f.get("link")]
    } for v in data.get("videos", [])]
