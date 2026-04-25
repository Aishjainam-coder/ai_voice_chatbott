"""
main.py — Flask Server + Embedded Avatar UI
============================================
All frontend logic lives here as a Python string (AVATAR_HTML).
No separate .html file is needed.

Routes
------
  GET  /              → serves the embedded avatar chat page
  GET  /static/<file> → serves static files (avatar.glb)
  POST /listen        → voice pipeline: audio → STT → LLM → TTS → lipsync
  POST /text          → text pipeline:  text  →      LLM → TTS → lipsync

Run
---
  cd ai_avatar
  python main.py

Prerequisites (running in background before starting):
  ollama serve          # LLM server
  ollama pull llama3    # download model once
"""

import os
import base64
import pathlib

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────
load_dotenv()

# ── Import pipeline modules ───────────────────────────────────
import stt       # Whisper speech-to-text
import llm       # Ollama LLaMA 3
import tts       # Coqui XTTS-v2
import lipsync   # librosa → viseme timestamps
import emotions  # keyword → morph weights

# ── Flask setup ───────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

_TEMP_DIR = pathlib.Path(os.getenv("TTS_OUTPUT_DIR", "temp_audio"))
_TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
#  EMBEDDED AVATAR UI  (all frontend logic in Python string)
# ═══════════════════════════════════════════════════════════════

AVATAR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Aisha — AI Avatar</title>
<meta name="description" content="Multilingual AI avatar powered by LLaMA 3 and Coqui XTTS."/>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#0a0a12;--panel:#13131f;--accent:#7c5cfc;--accent2:#c05cfc;
  --text:#e8e8f0;--sub:#888;--red:#fc5c7d;--green:#56f89a;
  --glass:rgba(255,255,255,0.05);
}
body{background:var(--bg);color:var(--text);
  font-family:'Segoe UI',system-ui,sans-serif;
  height:100vh;overflow:hidden;display:flex;flex-direction:column;align-items:center;}
body::before{content:'';position:fixed;inset:0;
  background:radial-gradient(ellipse 60% 50% at 50% 0%,rgba(124,92,252,.18),transparent),
             radial-gradient(ellipse 40% 40% at 80% 80%,rgba(192,92,252,.12),transparent);
  pointer-events:none;z-index:0;}
#app{position:relative;z-index:1;width:100%;max-width:900px;height:100vh;
  display:flex;flex-direction:column;}
header{padding:16px 24px;display:flex;align-items:center;gap:12px;flex-shrink:0;}
.logo{width:36px;height:36px;border-radius:50%;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;font-size:18px;}
header h1{font-size:1.2rem;font-weight:700;letter-spacing:.02em;}
.dot{width:8px;height:8px;border-radius:50%;background:var(--green);
  box-shadow:0 0 8px var(--green);margin-left:auto;animation:pulse 2s infinite;}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
#canvas-wrap{flex:1;position:relative;overflow:hidden;}
#three-canvas{width:100%;height:100%;display:block;}
#transcript-badge{position:absolute;top:12px;left:50%;transform:translateX(-50%);
  max-width:75%;text-align:center;padding:7px 16px;
  background:rgba(124,92,252,.18);backdrop-filter:blur(8px);
  border:1px solid rgba(124,92,252,.3);border-radius:24px;
  font-size:.82rem;color:#c4b5fd;opacity:0;transition:opacity .4s;pointer-events:none;}
#transcript-badge.show{opacity:1;}
#subtitle{position:absolute;bottom:16px;left:50%;transform:translateX(-50%);
  max-width:80%;text-align:center;padding:10px 20px;
  background:rgba(0,0,0,.6);backdrop-filter:blur(12px);
  border-radius:30px;font-size:.95rem;line-height:1.5;
  border:1px solid rgba(255,255,255,.08);
  opacity:0;transition:opacity .4s;pointer-events:none;}
#subtitle.show{opacity:1;}
#emotion-badge{position:absolute;top:12px;right:16px;padding:5px 12px;
  border-radius:20px;font-size:.75rem;font-weight:600;
  background:var(--glass);border:1px solid rgba(255,255,255,.1);
  letter-spacing:.05em;text-transform:uppercase;}
#bottom{flex-shrink:0;padding:16px 20px 20px;display:flex;flex-direction:column;gap:12px;
  background:linear-gradient(to top,var(--panel),transparent);}
#text-row{display:flex;gap:10px;}
#text-input{flex:1;background:var(--glass);border:1px solid rgba(255,255,255,.1);
  border-radius:12px;padding:12px 16px;color:var(--text);font-size:.95rem;
  outline:none;transition:border-color .2s;}
