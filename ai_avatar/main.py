"""
main.py — Flask Server + Embedded Face-Only Avatar UI
Run:
  cd ai_avatar
  python main.py
"""

import os, base64, pathlib
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

import stt
import llm
import tts
import lipsync
import emotions

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

_TEMP_DIR = pathlib.Path(os.getenv("TTS_OUTPUT_DIR", "temp_audio"))
_TEMP_DIR.mkdir(parents=True, exist_ok=True)


AVATAR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Aisha — AI Avatar</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet"/>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --bg:#060610;--accent:#7c5cfc;--accent2:#c05cfc;
  --text:#e8e8f0;--sub:#6b7280;--red:#fc5c7d;--green:#34d399;
}
body{
  background:var(--bg);color:var(--text);
  font-family:'Inter',system-ui,sans-serif;
  height:100vh;overflow:hidden;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
}
body::before{
  content:'';position:fixed;inset:0;
  background:
    radial-gradient(ellipse 70% 60% at 50% -10%,rgba(124,92,252,.25),transparent),
    radial-gradient(ellipse 50% 40% at 90% 90%,rgba(192,92,252,.15),transparent),
    radial-gradient(ellipse 40% 40% at 10% 80%,rgba(52,211,153,.08),transparent);
  pointer-events:none;z-index:0;
}

#app{
  position:relative;z-index:1;
  width:100%;max-width:480px;
  display:flex;flex-direction:column;align-items:center;gap:0;
  height:100vh;
}

/* ── Header ── */
header{
  width:100%;padding:18px 24px 10px;
  display:flex;align-items:center;gap:10px;
}
.logo-ring{
  width:38px;height:38px;border-radius:50%;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;font-size:17px;
}
header h1{font-size:1.1rem;font-weight:700;letter-spacing:.01em;}
header .tagline{font-size:.75rem;color:var(--sub);margin-left:2px;}
.status-dot{
  width:8px;height:8px;border-radius:50%;
  background:var(--sub);margin-left:auto;
  transition:background .4s,box-shadow .4s;
}
.status-dot.ready{background:var(--green);box-shadow:0 0 8px var(--green);}
.status-dot.busy{background:var(--accent);box-shadow:0 0 8px var(--accent);animation:blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}

/* ── Face canvas area ── */
#face-wrap{
  flex:1;width:100%;position:relative;overflow:hidden;
  display:flex;align-items:center;justify-content:center;
}
#three-canvas{width:100%;height:100%;display:block;}

/* ── Subtitle overlay ── */
#subtitle{
  position:absolute;bottom:14px;left:50%;transform:translateX(-50%);
  max-width:88%;text-align:center;
  padding:9px 18px;
  background:rgba(6,6,16,.75);backdrop-filter:blur(14px);
  border:1px solid rgba(255,255,255,.08);border-radius:28px;
  font-size:.9rem;line-height:1.55;color:var(--text);
  opacity:0;transition:opacity .4s;pointer-events:none;
  white-space:pre-wrap;
}
#subtitle.show{opacity:1;}

/* ── Transcript badge ── */
#transcript-badge{
  position:absolute;top:10px;left:50%;transform:translateX(-50%);
  max-width:80%;text-align:center;
  padding:6px 14px;
  background:rgba(124,92,252,.18);backdrop-filter:blur(8px);
  border:1px solid rgba(124,92,252,.3);border-radius:20px;
  font-size:.78rem;color:#c4b5fd;
  opacity:0;transition:opacity .4s;pointer-events:none;
}
#transcript-badge.show{opacity:1;}

/* ── Emotion badge ── */
#emotion-badge{
  position:absolute;top:10px;right:14px;
  padding:5px 11px;border-radius:18px;
  font-size:.72rem;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
  background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.1);
}

