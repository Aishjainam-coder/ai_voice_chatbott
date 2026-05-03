"""
main.py — Flask Server + Embedded Face-Only Avatar UI
"""

import os, base64, pathlib, concurrent.futures, time, shutil
from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# ── Force FFmpeg and fix OMP conflict ────────────────────────
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
ffmpeg_path = r"C:\ffmpeg\ffmpeg-8.1-essentials_build\bin"
if ffmpeg_path not in os.environ["PATH"]:
    os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ["PATH"]

if shutil.which("ffmpeg"):
    print(f"[system] FFmpeg found at: {shutil.which('ffmpeg')}")

import stt
import llm
import tts
import lipsync
import emotions

app = Flask(__name__, static_folder="static", static_url_path="/static")
CORS(app)

_TEMP_DIR = pathlib.Path(os.getenv("TTS_OUTPUT_DIR", "temp_audio"))
_TEMP_DIR.mkdir(parents=True, exist_ok=True)

# ── Welcome message text (Hinglish) ─────────────────────────
_WELCOME_TEXT = (
    "Hi… I’m Aishwarya, your personalized AI avatar. I learn from how you interact and respond accordingly — making every conversation feel real."
)
_WELCOME_LANGUAGE = "hi"

AVATAR_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1.0"/>
<title>Aishwarya — AI Avatar</title>
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
#app{
  position:relative;z-index:1;
  width:100%;max-width:1200px;
  display:grid;grid-template-columns:1fr 400px;
  gap:0;height:100vh;
  background:rgba(6,6,16,0.4);
  backdrop-filter:blur(10px);
}
#face-wrap{
  width: 380px; height: 380px;
  margin: 30px auto;
  position: relative;
  overflow: hidden;
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.12);
  display: flex; align-items: center; justify-content: center;
}
#three-canvas{width:100%;height:100%;display:block;border-radius: 30px;}
#chat-container {
  background: rgba(255, 255, 255, 0.03);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  display: flex; flex-direction: column; height: 100vh; overflow: hidden;
}
#chat-history {
  flex: 1; overflow-y: auto; padding: 20px;
  display: flex; flex-direction: column; gap: 12px;
}
.msg {
  max-width: 85%; padding: 10px 14px; border-radius: 15px; font-size: 0.9rem;
}
.msg.user { align-self: flex-end; background: var(--accent); color: white; }
.msg.aishwarya { align-self: flex-start; background: rgba(255, 255, 255, 0.1); color: var(--text); }
#bottom{
  padding:14px 20px 22px; display:flex; flex-direction:column; align-items:center; gap:12px;
}
#text-row{ display:flex; gap:8px; width:100%; }
#text-input{
  flex:1; background:rgba(255,255,255,.06); border:1px solid rgba(255,255,255,.1);
  border-radius:12px; padding:11px 15px; color:var(--text); outline:none;
}
#send-btn{
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  border:none; border-radius:12px; padding:11px 18px; color:#fff; cursor:pointer;
}
#mic-btn{
  width:68px; height:68px; border-radius:50%; border:none; cursor:pointer;
  background:linear-gradient(135deg,var(--accent),var(--accent2));
  display:flex; align-items:center; justify-content:center; font-size:26px;
}
#proc-ring{
  width:22px; height:22px; border:2.5px solid rgba(255,255,255,.15);
  border-top-color:var(--accent); border-radius:50%; display:none; animation:spin .7s linear infinite;
}
#proc-ring.show{display:block;}
@keyframes spin{to{transform:rotate(360deg)}}
#toast{
  position:fixed; bottom:20px; right:20px; padding:11px 18px; background:#200814;
  border:1px solid var(--red); border-radius:12px; color:var(--red); opacity:0; transition:all .3s;
}
#toast.show{opacity:1;}
#status-dot{ width:8px; height:8px; border-radius:50%; background:var(--sub); margin-left:auto; }
#status-dot.ready{background:var(--green);}
#status-dot.busy{background:var(--accent); animation:blink 1s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
#emotion-badge{
  position:absolute; top:10px; right:14px; padding:5px 11px; border-radius:18px;
  font-size:.72rem; background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
}
</style>
</head>
<body>
<div id="app">
  <div id="left-pane" style="display:flex; flex-direction:column; height:100vh; overflow:hidden;">
    <header style="width:100%;padding:18px 24px 10px;display:flex;align-items:center;gap:10px;">
      <div style="width:38px;height:38px;border-radius:50%;background:linear-gradient(135deg,var(--accent),var(--accent2));display:flex;align-items:center;justify-content:center;">✨</div>
      <h1>Aishwarya</h1>
      <div class="status-dot" id="status-dot"></div>
      <div id="emotion-badge">Neutral 😌</div>
    </header>
    <div id="face-wrap"><canvas id="three-canvas"></canvas></div>
    <div id="bottom">
      <div id="text-row">
        <input id="text-input" type="text" placeholder="Type a message…"/>
        <button id="send-btn">Send ↗</button>
      </div>
      <div style="display:flex;align-items:center;gap:18px;">
        <button id="mic-btn">🎤</button>
        <div id="proc-ring"></div>
      </div>
    </div>
  </div>
  <div id="chat-container"><div id="chat-history"></div></div>