#text-input:focus{border-color:var(--accent);}
#text-input::placeholder{color:var(--sub);}
#send-btn{background:linear-gradient(135deg,var(--accent),var(--accent2));
  border:none;border-radius:12px;padding:12px 20px;color:#fff;
  cursor:pointer;font-size:.9rem;font-weight:600;transition:opacity .2s,transform .1s;}
#send-btn:hover{opacity:.85;}#send-btn:active{transform:scale(.96);}
#mic-row{display:flex;justify-content:center;align-items:center;gap:16px;}
#mic-btn{width:72px;height:72px;border-radius:50%;border:none;cursor:pointer;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;font-size:28px;
  box-shadow:0 0 24px rgba(124,92,252,.4);transition:transform .15s,box-shadow .15s;}
#mic-btn:hover{transform:scale(1.07);}
#mic-btn.recording{background:linear-gradient(135deg,var(--red),#fc8a5c);
  box-shadow:0 0 32px rgba(252,92,125,.6);animation:mpulse 1s infinite;}
#mic-btn.thinking{opacity:.6;cursor:not-allowed;}
@keyframes mpulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
.mic-hint{font-size:.78rem;color:var(--sub);}
#proc-ring{width:20px;height:20px;border:2px solid rgba(255,255,255,.15);
  border-top-color:var(--accent);border-radius:50%;
  display:none;animation:spin .7s linear infinite;}
#proc-ring.show{display:block;}
@keyframes spin{to{transform:rotate(360deg)}}
#toast{position:fixed;bottom:24px;right:24px;padding:12px 20px;
  background:#2a0a15;border:1px solid var(--red);border-radius:12px;
  color:var(--red);font-size:.85rem;transform:translateY(80px);
  opacity:0;transition:all .35s;z-index:99;}
#toast.show{transform:translateY(0);opacity:1;}
</style>
</head>
<body>
<div id="app">
  <header>
    <div class="logo">✨</div>
    <h1>Aisha</h1>
    <span style="font-size:.8rem;color:var(--sub);margin-left:4px;">AI Avatar</span>
    <div class="dot" id="status-dot"></div>
  </header>
  <div id="canvas-wrap">
    <canvas id="three-canvas"></canvas>
    <div id="transcript-badge"></div>
    <div id="subtitle"></div>
    <div id="emotion-badge">Neutral 😌</div>
  </div>
  <div id="bottom">
    <div id="text-row">
      <input id="text-input" type="text"
        placeholder="Type a message… (Hindi, English, Hinglish…)" autocomplete="off"/>
      <button id="send-btn">Send</button>
    </div>
    <div id="mic-row">
      <span class="mic-hint">Hold to talk</span>
      <button id="mic-btn" title="Hold to record">🎤</button>
      <div id="proc-ring"></div>
    </div>
  </div>
</div>
<div id="toast"></div>

<script src="https://cdn.jsdelivr.net/npm/three@0.158.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.158.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
'use strict';

// ── Three.js scene ─────────────────────────────────────────
const canvas   = document.getElementById('three-canvas');
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputEncoding = THREE.sRGBEncoding;
renderer.shadowMap.enabled = true;

const scene  = new THREE.Scene();
scene.fog    = new THREE.FogExp2(0x0a0a12, 0.035);
const camera = new THREE.PerspectiveCamera(38,1,0.1,100);
camera.position.set(0,1.55,2.2);
camera.lookAt(0,1.5,0);

function onResize(){
  const w = canvas.parentElement.clientWidth;
  const h = canvas.parentElement.clientHeight;
  renderer.setSize(w,h);
  camera.aspect = w/h;
  camera.updateProjectionMatrix();
}
onResize();
new ResizeObserver(onResize).observe(canvas.parentElement);

// Lights
scene.add(new THREE.AmbientLight(0xffffff,0.6));
const key = new THREE.DirectionalLight(0xfff0e0,1.2);
key.position.set(1.5,3,2); key.castShadow=true; scene.add(key);
const fill = new THREE.DirectionalLight(0xc0a0ff,0.4);
fill.position.set(-2,1,1); scene.add(fill);
const rim = new THREE.DirectionalLight(0x8060ff,0.5);
rim.position.set(0,2,-3); scene.add(rim);

