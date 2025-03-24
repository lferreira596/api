import os
import sqlite3
import json
import yaml
from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

# Carrega configurações do arquivo YAML
CONFIG_FILE = "config.yaml"
with open(CONFIG_FILE, "r") as file:
    config = yaml.safe_load(file)

# Define variáveis de ambiente
os.environ["OPENAI_API_KEY"] = config["api_key"]["key"]
model = config["model"]["name"]

# Nome do banco de dados para dados de suporte
DATABASE_PATH = "delivery.db"

# Inicia Flask
app = Flask(__name__)

# Instancia o modelo da OpenAI
chat = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Conecta ao banco SQLite
def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Interpreta pergunta com LLM e retorna a intenção
def avaliar_pergunta_delivery(question):
    system_prompt = """
    Você é um analista de dados de pedidos de delivery. Sua tarefa é entender perguntas em linguagem natural
    e retornar um JSON com a métrica a ser analisada e os filtros desejados.

    Métricas possíveis:
    - "ticket_medio": valor médio dos pedidos
    - "mais_vendidos": produtos mais vendidos
    - "tempo_medio_entrega": tempo médio de entrega
    - "quantidade_pedidos": número de pedidos

    Filtros possíveis (opcionais): cidade, bairro, produto, data_pedido

    Responda SOMENTE com um JSON válido no seguinte formato:
    {
        "tipo": "<ticket_medio|mais_vendidos|tempo_medio_entrega|quantidade_pedidos>",
        "filtros": {
            "cidade": "São Paulo",
            "bairro": "Moema",
            "produto": "pizza",
            "data_pedido": "2024-03-01"
        }
    }

    Caso um filtro não seja mencionado, omita-o.
    """
    human_prompt = f"Pergunta: \"{question}\""
    response = chat.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ])
    return json.loads(response.content.strip())

# Monta e executa SQL com base no JSON retornado pela LLM
def consultar_delivery(metadados):
    tipo = metadados.get("tipo")
    filtros = metadados.get("filtros", {})

    where_clauses = []
    params = []
    for campo, valor in filtros.items():
        where_clauses.append(f"{campo} = ?")
        params.append(valor)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    conn = get_db_connection()
    cursor = conn.cursor()

    if tipo == "ticket_medio":
        cursor.execute(f"SELECT AVG(valor_total) AS resultado FROM pedidos {where_sql}", params)
        row = cursor.fetchone()
        return f"O ticket médio é R$ {row['resultado']:.2f}" if row and row['resultado'] else "Não há dados suficientes."

    elif tipo == "tempo_medio_entrega":
        cursor.execute(f"SELECT AVG(tempo_entrega) AS resultado FROM pedidos {where_sql}", params)
        row = cursor.fetchone()
        return f"O tempo médio de entrega é {round(row['resultado'])} minutos." if row and row['resultado'] else "Não há dados suficientes."

    elif tipo == "mais_vendidos":
        cursor.execute(f'''
            SELECT produto, COUNT(*) AS total 
            FROM pedidos 
            {where_sql}
            GROUP BY produto 
            ORDER BY total DESC 
            LIMIT 5
        ''', params)
        rows = cursor.fetchall()
        if not rows:
            return "Nenhum produto encontrado."
        resposta = "Top produtos mais vendidos:\n"
        for i, r in enumerate(rows, 1):
            resposta += f"{i}. {r['produto']} - {r['total']} pedidos\n"
        return resposta

    elif tipo == "quantidade_pedidos":
        cursor.execute(f"SELECT COUNT(*) AS total FROM pedidos {where_sql}", params)
        row = cursor.fetchone()
        return f"Total de pedidos: {row['total']}" if row else "Não há dados disponíveis."

    else:
        return "Desculpe, não entendi a análise solicitada."

# Rota principal
@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Requisição inválida. Forneça a chave 'question'."}), 400

    question = data["question"]

    try:
        analise = avaliar_pergunta_delivery(question)
        resposta = consultar_delivery(analise)
    except Exception as e:
        resposta = f"Erro ao processar a pergunta: {str(e)}"

    return jsonify({"answer": resposta})

# Roda servidor
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)


# DATABASE_PATH
