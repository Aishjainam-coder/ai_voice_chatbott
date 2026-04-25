"""
main.py — Flask Server + Embedded Avatar UI
============================================
All frontend logic lives here as a Python string (AVATAR_HTML).
No separate .html file is needed.

Run:
  cd ai_avatar
  .\tts_env\Scripts\activate
  python main.py
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
import tts       # Edge-TTS
import lipsync   # librosa → viseme timestamps
import emotions  # keyword → morph weights

# ── Flask setup ───────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

_TEMP_DIR = pathlib.Path(os.getenv("TTS_OUTPUT_DIR", "temp_audio"))
_TEMP_DIR.mkdir(parents=True, exist_ok=True)


# ═══════════════════════════════════════════════════════════════
#  EMBEDDED AVATAR UI
# ═══════════════════════════════════════════════════════════════

AVATAR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Aisha — AI Avatar</title>
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

<script type="importmap">
{
  "imports": {
    "three": "https://cdn.jsdelivr.net/npm/three@0.158.0/build/three.module.js",
    "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.158.0/examples/jsm/"
  }
}
</script>

<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

// ── Three.js scene ─────────────────────────────────────────
const canvas   = document.getElementById('three-canvas');
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
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

scene.add(new THREE.AmbientLight(0xffffff,0.6));
const key = new THREE.DirectionalLight(0xfff0e0,1.2);
key.position.set(1.5,3,2); key.castShadow=true; scene.add(key);
const fill = new THREE.DirectionalLight(0xc0a0ff,0.4);
fill.position.set(-2,1,1); scene.add(fill);
const rim = new THREE.DirectionalLight(0x8060ff,0.5);
rim.position.set(0,2,-3); scene.add(rim);

// ── Avatar load ────────────────────────────────────────────
let avatar=null, morphMesh=null, morphDict={};
const loader = new GLTFLoader();
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
}, null, err=>{
  console.error(err);
  showToast('Avatar load error: '+err.message);
});

window.setMorph = (name,val)=>{
  if(!morphMesh) return;
  const i=morphDict[name]; if(i===undefined) return;
  morphMesh.morphTargetInfluences[i]=Math.max(0,Math.min(1,val));
}

// ── Idle & Lipsync Logic ──────────────────────────────────
let blinkTimer=3, blinkPhase='open', blinkT=0;
let eyeTarget={x:0,y:0}, eyeCur={x:0,y:0}, eyeDriftT=2;
let breatheT=0;

let visQ=[], visStart=0, lipPlaying=false;
const LIP_MORPHS=[
  'viseme_PP','viseme_FF','viseme_TH','viseme_DD','viseme_kk',
  'viseme_CH','viseme_SS','viseme_nn','viseme_RR','viseme_aa',
  'viseme_E','viseme_I','viseme_O','viseme_U','jawOpen'
];

let eTarget={}, eCur={};
const EMO_MORPHS=[
  'mouthSmile','mouthFrownLeft','mouthFrownRight',
  'browDownLeft','browDownRight','browInnerUp',
  'eyeWideLeft','eyeWideRight','cheekSquintLeft','cheekSquintRight'
];
const EMO_ICONS={happy:'😊',sad:'😢',angry:'😠',surprised:'😲',neutral:'😌'};

function idleUpdate(dt){
  if(!morphMesh) return;
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
  breatheT+=dt*0.4;
  if(avatar) avatar.position.y=Math.sin(breatheT)*0.003;
}

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

function emotionUpdate(dt){
  if(!morphMesh) return;
  for(const m of EMO_MORPHS){
    const i=morphDict[m]; if(i===undefined) continue;
    if(eCur[m]===undefined) eCur[m]=0;
    eCur[m]+=(( eTarget[m]||0)-eCur[m])*dt*2;
    morphMesh.morphTargetInfluences[i]=eCur[m];
  }
}

function animate(){
  requestAnimationFrame(animate);
  const now=performance.now();
  const dt=Math.min((now-lastT)/1000,0.1);
  lastT=now;
  idleUpdate(dt); lipsyncUpdate(); emotionUpdate(dt);
  renderer.render(scene,camera);
}
let lastT=performance.now();
animate();

// ── Interaction Logic ──────────────────────────────────────
const micBtn=document.getElementById('mic-btn');
let mediaRec=null, audioChunks=[], micStream=null;

micBtn.addEventListener('mousedown',startRec);
micBtn.addEventListener('mouseup',stopRec);

async function startRec(){
  if(micBtn.classList.contains('thinking')) return;
  try{
    micStream=await navigator.mediaDevices.getUserMedia({audio:true});
    audioChunks=[];
    mediaRec=new MediaRecorder(micStream);
    mediaRec.ondataavailable=e=>audioChunks.push(e.data);
    mediaRec.onstop=onRecStop;
    mediaRec.start();
    micBtn.classList.add('recording');
  }catch(err){showToast('Mic denied: '+err.message);}
}

function stopRec(){
  if(!mediaRec||mediaRec.state==='inactive') return;
  mediaRec.stop(); micStream.getTracks().forEach(t=>t.stop());
  micBtn.classList.remove('recording');
}

async function onRecStop(){
  const blob=new Blob(audioChunks);
  if(blob.size<1000) return;
  setBusy(true);
  const fd=new FormData(); fd.append('audio',blob);
  try{
    const res=await fetch('/listen',{method:'POST',body:fd});
    handleReply(await res.json());
  }catch(err){showToast(err.message);}
  finally{setBusy(false);}
}

document.getElementById('send-btn').addEventListener('click',sendText);
async function sendText(){
  const inp=document.getElementById('text-input');
  const msg=inp.value.trim(); if(!msg) return;
  inp.value=''; setBusy(true);
  try{
    const res=await fetch('/text',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({message:msg})
    });
    handleReply(await res.json());
  }catch(err){showToast(err.message);}
  finally{setBusy(false);}
}

function handleReply(data){
  if(data.error){showToast(data.error);return;}
  if(data.transcript) showTranscript(data.transcript);
  showSubtitle(data.reply||'');
  if(data.emotion) {
     eTarget={...data.weights};
     document.getElementById('emotion-badge').textContent=
       (EMO_ICONS[data.emotion]||'😌')+' '+data.emotion.toUpperCase();
  }
  if(data.audio_base64){
    const buf=b64ToBuffer(data.audio_base64);
    new AudioContext().decodeAudioData(buf,ab=>{
      const ctx=new AudioContext();
      const src=ctx.createBufferSource(); src.buffer=ab;
      src.connect(ctx.destination);
      visQ=data.visemes; visStart=performance.now(); lipPlaying=true;
      src.start(0);
    });
  }
}

function showTranscript(t){
  const el=document.getElementById('transcript-badge');
  el.textContent='🗣 '+t; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),5000);
}
function showSubtitle(t){
  const el=document.getElementById('subtitle');
  el.textContent=t; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),5000);
}
function showToast(m){
  const el=document.getElementById('toast');
  el.textContent='⚠ '+m; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),4000);
}
function setBusy(b){
  micBtn.classList.toggle('thinking',b);
  document.getElementById('send-btn').disabled=b;
}
function b64ToBuffer(b64){
  const bin=atob(b64),buf=new ArrayBuffer(bin.length),v=new Uint8Array(buf);
  for(let i=0;i<bin.length;i++) v[i]=bin.charCodeAt(i);
  return buf;
}
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════
#  FLASK ROUTES
# ═══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template_string(AVATAR_HTML)

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/listen", methods=["POST"])
def listen():
    if "audio" not in request.files:
        return jsonify({"error": "No audio."}), 400
    audio_file = request.files["audio"]
    tmp_path = _TEMP_DIR / f"upload_{os.getpid()}.webm"
    audio_file.save(str(tmp_path))
    try:
        return _run_pipeline(str(tmp_path))
    finally:
        tmp_path.unlink(missing_ok=True)

@app.route("/text", methods=["POST"])
def text_input():
    data = request.get_json(force=True, silent=True) or {}
    message = data.get("message", "").strip()
    if not message: return jsonify({"error": "No message."}), 400
    return _run_pipeline_from_text(message, "en")

def _run_pipeline(audio_path: str):
    transcript, language = stt.transcribe(audio_path)
    if not transcript: return jsonify({"error": "No transcript."}), 422
    return _run_pipeline_from_text(transcript, language)

def _run_pipeline_from_text(transcript: str, language: str):
    reply = llm.generate_reply(transcript, language)
    wav_path = tts.synthesise(reply, language)
    viseme_events = lipsync.extract_visemes(wav_path)
    emotion_data = emotions.detect_emotion(reply)
    with open(wav_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")
    pathlib.Path(wav_path).unlink(missing_ok=True)
    return jsonify({
        "transcript": transcript, "reply": reply, "audio_base64": audio_b64,
        "visemes": viseme_events, "emotion": emotion_data["emotion"],
        "weights": emotion_data["weights"]
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n Aisha AI Avatar -> http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=False)
