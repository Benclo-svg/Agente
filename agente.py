import os
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests

# ====== CONFIGURAÇÃO ======
API_KEY = os.environ.get("GOOGLE_API_KEY")
CX = os.environ.get("GOOGLE_CX")

# ⚠️ Evita travar o deploy se variáveis não existirem (Render às vezes carrega depois)
if not API_KEY or not CX:
    print("⚠️ Aviso: GOOGLE_API_KEY ou GOOGLE_CX não configuradas. Verifique nas variáveis de ambiente do Render.")

app = Flask(__name__)
CORS(app)  # ✅ Permite chamadas do Hostinger Horizon (CORS liberado)

# ====== FUNÇÕES PRINCIPAIS ======
def google_search(query, num=5):
    """Faz a chamada à API do Google Custom Search."""
    url = "https://www.googleapis.com/customsearch/v1"
    params = {"key": API_KEY, "cx": CX, "q": query, "num": num}
    r = requests.get(url, params=params)
    r.raise_for_status()
    return r.json()

def responder_pergunta(pergunta):
    """Mapeia perguntas estratégicas para queries filtradas e retorna resultados."""
    pergunta = pergunta.lower()

    # ====== MAPEAMENTO DE PERGUNTAS ======
    if "marcas em alta" in pergunta and "google" in pergunta:
        query = '"marcas alimentícias em alta" site:trends.google.com.br OR site:thinkwithgoogle.com'
    elif "produto alimentício" in pergunta and "sudeste" in pergunta:
        query = '"produto alimentício em alta" site:trends.google.com.br inurl:SE'
    elif "marca pode crescer" in pergunta:
        query = '"marca tendência crescimento" site:trends.google.com.br OR site:foodconnection.com.br'
    elif "categoria está saturada" in pergunta or "categoria em ascensão" in pergunta:
        query = '"categoria alimentícia em ascensão OR saturada" site:trends.google.com.br'
    elif "marcas regionais" in pergunta and "sul" in pergunta:
        query = '"marcas alimentícias em alta" site:trends.google.com.br inurl:Sul'
    elif "pico de interesse" in pergunta or "cresceram mais" in pergunta:
        query = '"marcas alimentícias tendência" site:trends.google.com.br'
    else:
        query = pergunta  # fallback: busca direta

    # ====== BUSCA ======
    res = google_search(query, num=5)
    resultados = [
        {"title": item.get("title"), "link": item.get("link"), "snippet": item.get("snippet")}
        for item in res.get("items", [])
    ]
    return resultados

# ====== ENDPOINTS ======
@app.route("/")
def home():
    """Endpoint de status"""
    return jsonify({
        "status": "online ✅",
        "mensagem": "Agente Dourado ativo e pronto para responder perguntas!",
        "endpoints": {
            "perguntas": "/pergunta (POST)"
        }
    })

@app.route("/pergunta", methods=["POST"])
def pergunta_endpoint():
    """Recebe uma pergunta e retorna resultados do Google Custom Search."""
    data = request.get_json()
    if not data or "pergunta" not in data:
        return jsonify({"erro": "Campo 'pergunta' é obrigatório no corpo JSON."}), 400

    pergunta = data["pergunta"]

    try:
        respostas = responder_pergunta(pergunta)
        return jsonify({
            "pergunta": pergunta,
            "quantidade_resultados": len(respostas),
            "respostas": respostas
        })
    except Exception as e:
        print(f"❌ Erro ao processar pergunta: {e}")
        return jsonify({"erro": str(e)}), 500

# ====== EXECUÇÃO LOCAL / RENDER ======
if __name__ == "__main__":
    # ✅ Corrigido: Render usa a porta 5000 automaticamente
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