</div>
<div id="toast"></div>

<script type="importmap">
{ "imports": { "three": "https://cdn.jsdelivr.net/npm/three@0.158.0/build/three.module.js", "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.158.0/examples/jsm/" } }
</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';

const canvas=document.getElementById('three-canvas'), renderer=new THREE.WebGLRenderer({canvas,antialias:true,alpha:true});
renderer.setSize(380,380); const scene=new THREE.Scene(), camera=new THREE.PerspectiveCamera(35,1,0.1,100);
camera.position.set(0,1.58,1.15); camera.lookAt(0,1.62,0);
scene.add(new THREE.AmbientLight(0xffffff,1.1));
const key=new THREE.DirectionalLight(0xffffff,1.6); key.position.set(1.5,3,2.5); scene.add(key);

let avatar=null, morphMesh=null, morphDict={}, isRecording=false;
let leftEye=null, rightEye=null;

new GLTFLoader().load('/static/avatar.glb', gltf=>{
  avatar=gltf.scene; scene.add(avatar);
  avatar.traverse(o=>{
    if(o.isMesh && o.morphTargetDictionary){
      if(!morphMesh || Object.keys(o.morphTargetDictionary).length > Object.keys(morphDict).length){
        morphMesh=o; morphDict=o.morphTargetDictionary;
        console.log("Avatar Morph Targets:", Object.keys(morphDict));
      }
    }
    if(o.name.toLowerCase().includes('eye')){
       if(o.name.toLowerCase().includes('left')) leftEye = o;
       if(o.name.toLowerCase().includes('right')) rightEye = o;
    }
  });
  document.getElementById('status-dot').className='status-dot ready';

  // ── WELCOME: avatar speaks as soon as model is loaded ──────
  // Small delay so the scene fully settles before audio starts
  setTimeout(playWelcome, 800);
});

// ── Welcome function — calls /welcome endpoint ──────────────
async function playWelcome(){
  try {
    setBusy(true);
    const res  = await fetch('/welcome');
    const data = await res.json();
    if(data.error){ console.warn('[welcome] error:', data.error); setBusy(false); return; }
    // Show her greeting in chat
    addMsg('aishwarya', data.reply);
    // Play audio + lipsync + emotion — same as any normal reply
    if(data.audio_base64) playAudio(data.audio_base64, data.visemes);
    if(data.emotion) document.getElementById('emotion-badge').textContent=data.emotion.toUpperCase()+' 😊';
    if(data.weights) targetWeights = data.weights;
    setBusy(false);
  } catch(e){
    console.error('[welcome] fetch failed:', e);
    setBusy(false);
  }
}

let targetWeights = {};
function setMorph(n,v){ if(morphMesh && morphDict[n]!==undefined) morphMesh.morphTargetInfluences[morphDict[n]]=v; }

