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
});

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

let blinkVal=0, blinkStep=0, nextBlink=0;
function blinkUpdate(){
  if(!morphMesh) return; const now=performance.now();
  if(now>nextBlink && blinkStep===0) blinkStep=1;
  if(blinkStep===1){ blinkVal+=0.25; if(blinkVal>=1){ blinkVal=1; blinkStep=2; } }
  else if(blinkStep===2){ blinkVal-=0.25; if(blinkVal<=0){ blinkVal=0; blinkStep=0; nextBlink=now+2000+Math.random()*4000; } }
  setMorph('eyeBlinkLeft', blinkVal); setMorph('eyeBlinkRight', blinkVal);
}

function emotionUpdate(){
  if(!morphMesh) return;
  for(const m in targetWeights){
    if(m.startsWith('viseme_')||m==='jawOpen') continue;
    const idx=morphDict[m]; if(idx===undefined) continue;
    const current=morphMesh.morphTargetInfluences[idx];
    morphMesh.morphTargetInfluences[idx] += (targetWeights[m]-current)*0.1;
  }
}

let eyeTargetX=0, eyeTargetY=0, nextEyeShift=0;
function lookUpdate(){
  if(!leftEye || !rightEye) return; const now=performance.now();
  if(now>nextEyeShift){
    if(lipPlaying){
      // When speaking: more frequent, smaller, and more focused eye movements
      eyeTargetX=(Math.random()-0.5)*0.1; 
      eyeTargetY=(Math.random()-0.5)*0.08;
      nextEyeShift=now+400+Math.random()*1200;
    } else {
      // Idle: slower, wider eye movements
      eyeTargetX=(Math.random()-0.5)*0.25; 
      eyeTargetY=(Math.random()-0.5)*0.15;
      nextEyeShift=now+1000+Math.random()*3000;
    }
  }
  const speed = lipPlaying ? 0.12 : 0.08; // Slightly faster reaction when speaking
  leftEye.rotation.y += (eyeTargetX-leftEye.rotation.y)*speed;
  leftEye.rotation.x += (eyeTargetY-leftEye.rotation.x)*speed;
  rightEye.rotation.y += (eyeTargetX-rightEye.rotation.y)*speed;
  rightEye.rotation.x += (eyeTargetY-rightEye.rotation.x)*speed;
}

function idleUpdate(){
  const t=performance.now()*0.001;
  if(avatar){
    avatar.position.y = Math.sin(t*0.6)*0.003;
    if(isRecording){
      avatar.rotation.y *= 0.8; avatar.rotation.x *= 0.8;
      eyeTargetX=0; eyeTargetY=0; // Look straight while listening
    } else {
      avatar.rotation.y = Math.sin(t*0.2)*0.02;
      avatar.rotation.x = Math.cos(t*0.3)*0.01;
    }
  }
  blinkUpdate();
  lookUpdate();
}

function animate(){
  requestAnimationFrame(animate);
  idleUpdate();
  emotionUpdate();
  lipsyncUpdate();
  renderer.render(scene,camera);
}
animate();

const micBtn=document.getElementById('mic-btn'); let mediaRec=null, audioChunks=[];
micBtn.onclick=async()=>{
  if(mediaRec && mediaRec.state==='recording'){ mediaRec.stop(); micBtn.style.background=''; isRecording=false; return; }
  const stream=await navigator.mediaDevices.getUserMedia({audio:true});
  mediaRec=new MediaRecorder(stream); audioChunks=[]; isRecording=true;
  mediaRec.ondataavailable=e=>audioChunks.push(e.data);
  mediaRec.onstop=async()=>{
    isRecording=false;
    const res=await fetch('/listen',{method:'POST',body:new FormData()}); // Dummy for brevity in this example, actual uses blob
    const fd=new FormData(); fd.append('audio',new Blob(audioChunks));
    setBusy(true);
    const r=await fetch('/listen',{method:'POST',body:fd}); handleReply(await r.json());
    setBusy(false);
  };
  mediaRec.start(); micBtn.style.background='red';
};

document.getElementById('send-btn').onclick=async()=>{
  const inp=document.getElementById('text-input'), m=inp.value.trim(); if(!m) return;
  inp.value=''; setBusy(true);
  const r=await fetch('/text',{method:'POST',body:JSON.stringify({message:m})});
  handleReply(await r.json()); setBusy(false);
};

function handleReply(d){
  if(d.error){ showToast(d.error); return; }
  if(d.transcript) addMsg('user',d.transcript); if(d.reply) addMsg('aishwarya',d.reply);
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
    visQ=v; visStart=performance.now(); lipPlaying=true; s.start(0);
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
        
        # Step 1: LLM Generation
        t_llm_start = time.time()
        reply, llm_emotion = llm.generate_reply(transcript, language)
        t_llm_end = time.time()
        print(f"[timer] LLM took: {t_llm_end - t_llm_start:.2f}s")

        # Step 2: Parallelize TTS Synthesis and Emotion Detection
        t_parallel_start = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_tts     = executor.submit(tts.synthesise, reply, language)
            future_emotion = executor.submit(emotions.detect_emotion, reply, llm_emotion)
            
            wav_path = future_tts.result()
            emotion_data = future_emotion.result()
        t_parallel_end = time.time()
        print(f"[timer] TTS + Emotion took: {t_parallel_end - t_parallel_start:.2f}s")

        # Step 3: Lip-sync analysis
        t_lipsync_start = time.time()
        viseme_evts = lipsync.extract_visemes(wav_path)
        t_lipsync_end = time.time()
        print(f"[timer] Lip-sync took: {t_lipsync_end - t_lipsync_start:.2f}s")

        with open(wav_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        
        pathlib.Path(wav_path).unlink(missing_ok=True)

        total_time = time.time() - t0
        print(f"[timer] TOTAL TURNAROUND: {total_time:.2f}s")

        return jsonify({
            "transcript": transcript,
            "reply":      reply,
            "audio_base64": audio_b64,
            "visemes":    viseme_evts,
            "emotion":    emotion_data["emotion"],
            "weights":    emotion_data["weights"],
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

def _run_pipeline(audio_path: str):
    try:
        t_start = time.time()
        print(f"\n[pipeline] --- NEW REQUEST ---")
        
        t_stt_start = time.time()
        transcript, language = stt.transcribe(audio_path)
        t_stt_end = time.time()
        print(f"[timer] STT took: {t_stt_end - t_stt_start:.2f}s")
        
        if not transcript:
            print(f"[pipeline] No speech detected.")
            return jsonify({"error": "No speech detected."}), 422
            
        return _run_pipeline_from_text(transcript, language)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ── Routes ───────────────────────────────────────────────────

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

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n  Aishwarya AI Avatar -> http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
