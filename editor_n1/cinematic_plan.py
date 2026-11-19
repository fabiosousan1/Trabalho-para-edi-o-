"""Planejador local de cenas baseado na transcrição, sem serviços pagos."""
import json
import re
from dataclasses import asdict, dataclass


@dataclass
class Scene:
    start: float
    end: float
    narration: str
    mood: str
    music_query: str
    visual_query: str
    effect: str


MOODS = {
    "esperanca": ("esperança", "piano inspirador suave", "amanhecer luz dourada", "slow_zoom"),
    "desafio": ("desafio", "ambient suspense suave", "pessoa trabalhando pensativa", "subtle_push"),
    "conquista": ("conquista", "cinematic uplifting", "pessoa comemorando conquista", "soft_flash"),
    "ensino": ("ensino", "ambient minimalista", "pessoa ensinando com computador", "clean_cut"),
}


def classify(text):
    t = text.lower()
    if re.search(r"conquist|resultado|venc|consegui|sucesso", t):
        return "conquista"
    if re.search(r"difícil|erro|medo|problema|fracass|desist", t):
        return "desafio"
    if re.search(r"sonho|esperanç|recomeç|acredit|transform", t):
        return "esperanca"
    return "ensino"


def plan(segments):
    scenes = []
    for s in segments:
        text = str(s["text"]).strip()
        if not text:
            continue
        mood = classify(text)
        label, music, visual, effect = MOODS[mood]
        scenes.append(asdict(Scene(
            start=round(float(s["start"]), 2),
            end=round(float(s["end"]), 2),
            narration=text, mood=label, music_query=music,
            visual_query=visual, effect=effect
        )))
    return scenes


if __name__ == "__main__":
    import sys
    with open(sys.argv[1], encoding="utf-8") as f:
        segments = json.load(f)
    print(json.dumps(plan(segments), ensure_ascii=False, indent=2))