let visQ=[], visStart=0, lipPlaying=false;
function lipsyncUpdate(){
  if(!lipPlaying || !morphMesh) return;
  const elapsed=(performance.now()-visStart)/1000; const active={};
  for(const ev of visQ) if(elapsed>=ev.t && elapsed<ev.t+ev.dur) active[ev.vis]=ev.weight||1;
  for(const m in morphDict) if(m.startsWith('viseme_')||m==='jawOpen'||m==='mouthRollUpper'||m==='mouthRollLower'||m==='mouthClose'||m==='mouthPressLeft'||m==='mouthPressRight') setMorph(m, active[m]||0);
  if(visQ.length && elapsed>visQ[visQ.length-1].t+visQ[visQ.length-1].dur+0.3) lipPlaying=false;
}

// ═══════════════════════════════════════════════════════════
// ANIMATION SYSTEM — Natural Human Feel
// ═══════════════════════════════════════════════════════════

let avatarState = 'idle';

// ── Blink ────────────────────────────────────────────────────
let blinkVal=0, blinkPhase=0, nextBlink=2500, pendingDouble=false;
function blinkUpdate(){
  if(!morphMesh) return;
  const now = performance.now();
  if(now > nextBlink && blinkPhase===0){
    blinkPhase=1;
    if(Math.random()<0.12) pendingDouble=true;
  }
  if(blinkPhase===1){ blinkVal+=0.13; if(blinkVal>=1){blinkVal=1;blinkPhase=2;} }
  else if(blinkPhase===2){
    blinkVal-=0.17;
    if(blinkVal<=0){
      blinkVal=0; blinkPhase=0;
      if(pendingDouble){ pendingDouble=false; nextBlink=now+160; }
      else { nextBlink = now+2800+Math.random()*3500; }
    }
  }
  setMorph('eyeBlinkLeft',  blinkVal);
  setMorph('eyeBlinkRight', blinkVal);
  const sq = (1-blinkVal)*0.07;
  setMorph('eyeSquintLeft',  sq);
  setMorph('eyeSquintRight', sq);
}

// ── Emotion morph lerp ───────────────────────────────────────
function emotionUpdate(){
  if(!morphMesh) return;
  for(const m in targetWeights){
    if(m.startsWith('viseme_')||m==='jawOpen') continue;
    const idx=morphDict[m]; if(idx===undefined) continue;
    const cur=morphMesh.morphTargetInfluences[idx];
    morphMesh.morphTargetInfluences[idx] += (targetWeights[m]-cur)*0.06;
  }
}

// ── Eye gaze ─────────────────────────────────────────────────
let eyeTargetX=0, eyeTargetY=0, eyeCurX=0, eyeCurY=0, nextEyeShift=0;
function lookUpdate(){
  if(!leftEye||!rightEye) return;
  const now=performance.now();
  if(now>nextEyeShift){
    if(avatarState==='listening'){
      eyeTargetX=0; eyeTargetY=0;
      nextEyeShift=now+2000;
    } else if(avatarState==='thinking'){
      eyeTargetX=(Math.random()-0.5)*0.14;
      eyeTargetY=-0.04-Math.random()*0.04;
      nextEyeShift=now+600+Math.random()*800;
    } else if(avatarState==='speaking'){
      eyeTargetX=(Math.random()-0.5)*0.07;
      eyeTargetY=(Math.random()-0.5)*0.04;
      nextEyeShift=now+500+Math.random()*1200;
    } else {
      eyeTargetX=(Math.random()-0.5)*0.09;
      eyeTargetY=(Math.random()-0.5)*0.05;
      nextEyeShift=now+2200+Math.random()*3000;
    }
  }
  eyeCurX += (eyeTargetX-eyeCurX)*0.07;
  eyeCurY += (eyeTargetY-eyeCurY)*0.07;
  leftEye.rotation.y  = eyeCurX; leftEye.rotation.x  = eyeCurY;
  rightEye.rotation.y = eyeCurX; rightEye.rotation.x = eyeCurY;
}