// ── Avatar load ────────────────────────────────────────────
let avatar=null, morphMesh=null, morphDict={};
const loader = new THREE.GLTFLoader();
loader.load('/static/avatar.glb', gltf=>{
  avatar = gltf.scene;
  scene.add(avatar);
  avatar.traverse(o=>{
    if(o.isMesh && o.morphTargetDictionary &&
       Object.keys(o.morphTargetDictionary).length>0){
      if(!morphMesh || Object.keys(o.morphTargetDictionary).length>Object.keys(morphDict).length){
        morphMesh=o; morphDict=o.morphTargetDictionary;
      }
    }
  });
  console.log('[avatar] loaded. Morphs:', Object.keys(morphDict).join(', '));
  document.getElementById('status-dot').style.background='#56f89a';
}, null, err=>showToast('Avatar load error: '+err.message));

function setMorph(name,val){
  if(!morphMesh) return;
  const i=morphDict[name]; if(i===undefined) return;
  morphMesh.morphTargetInfluences[i]=Math.max(0,Math.min(1,val));
}

// ── Idle: blink, breathe, eye drift ───────────────────────
let blinkTimer=3, blinkPhase='open', blinkT=0;
let eyeTarget={x:0,y:0}, eyeCur={x:0,y:0}, eyeDriftT=2;
let breatheT=0;

function idleUpdate(dt){
  if(!morphMesh) return;
  // Blink
  blinkTimer-=dt;
  if(blinkTimer<=0){blinkPhase='closing';blinkT=0;blinkTimer=3+Math.random()*4;}
  if(blinkPhase!=='open'){
    blinkT+=dt/0.07;
    const w=blinkPhase==='closing'?Math.min(blinkT,1):1-Math.min(blinkT,1);
    setMorph('eyeBlinkLeft',w); setMorph('eyeBlinkRight',w);
    if(blinkT>=1){
      if(blinkPhase==='closing'){blinkPhase='opening';blinkT=0;}
      else{blinkPhase='open';setMorph('eyeBlinkLeft',0);setMorph('eyeBlinkRight',0);}
    }
  }
  // Eye drift
  eyeDriftT-=dt;
  if(eyeDriftT<=0){
    eyeTarget.x=(Math.random()-.5)*.4; eyeTarget.y=(Math.random()-.5)*.2;
    eyeDriftT=2+Math.random()*3;
  }
  eyeCur.x+=(eyeTarget.x-eyeCur.x)*dt*3;
  eyeCur.y+=(eyeTarget.y-eyeCur.y)*dt*3;
  setMorph('eyeLookInLeft',  Math.max(0, eyeCur.x));
  setMorph('eyeLookOutRight',Math.max(0, eyeCur.x));
  setMorph('eyeLookUpLeft',  Math.max(0, eyeCur.y));
  setMorph('eyeLookDownLeft',Math.max(0,-eyeCur.y));
  // Breathe
  breatheT+=dt*0.4;
  if(avatar) avatar.position.y=Math.sin(breatheT)*0.003;
}

// ── Lip sync ───────────────────────────────────────────────
let visQ=[], visStart=0, lipPlaying=false;
const LIP_MORPHS=[
  'viseme_PP','viseme_FF','viseme_TH','viseme_DD','viseme_kk',
  'viseme_CH','viseme_SS','viseme_nn','viseme_RR','viseme_aa',
  'viseme_E','viseme_I','viseme_O','viseme_U','jawOpen'
];

function startLipsync(visemes,startMs){visQ=visemes;visStart=startMs;lipPlaying=true;}

function lipsyncUpdate(){
  if(!lipPlaying||!morphMesh) return;
  const elapsed=(performance.now()-visStart)/1000;
  const active={};
  for(const ev of visQ) if(elapsed>=ev.t&&elapsed<ev.t+ev.dur) active[ev.vis]=1;
  for(const m of LIP_MORPHS){
    const i=morphDict[m]; if(i===undefined) continue;
    const target=active[m]||0;
    morphMesh.morphTargetInfluences[i]=morphMesh.morphTargetInfluences[i]*0.7+target*0.3;
  }
  if(visQ.length){
    const last=visQ[visQ.length-1];
    if(elapsed>last.t+last.dur+0.3){
      lipPlaying=false;
      for(const m of LIP_MORPHS) setMorph(m,0);
    }
  }
}

// ── Emotion ────────────────────────────────────────────────
const EMO_MORPHS=[
  'mouthSmile','mouthFrownLeft','mouthFrownRight',
  'browDownLeft','browDownRight','browInnerUp',
  'eyeWideLeft','eyeWideRight','cheekSquintLeft','cheekSquintRight'
];
const EMO_ICONS={happy:'😊',sad:'😢',angry:'😠',surprised:'😲',neutral:'😌'};
let eTarget={}, eCur={};

