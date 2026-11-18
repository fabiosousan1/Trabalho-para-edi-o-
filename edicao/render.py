"""Monta a edição a partir de plano.json: zoom rápido periódico e legendas de legendas.srt.

Uso:
    python render.py plano.json --dry-run   # só mostra o comando ffmpeg
    python render.py plano.json             # renderiza saida/edicao_9x16.mp4

Requer ffmpeg com os filtros zoompan e drawtext.
"""
import argparse
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def ler_srt(caminho):
    """Lê um .srt simples e devolve lista de (inicio, fim, texto)."""
    if not os.path.exists(caminho):
        return []
    blocos = re.split(r"\n\s*\n", open(caminho, encoding="utf-8").read().strip())
    cues = []
    for bloco in blocos:
        linhas = bloco.strip().splitlines()
        for i, linha in enumerate(linhas):
            m = re.match(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)", linha)
            if m:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, m.groups())
                ini = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
                fim = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
                texto = " ".join(linhas[i + 1:]).strip()
                if texto:
                    cues.append((ini, fim, texto))
                break
    return cues


def gravar_textos(cues, pasta):
    """Grava cada legenda em um arquivo: drawtext lê de arquivo, sem escapes de texto."""
    os.makedirs(pasta, exist_ok=True)
    caminhos = []
    for i, (_, _, texto) in enumerate(cues):
        caminho = os.path.join(pasta, f"legenda_{i:03d}.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        caminhos.append(caminho)
    return caminhos


def expressao_zoom(plano, duracao_total):
    """Expressão do zoompan: soma de pulsos triangulares, um a cada intervalo."""
    escala = plano["zoom_escala"] - 1
    meia = plano["zoom_duracao_segundos"] / 2
    fps = plano["fps"]
    termos = []
    t = plano["zoom_inicio_segundos"]
    while t < duracao_total:
        termos.append(f"max(0,1-abs(on/{fps}-{t + meia:.3f})/{meia:.3f})")
        t += plano["zoom_a_cada_segundos"]
    if not termos:
        return "1"
    return f"1+{escala:.3f}*min(1,{'+'.join(termos)})"


def montar_comando(plano, duracao_total, cues, saida, pasta_textos):
    w, h = plano["resolucao"]
    fps = plano["fps"]
    z = expressao_zoom(plano, duracao_total)
    filtros = [
        f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps={fps}",
        "format=yuv420p",
    ]
    leg = plano["legenda"]
    caminhos = gravar_textos(cues, pasta_textos)
    for (ini, fim, _), caminho in zip(cues, caminhos):
        filtros.append(
            "drawtext=textfile='{}':expansion=none:fontsize={}:fontcolor={}:x=(w-text_w)/2:y={}"
            ":box={}:boxcolor={}:boxborderw=18:enable='between(t,{:.2f},{:.2f})'".format(
                caminho.replace("\\", "/").replace(":", "\\:"), leg["fonte_tamanho"], leg["cor"],
                leg["posicao_y"], 1 if leg["fundo_caixa"] else 0, leg["cor_caixa"], ini, fim)
        )
    return [
        "ffmpeg", "-y", "-i", os.path.join(HERE, plano["fonte"]),
        "-vf", ",".join(filtros),
        "-r", str(fps), "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-c:a", "copy", saida,
    ]


def duracao_do_video(caminho):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", caminho],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plano")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plano = json.load(open(os.path.join(HERE, args.plano), encoding="utf-8"))
    fonte = os.path.join(HERE, plano["fonte"])
    if not os.path.exists(fonte):
        sys.exit(f"Vídeo de origem não encontrado: {fonte}")

    dur = duracao_do_video(fonte)
    cues = ler_srt(os.path.join(HERE, plano["legendas_srt"]))
    saida = os.path.join(HERE, plano["saida"])
    os.makedirs(os.path.dirname(saida), exist_ok=True)

    pasta_textos = os.path.join(os.path.dirname(saida), "textos")
    cmd = montar_comando(plano, dur, cues, saida, pasta_textos)
    print(" ".join(f"'{c}'" if " " in c or "(" in c else c for c in cmd))
    if args.dry_run:
        return
    # Renderiza em arquivo temporário e só renomeia se o ffmpeg terminar com sucesso.
    tmp = saida + ".tmp.mp4"
    cmd[-1] = tmp
    subprocess.run(cmd, check=True)
    os.replace(tmp, saida)
    print("Pronto:", saida)


if __name__ == "__main__":
    main()
