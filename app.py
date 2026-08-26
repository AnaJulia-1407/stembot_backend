from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json
import re
import os

app = Flask(__name__)
CORS(app)

GROQ_KEY = os.environ.get("GROQ_API_KEY", "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")

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    user_prompt = data.get("prompt", "")

    if not user_prompt:
        return jsonify({"error": "Prompt vazio"}), 400

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "system", "content": "Você é o STEMbot, um tutor amigável de exatas e tecnologia. Responda em português de forma clara."},
                    {"role": "user", "content": user_prompt}
                ]
            }
        )
        res_data = response.json()
        
        if 'error' in res_data:
            print("\n[ERRO DA GROQ]:", res_data['error'])
            return jsonify({"error": res_data['error'].get('message', 'Erro na API')}), 400

        bot_reply = res_data['choices'][0]['message']['content']
        return jsonify({"response": bot_reply})
        
    except Exception as e:
        print("\n[ERRO INTERNO]:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/api/generate-quiz', methods=['POST'])
def generate_quiz():
    data = request.get_json()
    tema = data.get("tema", "").strip()

    if not tema:
        return jsonify({"error": "Tema vazio"}), 400

    prompt_sistema = (
        "Você gera quizzes educacionais de exatas, tecnologia e ciências em português. "
        "Responda SOMENTE com um array JSON puro, sem markdown, sem crases, sem texto antes ou depois. "
        "O array deve ter exatamente 10 objetos, cada um com as chaves: "
        "'pergunta' (string), 'opcoes' (array com exatamente 4 strings), "
        "'correta' (número inteiro de 0 a 3, índice da opção correta em 'opcoes'), "
        "'explicacao' (string curta explicando a resposta certa)."
    )

    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-20b",
                "messages": [
                    {"role": "system", "content": prompt_sistema},
                    {"role": "user", "content": f"Gere o quiz sobre o tema: {tema}"}
                ]
            }
        )
        res_data = response.json()

        if 'error' in res_data:
            print("\n[ERRO DA GROQ - QUIZ]:", res_data['error'])
            return jsonify({"error": res_data['error'].get('message', 'Erro na API')}), 400

        conteudo = res_data['choices'][0]['message']['content']

        # Remove possíveis blocos de código (```json ... ```) que o modelo às vezes adiciona
        conteudo_limpo = re.sub(r"^```(json)?|```$", "", conteudo.strip(), flags=re.MULTILINE).strip()

        try:
            quiz_gerado = json.loads(conteudo_limpo)
        except json.JSONDecodeError:
            print("\n[ERRO DE FORMATO - QUIZ]:", conteudo)
            return jsonify({"error": "A IA não retornou um JSON válido. Tente novamente."}), 500

        if not isinstance(quiz_gerado, list) or len(quiz_gerado) == 0:
            return jsonify({"error": "Formato de quiz inesperado. Tente novamente."}), 500

        return jsonify({"quiz": quiz_gerado})

    except Exception as e:
        print("\n[ERRO INTERNO - QUIZ]:", str(e))
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Servidor STEMbot rodando na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)