/* ── Bottom controls ── */
#bottom{
  flex-shrink:0;width:100%;
  padding:14px 20px 22px;
  display:flex;flex-direction:column;align-items:center;gap:12px;
  background:linear-gradient(to top,rgba(6,6,16,1) 60%,transparent);
}

/* Text input row */
#text-row{
  display:flex;gap:8px;width:100%;
}
#text-input{
  flex:1;background:rgba(255,255,255,.06);
  border:1px solid rgba(255,255,255,.1);
  border-radius:12px;padding:11px 15px;
  color:var(--text);font-size:.9rem;outline:none;
  transition:border-color .2s;
  font-family:'Inter',system-ui,sans-serif;
}
#text-input:focus{border-color:var(--accent);}
#text-input::placeholder{color:var(--sub);}
#send-btn{
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  border:none;border-radius:12px;padding:11px 18px;
  color:#fff;font-size:.88rem;font-weight:600;cursor:pointer;
  transition:opacity .2s,transform .1s;white-space:nowrap;
  font-family:'Inter',system-ui,sans-serif;
}
#send-btn:hover{opacity:.85;}
#send-btn:active{transform:scale(.96);}
#send-btn:disabled{opacity:.4;cursor:not-allowed;}

/* Mic row */
#mic-row{
  display:flex;align-items:center;justify-content:center;gap:18px;
}
#mic-btn{
  width:68px;height:68px;border-radius:50%;border:none;cursor:pointer;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex;align-items:center;justify-content:center;font-size:26px;
  box-shadow:0 0 24px rgba(124,92,252,.4);
  transition:transform .15s,box-shadow .15s,background .2s;
}
#mic-btn:hover{transform:scale(1.07);}
#mic-btn.recording{
  background:linear-gradient(135deg,var(--red),#fc8a5c);
  box-shadow:0 0 36px rgba(252,92,125,.7);
  animation:mpulse 1s infinite;
}
#mic-btn.busy{opacity:.5;cursor:not-allowed;transform:none!important;}
@keyframes mpulse{0%,100%{transform:scale(1)}50%{transform:scale(1.1)}}
.mic-hint{font-size:.76rem;color:var(--sub);}
#proc-ring{
  width:22px;height:22px;border:2.5px solid rgba(255,255,255,.15);
  border-top-color:var(--accent);border-radius:50%;
  display:none;animation:spin .7s linear infinite;
}
#proc-ring.show{display:block;}
@keyframes spin{to{transform:rotate(360deg)}}

/* Toast */
#toast{
  position:fixed;bottom:20px;right:20px;
  padding:11px 18px;background:#200814;
  border:1px solid var(--red);border-radius:12px;
  color:var(--red);font-size:.83rem;
  transform:translateY(80px);opacity:0;
  transition:all .35s;z-index:999;
  font-family:'Inter',system-ui,sans-serif;
}
#toast.show{transform:translateY(0);opacity:1;}
</style>
</head>
<body>
<div id="app">
  <header>
    <div class="logo-ring">✨</div>
    <h1>Aisha</h1>
    <span class="tagline">AI Avatar</span>
    <div class="status-dot" id="status-dot"></div>
  </header>

  <div id="face-wrap">
    <canvas id="three-canvas"></canvas>
    <div id="transcript-badge"></div>
    <div id="subtitle"></div>
    <div id="emotion-badge">Neutral 😌</div>
  </div>

  <div id="bottom">
    <div id="text-row">
      <input id="text-input" type="text"
        placeholder="Type a message… (Hindi / English / Hinglish)" autocomplete="off"/>
      <button id="send-btn">Send ↗</button>
    </div>
    <div id="mic-row">
      <span class="mic-hint">Click to talk</span>
      <button id="mic-btn" title="Click to record / stop">🎤</button>
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

