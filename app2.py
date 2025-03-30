import os
import yaml
from flask import Flask, request, jsonify

# ✅ NOVOS IMPORTS ATUALIZADOS
from langchain_community.utilities import SQLDatabase
from langchain_community.tools import QuerySQLDataBaseTool, InfoSQLDatabaseTool
from langchain.agents import initialize_agent, Tool
from langchain.agents.agent_types import AgentType
from langchain_openai import ChatOpenAI

# 🔐 Carrega configurações
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

os.environ["OPENAI_API_KEY"] = config["api_key"]["key"]
model = config["model"]["name"]

# 🔗 Banco de dados
db = SQLDatabase.from_uri("sqlite:///delivery.db")

# 🧠 Ferramentas
tools = [
    Tool(
        name="Consultar_Banco_delivery",
        func=QuerySQLDataBaseTool(db=db).run,
        description="Use esta ferramenta para responder perguntas sobre pedidos, produtos, ticket médio, faturamento, etc."
    ),
    Tool(
        name="Info_sobre_banco",
        func=InfoSQLDatabaseTool(db=db).run,
        description="Mostra estrutura das tabelas e colunas do banco de dados."
    )
]

llm = ChatOpenAI(model=model, temperature=0.5)

agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

# 🚀 API
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
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
