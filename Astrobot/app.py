import json, requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"
MODEL_ID       = "meta-llama-3.1-8b-instruct"

app = Flask(__name__, static_folder="frontend")
CORS(app)

def load_knowledge():
    with open("conocimiento.json", "r", encoding="utf-8") as f:
        return json.load(f)

def knowledge_to_text(k):
    lines = []
    cats  = k.get("categorias", {})
    ss    = cats.get("sistema_solar", {})
    sol   = ss.get("sol", {})
    lines.append("=== SISTEMA SOLAR ===")
    lines.append(f"El Sol: {sol.get('tipo')}, temperatura {sol.get('temperatura_superficie')}, edad {sol.get('edad')}.")
    for p in ss.get("planetas", []):
        lines.append(f"Planeta {p['nombre']}: {p['tipo']}, {p['diametro_km']} km, {p['distancia_sol_UA']} UA, {p['lunas']} lunas. {p.get('dato_curioso','')}")
    for pd_ in ss.get("planetas_enanos", []):
        lines.append(f"Planeta enano {pd_['nombre']}: {pd_['dato']}")
    est = cats.get("estrellas", {})
    lines.append("\n=== ESTRELLAS ===")
    for en in est.get("estrellas_notables", []):
        lines.append(f"{en['nombre']}: {en['dato']}")
    gal = cats.get("galaxias", {})
    vl  = gal.get("via_lactea", {})
    lines.append("\n=== GALAXIAS ===")
    lines.append(f"Via Lactea: {vl.get('tipo')}, {vl.get('diametro')}, agujero negro: {vl.get('agujero_negro_central')}.")
    lines.append(gal.get("colision_andromeda", ""))
    cos = cats.get("cosmologia", {})
    bb  = cos.get("big_bang", {})
    lines.append("\n=== COSMOLOGIA ===")
    lines.append(f"Big Bang: {bb.get('descripcion')}")
    an = cats.get("agujeros_negros", {})
    lines.append("\n=== AGUJEROS NEGROS ===")
    lines.append(an.get("descripcion", ""))
    for ej in an.get("ejemplos_famosos", []):
        lines.append(f"{ej['nombre']}: {ej['dato']}")
    exo = cats.get("exoplanetas", {})
    lines.append("\n=== EXOPLANETAS ===")
    lines.append(f"{exo.get('descripcion')} {exo.get('estadisticas')}")
    for ej in exo.get("ejemplos_notables", []):
        lines.append(f"{ej['nombre']}: {ej['dato']}")
    fen = cats.get("fenomenos_astronomicos", {})
    lines.append("\n=== FENOMENOS ===")
    for ll in fen.get("lluvia_meteoritos", []):
        lines.append(f"{ll['nombre']} ({ll['fecha']}): {ll['dato']}")
    mis = cats.get("telescopios_misiones", {})
    lines.append("\n=== MISIONES ===")
    for k2, v in mis.items():
        lines.append(f"{k2.upper()}: {v}")
    return "\n".join(lines)

def build_system_prompt(kt):
    return f"""Eres AstroBot, experto en astronomia, entusiasta y didactico.
REGLAS:
1. Solo responde sobre astronomia. Si preguntan otra cosa di: "Solo puedo ayudarte con temas de astronomia."
2. Responde SIEMPRE en espanol.
3. Se conciso: 3 a 8 oraciones con datos numericos.
4. Termina con un dato curioso fascinante.
BASE DE CONOCIMIENTO:\n{kt}"""

def call_llm(messages):
    try:
        r = requests.post(LM_STUDIO_URL, json={
            "model": MODEL_ID, "messages": messages,
            "temperature": 0.7, "max_tokens": 512, "stream": False
        }, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return "Error: LM Studio no esta corriendo. Activa el servidor en LM Studio."
    except Exception as e:
        return f"Error: {str(e)}"

knowledge     = load_knowledge()
kt            = knowledge_to_text(knowledge)
system_prompt = build_system_prompt(kt)

@app.route("/")
def index():
    return send_from_directory("frontend", "index.html")

@app.route("/chat", methods=["POST"])
def chat():
    data    = request.get_json()
    message = data.get("message", "").strip()
    history = data.get("history", [])
    if not message:
        return jsonify({"error": "Mensaje vacio"}), 400
    messages = [{"role": "system", "content": system_prompt}]
    for t in history[-10:]:
        messages.append({"role": t["role"], "content": t["content"]})
    messages.append({"role": "user", "content": message})
    reply = call_llm(messages)
    return jsonify({"reply": reply})

@app.route("/health")
def health():
    try:
        r = requests.get("http://127.0.0.1:1234/v1/models", timeout=5)
        lm = "ok" if r.status_code == 200 else "error"
    except:
        lm = "no disponible"
    return jsonify({"flask": "ok", "lm_studio": lm})

if __name__ == "__main__":
    print("AstroBot corriendo en http://localhost:5000")
    app.run(debug=False, port=5000)