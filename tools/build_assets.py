#!/usr/bin/env python3
"""Convierte los mp4 de una carpeta en los assets que lleva DENTRO del mod (fotogramas JPEG + audio OGG).
Uso: python3 build_assets.py carpeta_con_mp4   (requiere ffmpeg)
Calidad/tamano: scenes.json -> "embed": {"width":1280,"fps":24,"q":7}  (q: 2 mejor ... 31 peor)"""
import json, os, subprocess, sys
here = os.path.dirname(os.path.abspath(__file__))
src = sys.argv[1]
res = os.path.join(here, "..", "src", "main", "resources", "assets", "sarexstudio")
vd, sd = os.path.join(res, "cinematics"), os.path.join(res, "sounds")
os.makedirs(vd, exist_ok=True); os.makedirs(sd, exist_ok=True)
cfg = json.load(open(os.path.join(here, "scenes.json"), encoding="utf-8"))
emb = cfg.get("embed", {})
W, FPS, Q = emb.get("width", 1280), emb.get("fps", 24), emb.get("q", 7)
sounds, meta = {}, {}
for sc in cfg["scenes"]:
    n = sc["name"]; f = os.path.join(src, n + ".mp4")
    pr = subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries",
        "stream=width,height:format=duration","-of","json",f])
    j = json.loads(pr); sw, sh = j["streams"][0]["width"], j["streams"][0]["height"]
    dur = float(j["format"]["duration"])
    w = min(W, sw); h = int(round(w * sh / sw / 2.0)) * 2          # conserva la proporcion
    subprocess.run(["ffmpeg","-y","-v","error","-i",f,"-an","-vf",f"scale={w}:{h}:flags=lanczos,fps={FPS}",
        "-c:v","mjpeg","-q:v",str(Q),"-pix_fmt","yuvj420p","-f","mjpeg",os.path.join(vd,n+".mjpg")],check=True)
    subprocess.run(["ffmpeg","-y","-v","error","-i",f,"-vn","-c:a","libvorbis","-q:a","4","-ac","2","-ar","44100",
        os.path.join(sd,n+".ogg")],check=True)
    sounds[n] = {"sounds": [{"name": "sarexstudio:"+n, "stream": True}]}
    meta[n] = {"fps": FPS, "width": w, "height": h, "duration": round(dur,3)}
    print("OK", n, w, h, flush=True)
json.dump(sounds, open(os.path.join(res,"sounds.json"),"w"), indent=2)
json.dump(meta, open(os.path.join(vd,"index.json"),"w"), indent=2)
