import os, uuid, subprocess, json, re, shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from faster_whisper import WhisperModel

BASE=Path(__file__).resolve().parent
JOBS=BASE/"jobs"
JOBS.mkdir(exist_ok=True)
app=FastAPI(title="Editor Magnético N1")
model=None
def run(args):
    p=subprocess.run(args, capture_output=True, text=True)
    if p.returncode: raise RuntimeError(p.stderr[-1500:])
    return p.stdout
def probe(path):
    return json.loads(run(["ffprobe","-v","error","-show_format","-of","json",str(path)]))["format"]
def stamp(t):
    t=max(0,t)
    h=int(t//3600); m=int(t%3600//60); s=t%60
    return f"{h:02}:{m:02}:{s:05.2f}"
def ass_escape(s):
    return s.replace("\\","").replace("{","(").replace("}",")").replace("\n"," ")
def build_ass(segments, path):
    header="""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,70,&H00FFFFFF,&H0000FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,2,90,90,260,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines=[f"Dialogue: 0,{stamp(a)},{stamp(b)},Default,,0,0,0,,{ass_escape(txt)}" for a,b,txt in segments if b>a]
    path.write_text(header+"\n".join(lines),encoding="utf-8")
def speech_segments(path):
    global model
    if model is None: model=WhisperModel(os.getenv("WHISPER_MODEL","small"),device="cpu",compute_type="int8")
    segs,_=model.transcribe(str(path),language="pt",word_timestamps=True,vad_filter=True)
    output=[]
    for seg in segs:
        if seg.words:
            for w in seg.words: output.append((float(w.start),float(w.end),w.word.strip()))
        else: output.append((float(seg.start),float(seg.end),seg.text.strip()))
    return output
def keep_intervals(path,duration):
    data=run(["ffmpeg","-hide_banner","-i",str(path),"-af","silencedetect=noise=-35dB:d=0.65","-f","null","-"])
    return [(0,duration)]
def detect_intervals(path,duration):
    p=subprocess.run(["ffmpeg","-hide_banner","-i",str(path),"-af","silencedetect=noise=-35dB:d=0.65","-f","null","-"],capture_output=True,text=True)
    starts=[float(x) for x in re.findall(r"silence_start: ([\d.]+)",p.stderr)]
    ends=[float(x) for x in re.findall(r"silence_end: ([\d.]+)",p.stderr)]
    silence=[]; i=0
    for s in starts:
        e=next((v for v in ends if v>s),duration)
        silence.append((s,e))
    keep=[]; cursor=0
    for s,e in silence:
        if s-cursor>0.2:keep.append((max(0,cursor-0.08),min(duration,s+0.08)))
        cursor=max(cursor,e)
    if duration-cursor>0.2:keep.append((max(0,cursor-0.08),duration))
    return keep or [(0,duration)]
def cut_video(src,dst,intervals,has_audio):
    parts=[]
    for i,(a,b) in enumerate(intervals):
        parts.append(f"[0:v]trim=start={a}:end={b},setpts=PTS-STARTPTS[v{i}]")
        if has_audio:parts.append(f"[0:a]atrim=start={a}:end={b},asetpts=PTS-STARTPTS[a{i}]")
    refs="".join(f"[v{i}]"+(f"[a{i}]" if has_audio else "") for i in range(len(intervals)))
    parts.append(refs+f"concat=n={len(intervals)}:v=1:a={1 if has_audio else 0}[v]"+("[a]" if has_audio else ""))
    cmd=["ffmpeg","-y","-i",str(src),"-filter_complex",";".join(parts),"-map","[v]"]
    if has_audio:cmd+=["-map","[a]"]
    cmd+=["-c:v","libx264","-preset","veryfast","-crf","21"]
    if has_audio:cmd+=["-c:a","aac"]
    cmd+=[str(dst)]
    run(cmd)
@app.get("/")
def home(): return FileResponse(BASE/"editor.html")
@app.post("/api/edit")
async def edit(file:UploadFile=File(...),remove_silence:bool=Form(True)):
    if not file.filename or Path(file.filename).suffix.lower() not in {".mp4",".mov",".mkv",".webm"}:
        raise HTTPException(400,"Envie um vídeo MP4, MOV, MKV ou WebM.")
    job=uuid.uuid4().hex
    folder=JOBS/job;folder.mkdir()
    src=folder/("input"+Path(file.filename).suffix.lower())
    size=0
    with src.open("wb") as f:
        while chunk:=await file.read(1024*1024):
            size+=len(chunk)
            if size>200*1024*1024: raise HTTPException(413,"Limite: 200 MB")
            f.write(chunk)
    try:
        duration=float(probe(src)["duration"])
        if duration>180: raise HTTPException(400,"Limite: 3 minutos por vídeo.")
        audio=subprocess.run(["ffprobe","-v","error","-select_streams","a:0","-show_entries","stream=index","-of","csv=p=0",str(src)],capture_output=True,text=True).stdout.strip()!=""
        intervals=detect_intervals(src,duration) if remove_silence and audio else [(0,duration)]
        cut=folder/"cut.mp4"
        cut_video(src,cut,intervals,audio)
        words=speech_segments(cut) if audio else []
        ass=folder/"captions.ass";build_ass(words,ass)
        out=folder/"final.mp4"
        vf="scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1"
        if words: vf+=",ass="+str(ass).replace("\\","/").replace(":","\\:")
        cmd=["ffmpeg","-y","-i",str(cut),"-vf",vf,"-c:v","libx264","-preset","veryfast","-crf","21","-pix_fmt","yuv420p"]
        if audio:cmd+=["-c:a","aac","-b:a","160k"]
        cmd+=["-movflags","+faststart",str(out)]
        run(cmd)
        return {"job":job,"download":f"/api/download/{job}","transcript":" ".join(w[2] for w in words),"removed_silence":remove_silence}
    except HTTPException:raise
    except Exception as e:raise HTTPException(500,f"Erro no processamento: {str(e)[:400]}")
@app.get("/api/download/{job}")
def download(job:str):
    if not re.fullmatch("[a-f0-9]{32}",job):raise HTTPException(400,"ID inválido")
    path=JOBS/job/"final.mp4"
    if not path.exists():raise HTTPException(404,"Vídeo não encontrado")
    return FileResponse(path,media_type="video/mp4",filename="editor-magnetico-n1.mp4")
