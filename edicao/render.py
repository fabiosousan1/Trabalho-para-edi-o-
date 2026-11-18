"""Monta a edição a partir de plano.json, em três etapas nesta ordem:

1. Cortes: remove pausas longas (silêncio detectado no áudio), com margem de fala.
2. Visual: zoom periódico, flash em cada batida e os efeitos listados em
   "efeitos" (Impact frame, Dolly zoom, Rack focus, Voice note).
3. Legendas: queima o texto de legendas.srt por último. O SRT precisa estar
   no tempo do vídeo já editado (depois dos cortes).

Efeitos implementados em ffmpeg:
    Impact frame  -> flash branco + zoom rápido (usa a batida do flash)
    Dolly zoom    -> zoom gradual dentro da janela de tempo
    Rack focus    -> desfoque pulsado na janela (aproximação)
    Voice note    -> forma de onda do áudio sobre o vídeo na janela
Os demais efeitos do vídeo de referência (Live cursor, Post wall, Comment drop,
Press font etc.) dependem de animação de interface ou de texto e não entram aqui.

Uso:
    python render.py plano.json --dry-run   # só mostra os comandos ffmpeg
    python render.py plano.json             # renderiza saida/edicao_9x16.mp4

Requer ffmpeg com silencedetect, zoompan, eq, boxblur, showwaves e drawtext.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def ffprobe_duracao(caminho):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", caminho],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())


def detectar_silencios(caminho, limiar_db, minimo_s):
    """Devolve lista de (inicio, fim) das pausas detectadas no áudio."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", caminho,
         "-af", f"silencedetect=noise={limiar_db}dB:d={minimo_s}", "-f", "null", "-"],
        capture_output=True, text=True)
    inicios = [float(m) for m in re.findall(r"silence_start: ([\d.]+)", proc.stderr)]
    fins = [float(m) for m in re.findall(r"silence_end: ([\d.]+)", proc.stderr)]
    return list(zip(inicios, fins))


def intervalos_mantidos(dur, silencios, pausa_longa_s, margem_s):
    """Tira as pausas longas, deixando margem_s de cada lado da fala."""
    cortes = []
    for ini, fim in silencios:
        if fim - ini >= pausa_longa_s:
            cortes.append((ini + margem_s, fim - margem_s))
    mantidos, cursor = [], 0.0
    for ini, fim in cortes:
        if ini > cursor:
            mantidos.append((cursor, ini))
        cursor = fim
    if cursor < dur:
        mantidos.append((cursor, dur))
    return mantidos


def etapa_cortes(plano, fonte, dest, dur):
    c = plano["cortes"]
    silencios = detectar_silencios(fonte, c["limiar_db"], c["silencio_minimo_s"])
    mantidos = intervalos_mantidos(dur, silencios, c["pausa_longa_s"], c["margem_s"])
    n = len(mantidos)
    partes = []
    for i, (a, b) in enumerate(mantidos):
        partes.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}]")
        partes.append(f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}]")
    entradas = "".join(f"[v{i}][a{i}]" for i in range(n))
    partes.append(f"{entradas}concat=n={n}:v=1:a=1[vout][aout]")
    cmd = [
        "ffmpeg", "-y", "-i", fonte,
        "-filter_complex", ";".join(partes),
        "-map", "[vout]", "-map", "[aout]",
        "-r", str(plano["fps"]), "-c:v", "libx264", "-crf", "18", "-preset", "veryfast",
        "-pix_fmt", "yuv420p", "-c:a", "aac", dest,
    ]
    return cmd, mantidos


def pontos_zoom(plano, duracao_total):
    pontos, t = [], plano["zoom_inicio_segundos"]
    while t < duracao_total:
        pontos.append(t)
        t += plano["zoom_a_cada_segundos"]
    return pontos


def expressao_zoom(plano, duracao_total, efeitos):
    """Expressão do zoompan: pulsos periódicos (+ Impact frame) e Dolly zoom."""
    escala = plano["zoom_escala"] - 1
    meia = plano["zoom_duracao_segundos"] / 2
    fps = plano["fps"]
    pulsos = []
    for t in pontos_zoom(plano, duracao_total):
        pulsos.append(f"max(0,1-abs(on/{fps}-{t + meia:.3f})/{meia:.3f})")
    for e in efeitos:
        if e["nome"] == "Impact frame":
            m = e["inicio"] + 0.1
            pulsos.append(f"max(0,1-abs(on/{fps}-{m:.3f})/0.25)")
    termos = [f"{escala:.3f}*min(1,{'+'.join(pulsos)})"] if pulsos else []
    for e in efeitos:
        if e["nome"] == "Dolly zoom":
            a, b = e["inicio"], e["fim"]
            termos.append(f"{e.get('zoom_extra', 0.18)}*between(on/{fps},{a},{b})*(on/{fps}-{a})/{b - a:.3f}")
    return "1" + "".join(f"+{t}" for t in termos)