// ── Head motion ──────────────────────────────────────────────
let hCurX=0,hCurY=0,hCurZ=0, hTgtX=0,hTgtY=0,hTgtZ=0, nextHeadShift=0;
let nodActive=false, nodPhase=0;

function headUpdate(){
  if(!avatar) return;
  const now=performance.now();
  if(now>nextHeadShift){
    if(avatarState==='listening'){
      hTgtX= 0.010+Math.random()*0.006;
      hTgtY=(Math.random()-0.5)*0.010;
      hTgtZ=(Math.random()-0.5)*0.008;
      nextHeadShift=now+2500+Math.random()*2000;
    } else if(avatarState==='thinking'){
      hTgtX= 0.014+Math.random()*0.006;
      hTgtY=(Math.random()-0.5)*0.016;
      hTgtZ= 0.008+Math.random()*0.008;
      nextHeadShift=now+700+Math.random()*800;
    } else if(avatarState==='speaking'){
      hTgtX=(Math.random()-0.5)*0.018;
      hTgtY=(Math.random()-0.5)*0.020;
      hTgtZ=(Math.random()-0.5)*0.012;
      nextHeadShift=now+500+Math.random()*900;
    } else {
      hTgtX=(Math.random()-0.5)*0.010;
      hTgtY=(Math.random()-0.5)*0.012;
      hTgtZ=(Math.random()-0.5)*0.007;
      nextHeadShift=now+3000+Math.random()*3000;
    }
  }
  const spd = avatarState==='speaking' ? 0.016 : 0.008;
  hCurX+=(hTgtX-hCurX)*spd;
  hCurY+=(hTgtY-hCurY)*spd;
  hCurZ+=(hTgtZ-hCurZ)*spd;
  let nodOffset=0;
  if(nodActive){
    nodPhase+=0.10;
    nodOffset = Math.sin(nodPhase)*0.022;
    if(nodPhase>Math.PI) nodActive=false;
  }
  avatar.rotation.x = hCurX + nodOffset;
  avatar.rotation.y = hCurY;
  avatar.rotation.z = hCurZ;
}

function triggerNod(){ nodActive=true; nodPhase=0; }

// ── Micro expressions ─────────────────────────────────────────
function microUpdate(){
  if(!morphMesh) return;
  const jawNow = morphDict['jawOpen']!==undefined
    ? morphMesh.morphTargetInfluences[morphDict['jawOpen']] : 0;
  if(avatarState==='speaking'){
    const brow = jawNow*0.30;
    _lerp('browInnerUp',     brow,     0.08);
    _lerp('browOuterUpLeft', brow*0.5, 0.08);
    _lerp('browOuterUpRight',brow*0.5, 0.08);
    _lerp('cheekSquintLeft', jawNow*0.18, 0.08);
    _lerp('cheekSquintRight',jawNow*0.18, 0.08);
  } else if(avatarState==='thinking'){
    _lerp('browInnerUp',      0.12, 0.04);
    _lerp('browOuterUpLeft',  0.06, 0.04);
    _lerp('browOuterUpRight', 0.02, 0.04);
    _lerp('cheekSquintLeft',  0,    0.04);
    _lerp('cheekSquintRight', 0,    0.04);
  } else {
    _lerp('browInnerUp',      0, 0.03);
    _lerp('browOuterUpLeft',  0, 0.03);
    _lerp('browOuterUpRight', 0, 0.03);
    _lerp('cheekSquintLeft',  0, 0.03);
    _lerp('cheekSquintRight', 0, 0.03);
  }
}

function _lerp(name, target, speed){
  if(!morphMesh||morphDict[name]===undefined) return;
  const i=morphDict[name];
  morphMesh.morphTargetInfluences[i]+=(target-morphMesh.morphTargetInfluences[i])*speed;
}

// ── Breathing ─────────────────────────────────────────────────
function breathUpdate(){
  if(!avatar) return;
  const t=performance.now()*0.001;
  avatar.position.y = Math.sin(t*0.40)*0.0022;
}

