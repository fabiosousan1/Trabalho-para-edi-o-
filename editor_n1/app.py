import json
import math
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import gradio as gr
from faster_whisper import WhisperModel
from cinematic_plan import plan as cinematic_plan

MODEL = None


def run(*args):
    p = subprocess.run(list(map(str, args)), capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-2500:])
    return p.stdout


def probe_duration(path):
    return float(run("ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "default=noprint_wrappers=1:nokey=1", path).strip())


def speech_segments(audio):
    global MODEL
    if MODEL is None:
        MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = MODEL.transcribe(str(audio), language="pt", vad_filter=True,
                                    word_timestamps=True, beam_size=3)
    return list(segments)


def ass_time(sec):
    sec = max(0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def ass_escape(txt):
    return re.sub(r"[{}\\]", "", txt).replace("\n", " ").strip()


def edit(video, music, broll, intensity, music_volume, cinematic):
    if not video:
        raise gr.Error("Envie um vídeo MP4 primeiro.")
    with tempfile.TemporaryDirectory(prefix="editor_n1_") as tmp:
        root = Path(tmp)
        original = root / "input.mp4"
        shutil.copy2(video, original)
        duration = probe_duration(original)
        if duration > 600:
            raise gr.Error("Nesta versão, use vídeos de até 10 minutos.")
        audio = root / "voice.wav"
        run("ffmpeg", "-y", "-i", original, "-vn", "-ac", "1", "-ar", "16000", audio)
        segments = speech_segments(audio)
        if not segments:
            raise gr.Error("Não encontrei fala suficiente para editar.")

        # Preserve short natural pauses; remove longer dead air.
        gap = {"suave": 0.9, "equilibrado": 0.55, "dinamico": 0.3}[intensity]
        ranges = []
        for seg in segments:
            a, b = max(0, seg.start - 0.12), min(duration, seg.end + 0.16)
            if ranges and a - ranges[-1][1] <= gap:
                ranges[-1] = (ranges[-1][0], max(b, ranges[-1][1]))
            else:
                ranges.append((a, b))
        parts = []
        for i, (a, b) in enumerate(ranges):
            part = root / f"part_{i:03d}.mp4"
            run("ffmpeg", "-y", "-ss", f"{a:.3f}", "-to", f"{b:.3f}",
                "-i", original, "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,eq=contrast=1.035:saturation=1.06",
                "-af", "highpass=f=85,lowpass=f=12500,acompressor=threshold=-18dB:ratio=2.5:attack=10:release=160,alimiter=limit=0.89",
                "-r", "30", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "23", "-c:a", "aac", "-ar", "48000", "-ac", "2", part)
            parts.append(part)
        concat = root / "parts.txt"
        concat.write_text("".join("file '" + str(p) + "'\n" for p in parts), encoding="utf-8")
        joined = root / "joined.mp4"
        run("ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", concat,
            "-c", "copy", joined)

        def remap(t):
            elapsed = 0
            for a, b in ranges:
                if t < a:
                    return elapsed
                if t <= b:
                    return elapsed + t - a
                elapsed += b - a
            return elapsed

        # Convert transcript times into the edited timeline before planning scenes.
        scene_segments = []
        for seg in segments:
            a, b = remap(seg.start), remap(seg.end)
            if b > a:
                scene_segments.append({"start": a, "end": b, "text": seg.text})
        scene_plan = cinematic_plan(scene_segments)

        subs = root / "captions.ass"
        header = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: N1,Arial,54,&H00FFFFFF,&H0000FFFF,&H00101010,&H88000000,1,0,0,0,100,100,0,0,1,3,1,2,70,70,230,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        events = []
        for seg in segments:
            words = [w for w in (seg.words or []) if w.word.strip()]
            if words:
                for k in range(0, len(words), 5):
                    group = words[k:k+5]
                    a, b = remap(group[0].start), remap(group[-1].end)
                    if b > a:
                        events.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},N1,,0,0,0,,{ass_escape(' '.join(w.word.strip() for w in group))}")
            else:
                a, b = remap(seg.start), remap(seg.end)
                if b > a:
                    events.append(f"Dialogue: 0,{ass_time(a)},{ass_time(b)},N1,,0,0,0,,{ass_escape(seg.text)}")
        subs.write_text(header + "\n".join(events) + "\n", encoding="utf-8")

        subtitled = root / "subtitled.mp4"
        run("ffmpeg", "-y", "-i", joined, "-vf", f"ass={subs}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
            "-c:a", "copy", subtitled)

        # Optional user-supplied licensed B-roll, placed as a short visual insert.
        visual = subtitled
        # Cinematic mode currently adjusts pacing and tonal treatment; scene recommendations are reviewed separately.
        if broll:
            clip = root / "broll.mp4"
            run("ffmpeg", "-y", "-stream_loop", "-1", "-i", broll,
                "-t", "2", "-an", "-vf",
                "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30",
                "-c:v", "libx264", "-preset", "veryfast", clip)
            # Overlay B-roll while preserving original narration.
            overlaid = root / "overlaid.mp4"
            run("ffmpeg", "-y", "-i", subtitled, "-i", clip,
                "-filter_complex", "[0:v][1:v]overlay=enable='between(t,2,4)':eof_action=pass[v]",
                "-map", "[v]", "-map", "0:a", "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "23", "-c:a", "copy", overlaid)
            visual = overlaid

        out = Path(tempfile.mkstemp(suffix="_magnetico_n1.mp4")[1])
        if music:
            run("ffmpeg", "-y", "-i", visual, "-stream_loop", "-1", "-i", music,
                "-filter_complex",
                f"[1:a]volume={float(music_volume):.2f}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2,alimiter=limit=0.89[m]",
                "-map", "0:v", "-map", "[m]", "-c:v", "copy", "-c:a", "aac",
                "-b:a", "192k", "-shortest", out)
        else:
            shutil.copy2(visual, out)
        transcript = " ".join(s.text.strip() for s in segments)
        report = {
            "duracao_original_segundos": round(duration, 1),
            "duracao_editada_segundos": round(probe_duration(out), 1),
            "trechos_mantidos": len(ranges),
            "legendas": len(events),
            "musica": bool(music),
            "imagem_apoio": bool(broll),
            "modo_cinematografico": bool(cinematic),
            "plano_cenas": scene_plan,
            "observacao": "Cortes automáticos por fala, não revisão semântica humana."
        }
        return str(out), transcript, scene_plan, json.dumps(report, ensure_ascii=False, indent=2)


MOBILE_CSS = """
.gradio-container {max-width: 920px !important; margin: auto !important; padding: 12px !important;}
@media (max-width: 650px) {
  .gradio-container {padding: 8px !important;}
  button {min-height: 52px !important; font-size: 17px !important;}
  .wrap {gap: 12px !important;}
}
"""
with gr.Blocks(title="Editor Magnético N1", css=MOBILE_CSS) as app:
    gr.Markdown("# Editor Magnético N1\nEnvie um vídeo e gere uma primeira edição automática. Use somente trilhas e imagens que você pode publicar.")
    video = gr.Video(label="Vídeo original", sources=["upload"], format="mp4")
    music = gr.Audio(label="Trilha sonora licenciada (opcional)", type="filepath")
    broll = gr.Video(label="Cena de apoio licenciada (opcional)", sources=["upload"])
    intensity = gr.Dropdown(["suave", "equilibrado", "dinamico"], value="equilibrado", label="Ritmo dos cortes")
    volume = gr.Slider(0.03, 0.25, value=0.10, step=0.01, label="Volume da trilha")
    cinematic = gr.Checkbox(value=True, label="Planejar cenas com emoção (cinematográfico)")
    gr.Markdown("**Como funciona:** o plano emocional sugere cenas e trilhas para revisão. Nesta versão, as sugestões ainda não geram imagens ou músicas automaticamente.")
    go = gr.Button("Criar edição e plano cinematográfico", variant="primary")
    result = gr.Video(label="MP4 final")
    transcript = gr.Textbox(label="Transcrição", lines=6)
    scenes = gr.JSON(label="Plano de cenas sugerido pela IA local")
    report = gr.Code(label="Relatório da edição", language="json")
    go.click(edit, [video, music, broll, intensity, volume, cinematic], [result, transcript, scenes, report])

if __name__ == "__main__":
    app.queue(default_concurrency_limit=1).launch(server_name="127.0.0.1")