function applyEmotion(emotion,weights){
  eTarget={...weights};
  document.getElementById('emotion-badge').textContent=
    (EMO_ICONS[emotion]||'😌')+' '+emotion.charAt(0).toUpperCase()+emotion.slice(1);
}

function emotionUpdate(dt){
  if(!morphMesh) return;
  for(const m of EMO_MORPHS){
    const i=morphDict[m]; if(i===undefined) continue;
    if(eCur[m]===undefined) eCur[m]=0;
    eCur[m]+=(( eTarget[m]||0)-eCur[m])*dt*2;
    morphMesh.morphTargetInfluences[i]=eCur[m];
  }
}

// ── Render loop ────────────────────────────────────────────
let lastT=performance.now();
function animate(){
  requestAnimationFrame(animate);
  const now=performance.now(), dt=Math.min((now-lastT)/1000,0.1); lastT=now;
  idleUpdate(dt); lipsyncUpdate(); emotionUpdate(dt);
  renderer.render(scene,camera);
}
animate();

// ── Mic recording ──────────────────────────────────────────
let mediaRec=null, audioChunks=[], micStream=null;
const micBtn=document.getElementById('mic-btn');

micBtn.addEventListener('mousedown',startRec);
micBtn.addEventListener('touchstart',startRec,{passive:true});
micBtn.addEventListener('mouseup',stopRec);
micBtn.addEventListener('mouseleave',stopRec);
micBtn.addEventListener('touchend',stopRec);

async function startRec(e){
  e.preventDefault();
  if(micBtn.classList.contains('thinking')) return;
  try{
    micStream=await navigator.mediaDevices.getUserMedia({audio:true});
    audioChunks=[];
    const mime=MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ?'audio/webm;codecs=opus':'audio/webm';
    mediaRec=new MediaRecorder(micStream,{mimeType:mime});
    mediaRec.ondataavailable=e=>audioChunks.push(e.data);
    mediaRec.onstop=onRecStop;
    mediaRec.start();
    micBtn.classList.add('recording');
    micBtn.textContent='⏹';
  }catch(err){showToast('Mic denied: '+err.message);}
}

function stopRec(){
  if(!mediaRec||mediaRec.state==='inactive') return;
  mediaRec.stop(); micStream.getTracks().forEach(t=>t.stop());
  micBtn.classList.remove('recording'); micBtn.textContent='🎤';
}

async function onRecStop(){
  const blob=new Blob(audioChunks,{type:audioChunks[0]?.type||'audio/webm'});
  if(blob.size<1000) return;
  setBusy(true);
  const fd=new FormData(); fd.append('audio',blob,'rec.webm');
  try{
    const res=await fetch('/listen',{method:'POST',body:fd});
    if(!res.ok) throw new Error('Server '+res.status);
    const data=await res.json();
    if(data.transcript) showTranscript(data.transcript);
    handleReply(data);
  }catch(err){showToast(err.message);}
  finally{setBusy(false);}
}

// ── Text input ─────────────────────────────────────────────
document.getElementById('send-btn').addEventListener('click',sendText);
document.getElementById('text-input').addEventListener('keydown',e=>{if(e.key==='Enter')sendText();});

async function sendText(){
  const inp=document.getElementById('text-input');
  const msg=inp.value.trim(); if(!msg) return;
  inp.value=''; showTranscript(msg); setBusy(true);
  try{
    const res=await fetch('/text',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:msg,language:'en'})
    });
    if(!res.ok) throw new Error('Server '+res.status);
    handleReply(await res.json());
  }catch(err){showToast(err.message);}
  finally{setBusy(false);}
}

// ── Response handler ───────────────────────────────────────
function handleReply(data){
  if(data.error){showToast(data.error);return;}
  showSubtitle(data.reply||'');
  if(data.emotion&&data.weights) applyEmotion(data.emotion,data.weights);
  if(data.audio_base64){
    const buf=b64ToBuffer(data.audio_base64);
    new AudioContext().decodeAudioData(buf,ab=>{
      const ctx=new AudioContext();
      const src=ctx.createBufferSource(); src.buffer=ab;
      src.connect(ctx.destination);
      const t0=performance.now(); src.start(0);
      if(data.visemes&&data.visemes.length) startLipsync(data.visemes,t0);
    },err=>showToast('Audio error: '+err));
  }
}