// ── Thinking animation ────────────────────────────────────────
let thinkTimer=null;
function startThinking(){
  avatarState='thinking';
  eyeTargetX=0.08; eyeTargetY=-0.05; nextEyeShift=performance.now()+9999;
}
function stopThinking(){ clearTimeout(thinkTimer); }

// ── Main render loop ──────────────────────────────────────────
function idleUpdate(){
  breathUpdate(); blinkUpdate(); lookUpdate(); headUpdate(); microUpdate();
}
function animate(){
  requestAnimationFrame(animate);
  idleUpdate(); emotionUpdate(); lipsyncUpdate();
  renderer.render(scene,camera);
}
animate();

// ── Mic button ────────────────────────────────────────────────
const micBtn=document.getElementById('mic-btn'); let mediaRec=null, audioChunks=[];
micBtn.onclick=async()=>{
  if(mediaRec && mediaRec.state==='recording'){ mediaRec.stop(); micBtn.style.background=''; isRecording=false; return; }
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});
  mediaRec=new MediaRecorder(stream); audioChunks=[]; isRecording=true;
  mediaRec.ondataavailable=e=>audioChunks.push(e.data);
  mediaRec.onstop=async()=>{
    isRecording=false; micBtn.style.background='';
    startThinking();
    const fd=new FormData(); fd.append('audio',new Blob(audioChunks));
    setBusy(true);
    const r=await fetch('/listen',{method:'POST',body:fd}); handleReply(await r.json());
    setBusy(false); stopThinking();
  };
  mediaRec.start(); micBtn.style.background='red'; avatarState='listening';
};

// ── Send button ───────────────────────────────────────────────
document.getElementById('send-btn').onclick=async()=>{
  const inp=document.getElementById('text-input'), m=inp.value.trim(); if(!m) return;
  inp.value=''; startThinking(); setBusy(true);
  const r=await fetch('/text',{method:'POST',body:JSON.stringify({message:m}),headers:{'Content-Type':'application/json'}});
  handleReply(await r.json()); stopThinking(); setBusy(false);
};

// ── Enter key to send ─────────────────────────────────────────
document.getElementById('text-input').addEventListener('keydown', async(e)=>{
  if(e.key !== 'Enter') return;
  const inp=document.getElementById('text-input'), m=inp.value.trim(); if(!m) return;
  inp.value=''; startThinking(); setBusy(true);
  const r=await fetch('/text',{method:'POST',body:JSON.stringify({message:m}),headers:{'Content-Type':'application/json'}});
  handleReply(await r.json()); stopThinking(); setBusy(false);
});

