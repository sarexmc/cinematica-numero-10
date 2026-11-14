#!/usr/bin/env python3
"""Genera un mp4 H.264 1080p60 por escena (audio AAC + fundidos) a partir de scenes.json.
Uso: python3 build_mp4.py video.mp4 [salida_dir] [escena1,escena2]   (requiere ffmpeg)
Por escena: "crop": "w:h:x:y" (recorte manual)  |  "autocrop": true (quita barras negras)"""
import json, os, re, subprocess, sys
from collections import Counter
here = os.path.dirname(os.path.abspath(__file__))
video = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "videos")
os.makedirs(out, exist_ok=True)
cfg = json.load(open(os.path.join(here, "scenes.json"), encoding="utf-8"))
H, FPS, CRF = cfg.get("height", 1080), cfg.get("fps", 60), cfg.get("crf", 16)
PRESET = cfg.get("preset", "veryfast")

def detect_crop(ss, dur):
    p = subprocess.run(["ffmpeg","-v","info","-ss",str(ss),"-t",str(dur),"-i",video,
        "-vf","fps=1,cropdetect=24:2:0","-f","null","-"], capture_output=True, text=True)
    found = re.findall(r"crop=(\d+:\d+:\d+:\d+)", p.stderr)
    return Counter(found).most_common(1)[0][0] if found else None

only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else None
for sc in cfg["scenes"]:
    if only and sc["name"] not in only: continue
    n, ss, dur = sc["name"], sc["start"], sc["end"] - sc["start"]
    vf = []
    crop = sc.get("crop") or (detect_crop(ss, dur) if sc.get("autocrop") else None)
    if sc.get("delogo"):
        vf.append("delogo=" + sc["delogo"] + ":enable='lt(t,%s)'" % sc.get("delogo_until", 9999))
    if crop: vf.append("crop=" + crop)
    vf += ["deblock=filter=strong:block=8:alpha=0.14:beta=0.08:gamma=0.06:delta=0.05",
           "hqdn3d=1.6:1.4:3.5:3",
           f"scale=-2:{H}:flags=lanczos" if not crop else f"scale=1920:-2:flags=lanczos",
           "cas=strength=0.4",
           "eq=contrast=1.03:saturation=1.06",
           f"fps={FPS}",
           f"fade=t=in:st=0:d=0.6,fade=t=out:st={dur-0.6:.2f}:d=0.6"]
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(ss),"-t",str(dur),"-i",video,
        "-vf",",".join(vf),"-af",f"afade=t=in:st=0:d=0.6,afade=t=out:st={dur-0.6:.2f}:d=0.6",
        "-c:v","libx264","-preset",PRESET,"-crf",str(CRF),"-pix_fmt","yuv420p",
        "-c:a","aac","-b:a","192k","-movflags","+faststart",
        os.path.join(out, n + ".mp4")], check=True)
    print("OK", n, crop or "", flush=True)
