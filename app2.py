import os
import yaml
from flask import Flask, request, jsonify
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDatabaseTool, InfoSQLDatabaseTool
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage

# ======================
# 🔐 CONFIGURAÇÃO
# ======================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

os.environ["OPENAI_API_KEY"] = config["api_key"]["key"]
model = config["model"]["name"]

# ======================
# 🔗 BANCO DE DADOS
# ======================
DATABASE_PATH = "delivery.db"
db = SQLDatabase.from_uri(f"sqlite:///{DATABASE_PATH}")

# Captura o schema do banco como contexto inicial
schema_context = InfoSQLDatabaseTool(db=db).run("")
system_prompt = SystemMessage(
    content=f"""
Você é um analista de dados inteligente. Use os dados abaixo para responder perguntas sobre o delivery.

📊 Estrutura do banco de dados:
{schema_context}

Sempre que possível, responda em linguagem natural com base nos resultados do banco.
"""
)

# ======================
# 🧠 FERRAMENTAS DO AGENTE
# ======================
tools = [
    Tool(
        name="query_delivery_db",
        func=QuerySQLDatabaseTool(db=db).run,
        description="Executa consultas SQL na tabela 'pedidos' com colunas como cidade, bairro, produto, valor_total, tempo_entrega e data_pedido."
    ),
    Tool(
        name="info_sobre_banco",
        func=InfoSQLDatabaseTool(db=db).run,
        description="Retorna estrutura de tabelas e colunas disponíveis no banco SQLite."
    )
]

llm = ChatOpenAI(model=model, temperature=0.5)

# ======================
# 🤖 AGENTE LANGCHAIN
# ======================
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True,
    agent_kwargs={"system_message": system_prompt}
)

# ======================
# 🚀 API FLASK
# ======================
app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.get_json()
    if not data or "question" not in data:
        return jsonify({"error": "Requisição inválida. Forneça a chave 'question'."}), 400

    pergunta = data["question"]

    try:
        resposta = agent.run(pergunta)
        return jsonify({"answer": resposta})
    except Exception as e:
        return jsonify({"error": f"Erro ao processar a pergunta: {str(e)}"}), 500

# ======================
# 🏁 MAIN
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