def etapa_visual(plano, origem, dest, dur):
    w, h = plano["resolucao"]
    fps = plano["fps"]
    efeitos = plano.get("efeitos", [])

    base = [f"zoompan=z='{expressao_zoom(plano, dur, efeitos)}':"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s={w}x{h}:fps={fps}"]
    fl = plano["flash"]
    if fl["ativo"]:
        for t in pontos_zoom(plano, dur):
            base.append(f"eq=brightness={fl['brilho']}:"
                        f"enable='between(t,{t:.3f},{t + fl['duracao_s']:.3f})'")
    for e in efeitos:
        if e["nome"] == "Impact frame":
            base.append(f"eq=brightness={fl['brilho'] + 0.1}:"
                        f"enable='between(t,{e['inicio']:.3f},{e['inicio'] + 0.12:.3f})'")
    partes = [f"[0:v]{','.join(base)}[v0]"]
    rotulo, n = "v0", 0

    for e in efeitos:
        if e["nome"] == "Rack focus":
            n += 1
            novo = f"v{n}"
            partes.append(f"[{rotulo}]boxblur=luma_radius=6:luma_power=1:"
                          f"enable='between(t,{e['inicio']:.3f},{e['fim']:.3f})'[{novo}]")
            rotulo = novo

    voz = [e for e in efeitos if e["nome"] == "Voice note"]
    if voz:
        alt = h // 7
        cond = "+".join(f"between(t,{e['inicio']:.3f},{e['fim']:.3f})" for e in voz)
        partes.append("[0:a]asplit=2[aout][aw]")
        partes.append(f"[aw]showwaves=s={w}x{alt}:mode=cline:colors=0xFF8C2A:rate={fps}[wv]")
        partes.append(f"[{rotulo}][wv]overlay=0:{h - alt - 60}:enable='{cond}'[vout]")
        mapas = ["-map", "[vout]", "-map", "[aout]"]
    else:
        partes.append(f"[{rotulo}]null[vout]")
        mapas = ["-map", "[vout]", "-map", "0:a"]

    return [
        "ffmpeg", "-y", "-i", origem,
        "-filter_complex", ";".join(partes), *mapas,
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "aac", dest,
    ]


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


def etapa_legendas(plano, origem, cues, pasta_textos, dest):
    leg = plano["legenda"]
    os.makedirs(pasta_textos, exist_ok=True)
    filtros = []
    for i, (ini, fim, texto) in enumerate(cues):
        caminho = os.path.join(pasta_textos, f"legenda_{i:03d}.txt")
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(texto)
        filtros.append(
            "drawtext=textfile='{}':expansion=none:fontsize={}:fontcolor={}:x=(w-text_w)/2:y={}"
            ":box={}:boxcolor={}:boxborderw=18:enable='between(t,{:.2f},{:.2f})'".format(
                caminho.replace("\\", "/").replace(":", "\\:"), leg["fonte_tamanho"], leg["cor"],
                leg["posicao_y"], 1 if leg["fundo_caixa"] else 0, leg["cor_caixa"], ini, fim))
    return [
        "ffmpeg", "-y", "-i", origem,
        "-vf", ",".join(filtros + ["format=yuv420p"]),
        "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p",
        "-c:a", "copy", dest,
    ]


def executar(cmd, dest_final):
    """Renderiza em arquivo temporário e só renomeia se o ffmpeg terminar com sucesso."""
    tmp = dest_final + ".tmp.mp4"
    cmd = cmd[:-1] + [tmp]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.replace(tmp, dest_final)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plano")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    plano = json.load(open(os.path.join(HERE, args.plano), encoding="utf-8"))
    fonte = os.path.join(HERE, plano["fonte"])
    if not os.path.exists(fonte):
        sys.exit(f"Vídeo de origem não encontrado: {fonte}")

    dur = ffprobe_duracao(fonte)
    saida = os.path.join(HERE, plano["saida"])
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    cues = ler_srt(os.path.join(HERE, plano["legendas_srt"]))
    pasta_tmp = tempfile.mkdtemp(prefix="edicao_")
    cortes_mp4 = os.path.join(pasta_tmp, "cortes.mp4")
    visual_mp4 = os.path.join(pasta_tmp, "visual.mp4")

    cmd1, mantidos = etapa_cortes(plano, fonte, cortes_mp4, dur)
    cmd2 = etapa_visual(plano, cortes_mp4, visual_mp4, sum(b - a for a, b in mantidos))
    comandos = [("cortes", cmd1), ("visual", cmd2)]
    if cues:
        comandos.append(("legendas", etapa_legendas(
            plano, visual_mp4, cues, os.path.join(pasta_tmp, "textos"), saida)))
    else:
        print("Sem legendas.srt: a etapa de legendas foi pulada.")

    for nome, cmd in comandos:
        print(f"# {nome}\n" + " ".join(f"'{c}'" if " " in c else c for c in cmd)[:2000])
    if args.dry_run:
        return
    executar(cmd1, cortes_mp4)
    executar(cmd2, visual_mp4)
    if cues:
        executar(comandos[-1][1], saida)
    else:
        os.replace(visual_mp4, saida)
    print("Pronto:", saida)


if __name__ == "__main__":
    main()