// ── Scene ─────────────────────────────────────────────────────
const canvas   = document.getElementById('three-canvas');
const renderer = new THREE.WebGLRenderer({canvas, antialias:true, alpha:true});
renderer.setPixelRatio(Math.min(devicePixelRatio,2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;

const scene  = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(28, 1, 0.1, 100);

// Face-only framing: tight crop on head
camera.position.set(0, 1.65, 1.5);
camera.lookAt(0, 1.62, 0);

function onResize(){
  const wrap = canvas.parentElement;
  const w = wrap.clientWidth, h = wrap.clientHeight;
  renderer.setSize(w, h);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
onResize();
new ResizeObserver(onResize).observe(canvas.parentElement);

// ── Lighting ──────────────────────────────────────────────────
scene.add(new THREE.AmbientLight(0xffffff, 0.7));
const key = new THREE.DirectionalLight(0xfff5e0, 1.4);
key.position.set(1.5, 3, 2.5); key.castShadow=true; scene.add(key);
const fill = new THREE.DirectionalLight(0xb0a0ff, 0.45);
fill.position.set(-2, 1.5, 1); scene.add(fill);
const rim = new THREE.DirectionalLight(0x7060ff, 0.4);
rim.position.set(0, 2, -3); scene.add(rim);

// ── Avatar load ────────────────────────────────────────────────
let avatar=null, morphMesh=null, morphDict={};
const loader = new GLTFLoader();
loader.load('/static/avatar.glb', gltf=>{
  avatar = gltf.scene;
  scene.add(avatar);
  avatar.traverse(o=>{
    if(o.isMesh && o.morphTargetDictionary &&
       Object.keys(o.morphTargetDictionary).length > 0){
      if(!morphMesh || Object.keys(o.morphTargetDictionary).length > Object.keys(morphDict).length){
        morphMesh = o; morphDict = o.morphTargetDictionary;
      }
    }
  });
  console.log('[avatar] Morphs:', Object.keys(morphDict).join(', '));
  setStatus('ready');
}, null, err=>{
  console.error(err);
  showToast('Avatar load error: ' + err.message);
});

function setMorph(name, val){
  if(!morphMesh) return;
  const i = morphDict[name]; if(i===undefined) return;
  morphMesh.morphTargetInfluences[i] = Math.max(0, Math.min(1, val));
}

// ── Idle animations ────────────────────────────────────────────
let blinkTimer=3, blinkPhase='open', blinkT=0;
let eyeTarget={x:0,y:0}, eyeCur={x:0,y:0}, eyeDriftT=2;
let breatheT=0;

function idleUpdate(dt){
  if(!morphMesh) return;
  // Blinking
  blinkTimer -= dt;
  if(blinkTimer <= 0){blinkPhase='closing';blinkT=0;blinkTimer=3+Math.random()*4;}
  if(blinkPhase !== 'open'){
    blinkT += dt/0.07;
    const w = blinkPhase==='closing' ? Math.min(blinkT,1) : 1-Math.min(blinkT,1);
    setMorph('eyeBlinkLeft',w); setMorph('eyeBlinkRight',w);
    if(blinkT >= 1){
      if(blinkPhase==='closing'){blinkPhase='opening';blinkT=0;}
      else{blinkPhase='open';setMorph('eyeBlinkLeft',0);setMorph('eyeBlinkRight',0);}
    }
  }
  // Eye drift
  eyeDriftT -= dt;
  if(eyeDriftT <= 0){
    eyeTarget.x=(Math.random()-.5)*.35; eyeTarget.y=(Math.random()-.5)*.18;
    eyeDriftT=2+Math.random()*3;
  }
  eyeCur.x += (eyeTarget.x-eyeCur.x)*dt*3;
  eyeCur.y += (eyeTarget.y-eyeCur.y)*dt*3;
  setMorph('eyeLookInLeft',   Math.max(0,  eyeCur.x));
  setMorph('eyeLookOutRight', Math.max(0,  eyeCur.x));
  setMorph('eyeLookUpLeft',   Math.max(0,  eyeCur.y));
  setMorph('eyeLookDownLeft', Math.max(0, -eyeCur.y));
  // Subtle breathe
  breatheT += dt*0.35;
  if(avatar) avatar.position.y = Math.sin(breatheT)*0.002;
}

// ── Lip sync ──────────────────────────────────────────────────
const LIP_MORPHS = [
  'viseme_PP','viseme_FF','viseme_TH','viseme_DD','viseme_kk',
  'viseme_CH','viseme_SS','viseme_nn','viseme_RR','viseme_aa',
  'viseme_E','viseme_I','viseme_O','viseme_U','jawOpen'
];
let visQ=[], visStart=0, lipPlaying=false;

function lipsyncUpdate(){
  if(!lipPlaying || !morphMesh) return;
  const elapsed = (performance.now() - visStart)/1000;
  const active = {};
  for(const ev of visQ)
    if(elapsed >= ev.t && elapsed < ev.t+ev.dur) active[ev.vis]=1;
  for(const m of LIP_MORPHS){
    const i=morphDict[m]; if(i===undefined) continue;
    const target = active[m]||0;
    morphMesh.morphTargetInfluences[i] = morphMesh.morphTargetInfluences[i]*0.65 + target*0.35;
  }
  if(visQ.length){
    const last=visQ[visQ.length-1];
    if(elapsed > last.t+last.dur+0.3){
      lipPlaying=false;
      for(const m of LIP_MORPHS) setMorph(m,0);
    }
  }
}

// ── Emotion ───────────────────────────────────────────────────
const EMO_MORPHS=['mouthSmile','mouthFrownLeft','mouthFrownRight',
  'browDownLeft','browDownRight','browInnerUp',
  'eyeWideLeft','eyeWideRight','cheekSquintLeft','cheekSquintRight'];
const EMO_ICONS={happy:'😊',sad:'😢',angry:'😠',surprised:'😲',neutral:'😌'};
let eTarget={}, eCur={};

function emotionUpdate(dt){
  if(!morphMesh) return;
  for(const m of EMO_MORPHS){
    const i=morphDict[m]; if(i===undefined) continue;
    if(eCur[m]===undefined) eCur[m]=0;
    eCur[m] += ((eTarget[m]||0)-eCur[m])*dt*2;
    morphMesh.morphTargetInfluences[i]=eCur[m];
  }
}

// ── Render loop ───────────────────────────────────────────────
let lastT=performance.now();
function animate(){
  requestAnimationFrame(animate);
  const now=performance.now();
  const dt=Math.min((now-lastT)/1000,0.1); lastT=now;
  idleUpdate(dt); lipsyncUpdate(); emotionUpdate(dt);
  renderer.render(scene,camera);
}
animate();

// ── Mic recording (click toggle) ──────────────────────────────
const micBtn = document.getElementById('mic-btn');
let mediaRec=null, audioChunks=[], micStream=null, recActive=false;

micBtn.addEventListener('click', ()=>{
  if(micBtn.classList.contains('busy')) return;
  if(recActive) stopRec(); else startRec();
});

async function startRec(){
  try{
    micStream = await navigator.mediaDevices.getUserMedia({audio:true});
    audioChunks = [];
    mediaRec = new MediaRecorder(micStream);
    mediaRec.ondataavailable = e=>audioChunks.push(e.data);
    mediaRec.onstop = onRecStop;
    mediaRec.start();
    recActive = true;
    micBtn.classList.add('recording');
    micBtn.textContent = '⏹';
    document.querySelector('.mic-hint').textContent = 'Click to stop';
  }catch(err){showToast('Mic error: '+err.message);}
}

function stopRec(){
  if(!mediaRec||mediaRec.state==='inactive') return;
  mediaRec.stop();
  micStream.getTracks().forEach(t=>t.stop());
  recActive=false;
  micBtn.classList.remove('recording');
  micBtn.textContent='🎤';
  document.querySelector('.mic-hint').textContent='Click to talk';
}

async function onRecStop(){
  const blob = new Blob(audioChunks);
  if(blob.size < 1000){showToast('Recording too short');return;}
  setBusy(true);
  const fd = new FormData(); fd.append('audio',blob);
  try{
    const res = await fetch('/listen',{method:'POST',body:fd});
    handleReply(await res.json());
  }catch(err){showToast('Error: '+err.message);}
  finally{setBusy(false);}
}

// ── Text send ─────────────────────────────────────────────────
document.getElementById('send-btn').addEventListener('click', sendText);
document.getElementById('text-input').addEventListener('keydown', e=>{
  if(e.key==='Enter') sendText();
});

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
  }catch(err){showToast('Error: '+err.message);}
  finally{setBusy(false);}
}

// ── Handle server reply ───────────────────────────────────────
function handleReply(data){
  if(data.error){showToast(data.error);return;}
  if(data.transcript) showTranscript(data.transcript);
  showSubtitle(data.reply||'');
  if(data.emotion){
    eTarget = {...(data.weights||{})};
    document.getElementById('emotion-badge').textContent =
      (EMO_ICONS[data.emotion]||'😌')+' '+data.emotion.toUpperCase();
  }
  if(data.audio_base64){
    playAudio(data.audio_base64, data.visemes||[]);
  }
}

function playAudio(b64, visemes){
  const buf = b64ToBuffer(b64);
  const actx = new AudioContext();
  actx.decodeAudioData(buf, ab=>{
    const src = actx.createBufferSource();
    src.buffer = ab;
    src.connect(actx.destination);
    // Sync viseme start to audio start precisely
    src.onended = ()=>{ lipPlaying=false; for(const m of LIP_MORPHS) setMorph(m,0); };
    visQ = visemes;
    src.start(0);
    visStart = performance.now();
    lipPlaying = true;
  });
}

// ── UI helpers ────────────────────────────────────────────────
function showTranscript(t){
  const el=document.getElementById('transcript-badge');
  el.textContent='🗣 '+t; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),5000);
}
function showSubtitle(t){
  const el=document.getElementById('subtitle');
  el.textContent=t; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),8000);
}
function showToast(m){
  const el=document.getElementById('toast');
  el.textContent='⚠ '+m; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'),4000);
}
function setBusy(b){
  micBtn.classList.toggle('busy',b);
  document.getElementById('send-btn').disabled=b;
  document.getElementById('proc-ring').classList.toggle('show',b);
  setStatus(b?'busy':'ready');
}
function setStatus(s){
  const d=document.getElementById('status-dot');
  d.className='status-dot'+(s?' '+s:'');
}
function b64ToBuffer(b64){
  const bin=atob(b64),buf=new ArrayBuffer(bin.length),v=new Uint8Array(buf);
  for(let i=0;i<bin.length;i++) v[i]=bin.charCodeAt(i);
  return buf;
}
</script>
</body>
</html>"""


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
    if not message:
        return jsonify({"error": "No message."}), 400
    return _run_pipeline_from_text(message, "en")

def _run_pipeline(audio_path: str):
    try:
        transcript, language = stt.transcribe(audio_path)
        if not transcript:
            return jsonify({"error": "No speech detected."}), 422
        return _run_pipeline_from_text(transcript, language)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def _run_pipeline_from_text(transcript: str, language: str):
    try:
        reply       = llm.generate_reply(transcript, language)
        wav_path    = tts.synthesise(reply, language)
        viseme_evts = lipsync.extract_visemes(wav_path)
        emotion     = emotions.detect_emotion(reply)
        with open(wav_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        pathlib.Path(wav_path).unlink(missing_ok=True)
        return jsonify({
            "transcript": transcript,
            "reply":      reply,
            "audio_base64": audio_b64,
            "visemes":    viseme_evts,
            "emotion":    emotion["emotion"],
            "weights":    emotion["weights"],
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n  Aisha AI Avatar -> http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=False)