// ── UI helpers ─────────────────────────────────────────────
function showTranscript(t){
  const el=document.getElementById('transcript-badge');
  el.textContent='🗣 '+t; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),5000);
}
let stTimer=null;
function showSubtitle(t){
  const el=document.getElementById('subtitle');
  el.textContent=t; el.classList.add('show');
  if(stTimer) clearTimeout(stTimer);
  stTimer=setTimeout(()=>el.classList.remove('show'),Math.max(4000,t.length*60));
}
let toastTimer=null;
function showToast(m){
  const el=document.getElementById('toast');
  el.textContent='⚠ '+m; el.classList.add('show');
  if(toastTimer) clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>el.classList.remove('show'),4500);
}
function setBusy(b){
  micBtn.classList.toggle('thinking',b);
  document.getElementById('proc-ring').classList.toggle('show',b);
  document.getElementById('send-btn').disabled=b;
}
function b64ToBuffer(b64){
  const bin=atob(b64),buf=new ArrayBuffer(bin.length),v=new Uint8Array(buf);
  for(let i=0;i<bin.length;i++) v[i]=bin.charCodeAt(i);
  return buf;
}

// Default neutral emotion on load
applyEmotion('neutral',{mouthSmile:0.05,mouthFrownLeft:0,mouthFrownRight:0,
  browDownLeft:0,browDownRight:0,browInnerUp:0,
  eyeWideLeft:0,eyeWideRight:0,cheekSquintLeft:0,cheekSquintRight:0});
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the avatar UI — rendered from the Python string above."""
    return render_template_string(AVATAR_HTML)


@app.route("/static/<path:filename>")
def serve_static(filename):
    """Serve avatar.glb and any other static assets."""
    return send_from_directory("static", filename)


@app.route("/listen", methods=["POST"])
def listen():
    """
    Voice pipeline:
      1. Save uploaded audio blob
      2. Whisper STT  → transcript + language
      3. Ollama LLM   → Aisha reply
      4. XTTS-v2 TTS  → WAV file
      5. librosa      → viseme timestamps
      6. emotions     → morph weights
      7. Return JSON
    """
    if "audio" not in request.files:
        return jsonify({"error": "No audio in request."}), 400

    audio_file = request.files["audio"]
    suffix     = pathlib.Path(audio_file.filename or "a.webm").suffix or ".webm"
    tmp_path   = _TEMP_DIR / f"upload_{os.getpid()}_{id(request)}{suffix}"
    audio_file.save(str(tmp_path))

    try:
        return _run_pipeline(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)


@app.route("/text", methods=["POST"])
def text_input():
    """
    Text pipeline (no STT step):
      Body JSON: { "message": "...", "language": "en" }
    """
    data     = request.get_json(force=True, silent=True) or {}
    message  = data.get("message", "").strip()
    language = data.get("language", "en")

    if not message:
        return jsonify({"error": "No message provided."}), 400

    return _run_pipeline_from_text(message, language)


# ═══════════════════════════════════════════════════════════════
#  PIPELINE HELPERS
# ═══════════════════════════════════════════════════════════════

def _run_pipeline(audio_path: str):
    """Full pipeline starting from an audio file."""
    transcript, language = stt.transcribe(audio_path)
    if not transcript:
        return jsonify({"error": "Could not transcribe audio."}), 422
    return _run_pipeline_from_text(transcript, language)


def _run_pipeline_from_text(transcript: str, language: str):
    """LLM → TTS → lipsync → emotions → JSON response."""
    # 1. Generate Aisha's reply
    reply = llm.generate_reply(transcript, language)

    # 2. Synthesise speech to WAV
    wav_filename = f"reply_{os.getpid()}.wav"
    wav_path     = tts.synthesise(reply, language, output_filename=wav_filename)

    # 3. Extract viseme timing from the WAV
    viseme_events = lipsync.extract_visemes(wav_path)

    # 4. Detect emotion from reply text
    emotion_data = emotions.detect_emotion(reply)

    # 5. Encode WAV as base64 for inline transport to browser
    with open(wav_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    # Clean up the WAV — browser has it now
    pathlib.Path(wav_path).unlink(missing_ok=True)

    return jsonify({
        "transcript":   transcript,
        "reply":        reply,
        "language":     language,
        "audio_base64": audio_b64,
        "visemes":      viseme_events,
        "emotion":      emotion_data["emotion"],
        "weights":      emotion_data["weights"],
    })


# ═══════════════════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n{'='*50}")
    print(f"  Aisha AI Avatar  →  http://localhost:{port}")
    print(f"{'='*50}\n")
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,    # keep False — reload would re-import heavy models
        threaded=False, # keep False — avoids CUDA/XTTS context conflicts
    )
