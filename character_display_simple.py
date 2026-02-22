"""
Character Display — CSS-animated avatar with emotion overlays.
Provides get_character_image() for PIL-based frame generation.
The main animated display is handled in app.py via HTML/JS.
"""
import os
from PIL import Image, ImageDraw, ImageFilter

EMOTION_COLORS = {
    "happy":"#4CAF50","excited":"#FF9800","sad":"#607D8B",
    "calm":"#009688","friendly":"#2196F3","concerned":"#795548",
    "confident":"#9C27B0","professional":"#37474F",
    "empathetic":"#E91E63","thoughtful":"#3F51B5",
    "focused":"#00BCD4","attentive":"#8BC34A",
}
EMOTION_EMOJI = {
    "happy":"😊","excited":"🤩","sad":"😔","calm":"😌",
    "friendly":"😊","concerned":"😟","confident":"💪",
    "professional":"👔","empathetic":"🤗","thoughtful":"🤔",
}
MOUTH_OPEN = {
    "sil":0.0,"PP":0.0,"FF":0.15,"TH":0.2,"DD":0.25,
    "kk":0.3,"CH":0.35,"SS":0.2,"nn":0.25,"RR":0.4,
    "aa":0.75,"E":0.55,"I":0.4,"O":0.5,"U":0.45,
}

def get_character_image(path, emotion="calm", mouth="sil", size=(320,340)):
    if path and os.path.exists(path):
        try:
            img = Image.open(path).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        except:
            img = Image.new("RGBA", size, (30,30,50,255))
    else:
        img = Image.new("RGBA", size, (30,30,50,255))
        d = ImageDraw.Draw(img)
        d.text((size[0]//2-60, size[1]//2), "Add character.png\nto assets/", fill="white")
        return img.convert("RGB")

    overlay = Image.new("RGBA", size, (0,0,0,0))
    d = ImageDraw.Draw(overlay, "RGBA")

    open_r = MOUTH_OPEN.get(mouth, 0.0)
    if open_r > 0.05:
        cx, cy = size[0]//2, int(size[1]*0.72)
        mw, mh = int(size[0]*0.14), int(size[1]*0.07*open_r+4)
        d.ellipse((cx-mw,cy-mh,cx+mw,cy+mh), fill=(60,20,10,170))
        d.ellipse((cx-mw+3,cy-mh+3,cx+mw-3,cy+mh-3), fill=(15,5,5,200))

    color = EMOTION_COLORS.get(emotion,"#009688")
    emoji = EMOTION_EMOJI.get(emotion,"😌")
    r,g,b = int(color[1:3],16),int(color[3:5],16),int(color[5:7],16)
    bm,bh = 8, 36
    d.rounded_rectangle((bm,size[1]-bh-bm,size[0]-bm,size[1]-bm),
                         radius=10, fill=(r,g,b,160), outline=(r,g,b,220), width=2)
    d.text((size[0]//2-40, size[1]-bh+6), f"{emoji} {emotion.upper()}", fill="white")

    result = Image.alpha_composite(img, overlay)
    return result.convert("RGB")