// ── Shared helpers ────────────────────────────────────────────
function handleReply(d){
  if(d.error){ showToast(d.error); return; }
  if(d.transcript) addMsg('user',d.transcript);
  if(d.reply) addMsg('aishwarya',d.reply);
  if(d.audio_base64) playAudio(d.audio_base64, d.visemes);
  if(d.emotion) document.getElementById('emotion-badge').textContent=d.emotion.toUpperCase();
  if(d.weights) targetWeights = d.weights;
}
function addMsg(r,t){
  const h=document.getElementById('chat-history'), d=document.createElement('div');
  d.className='msg '+r; d.textContent=t; h.appendChild(d); h.scrollTop=h.scrollHeight;
}
function playAudio(b,v){
  const buf=b64ToBuf(b), actx=new AudioContext();
  actx.decodeAudioData(buf, ab=>{
    const s=actx.createBufferSource(); s.buffer=ab; s.connect(actx.destination);
    avatarState='speaking'; triggerNod();
    visQ=v; s.start(0); visStart=performance.now(); lipPlaying=true;
    s.onended=()=>{ lipPlaying=false; avatarState='idle'; };
  });
}
function b64ToBuf(b){ const s=atob(b),buf=new ArrayBuffer(s.length),v=new Uint8Array(buf); for(let i=0;i<s.length;i++)v[i]=s.charCodeAt(i); return buf; }
function setBusy(b){ document.getElementById('proc-ring').classList.toggle('show',b); document.getElementById('status-dot').className='status-dot '+(b?'busy':'ready'); }
function showToast(m){ const e=document.getElementById('toast'); e.textContent=m; e.classList.add('show'); setTimeout(()=>e.classList.remove('show'),3000); }
</script>
</body>
</html>"""

# ── Internal Pipeline Functions ──────────────────────────────

def _run_pipeline_from_text(transcript: str, language: str):
    try:
        print(f"[pipeline] Processing text: {transcript[:50]}...")
        t0 = time.time()

        t_llm_start = time.time()
        reply, llm_emotion = llm.generate_reply(transcript, language)
        print(f"[timer] LLM took: {time.time() - t_llm_start:.2f}s")

        t_parallel_start = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_tts     = executor.submit(tts.synthesise, reply, language)
            future_emotion = executor.submit(emotions.detect_emotion, reply, llm_emotion)
            wav_path     = future_tts.result()
            emotion_data = future_emotion.result()
        print(f"[timer] TTS + Emotion took: {time.time() - t_parallel_start:.2f}s")

        t_lipsync_start = time.time()
        viseme_evts = lipsync.extract_visemes(wav_path)
        print(f"[timer] Lip-sync took: {time.time() - t_lipsync_start:.2f}s")

        with open(wav_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        pathlib.Path(wav_path).unlink(missing_ok=True)

        print(f"[timer] TOTAL TURNAROUND: {time.time() - t0:.2f}s")

        return jsonify({
            "transcript":   transcript,
            "reply":        reply,
            "audio_base64": audio_b64,
            "visemes":      viseme_evts,
            "emotion":      emotion_data["emotion"],
            "weights":      emotion_data["weights"],
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


def _run_pipeline(audio_path: str):
    try:
        print(f"\n[pipeline] --- NEW REQUEST ---")
        t_stt_start = time.time()
        transcript, language = stt.transcribe(audio_path)
        print(f"[timer] STT took: {time.time() - t_stt_start:.2f}s")
        if not transcript:
            print(f"[pipeline] No speech detected.")
            return jsonify({"error": "No speech detected."}), 422
        return _run_pipeline_from_text(transcript, language)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500


# ── NEW: Welcome endpoint ─────────────────────────────────────
def _build_welcome_response():
    """
    Pre-generate the welcome audio + visemes using TTS + lipsync.
    Bypasses the LLM entirely — no delay, instant on load.
    """
    try:
        print("[welcome] Generating welcome message...")
        t0 = time.time()

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_tts     = executor.submit(tts.synthesise, _WELCOME_TEXT, _WELCOME_LANGUAGE, "welcome.wav")
            future_emotion = executor.submit(emotions.detect_emotion, _WELCOME_TEXT, "happy")
            wav_path     = future_tts.result()
            emotion_data = future_emotion.result()

        viseme_evts = lipsync.extract_visemes(wav_path)

        with open(wav_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        pathlib.Path(wav_path).unlink(missing_ok=True)

        print(f"[welcome] Ready in {time.time() - t0:.2f}s")
        return {
            "reply":        _WELCOME_TEXT,
            "audio_base64": audio_b64,
            "visemes":      viseme_evts,
            "emotion":      emotion_data["emotion"],
            "weights":      emotion_data["weights"],
        }
    except Exception as e:
        import traceback; traceback.print_exc()
        return None


# Pre-build welcome at startup so first load is instant
print("[welcome] Pre-generating welcome audio at startup...")
_WELCOME_CACHE = _build_welcome_response()


# ── Routes ───────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template_string(AVATAR_HTML)

@app.route("/static/<path:filename>")
def serve_static(filename):
    return send_from_directory("static", filename)

@app.route("/welcome", methods=["GET"])
def welcome():
    """Called by the frontend once the avatar GLB is loaded."""
    if _WELCOME_CACHE:
        return jsonify(_WELCOME_CACHE)
    # fallback: generate on the fly if startup cache failed
    data = _build_welcome_response()
    if data:
        return jsonify(data)
    return jsonify({"error": "Welcome generation failed."}), 500

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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n  Aishwarya AI Avatar -> http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)