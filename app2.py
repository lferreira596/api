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
Você é um assistente virtual inteligente e cordial especializado em análise de dados de delivery. 
Sua função é ajudar o usuário a entender melhor os dados do negócio e tomar decisões mais informadas.

Ao iniciar a conversa, cumprimente o usuário de forma educada e apresente-se brevemente. 
Diga que está disponível para responder perguntas sobre os dados de pedidos e fornecer análises como:

- Ticket médio
- Produtos mais vendidos
- Tempo médio de entrega
- Quantidade total de pedidos
- Faturamento
- Lucro estimado
- Margem de lucro
- Faturamento mensal
- Vendas por categoria

Caso a pergunta do usuário esteja fora desse contexto, avise com educação que não poderá ajudar.

Exemplos de perguntas válidas:
- "Qual o ticket médio em São Paulo?"
- "Qual o faturamento em março?"
- "Quais os produtos mais vendidos em BH?"

Sempre responda de forma clara, objetiva e educada.
Você é um analisador de intenção para perguntas sobre delivery. Sua única tarefa é identificar a intenção da pergunta e retornar um JSON estruturado.

⚠️ Responda SOMENTE com um JSON válido. Não inclua texto explicativo, saudação ou qualquer outra coisa.

Formato do JSON:

{
    "tipo": "<ticket_medio|mais_vendidos|tempo_medio_entrega|quantidade_pedidos|faturamento|lucro|margem|faturamento_mensal|vendas_por_categoria>",
    "filtros": {
        "cidade": "São Paulo",
        "data_pedido": "2024-03"
    }
}

Se um filtro não for mencionado, **não o inclua**. Se a pergunta não for sobre dados de delivery, retorne:

{ "tipo": null, "filtros": {} }
"""
    human_prompt = f"Pergunta: \"{question}\""
    response = chat.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
])

# Debug opcional:
    print("🧠 Resposta da LLM:", response.content)

    try:
        return json.loads(response.content)
    except Exception as e:
        raise ValueError(f"Erro ao interpretar a resposta da LLM: {e}\nResposta recebida: {response.content}")

# Monta e executa SQL com base no JSON retornado pela LLM
def consultar_delivery(metadados):
    tipo = metadados.get("tipo")
    filtros = metadados.get("filtros", {})

    where_clauses = []
    params = []

    for campo, valor in filtros.items():
        if campo == "data_pedido" and len(valor) == 7:
            where_clauses.append("strftime('%Y-%m', data_pedido) = ?")
        else:
            where_clauses.append(f"{campo} = ?")
        params.append(valor)

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    conn = get_db_connection()
    cursor = conn.cursor()

    if tipo == "ticket_medio":
        cursor.execute(f"SELECT AVG(valor_total) AS resultado FROM pedidos {where_sql}", params)
        row = cursor.fetchone()
        return f"O ticket médio é R$ {row['resultado']:.2f}" if row and row['resultado'] else "Sem dados."

    elif tipo == "tempo_medio_entrega":
        cursor.execute(f"SELECT AVG(tempo_entrega) AS resultado FROM pedidos {where_sql}", params)
        row = cursor.fetchone()
        return f"O tempo médio de entrega é {round(row['resultado'])} minutos." if row and row['resultado'] else "Sem dados."

    elif tipo == "mais_vendidos":
        cursor.execute(f"""
            SELECT produto, COUNT(*) AS total 
            FROM pedidos 
            {where_sql}
            GROUP BY produto 
            ORDER BY total DESC 
            LIMIT 5
        """, params)
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
        return f"Total de pedidos: {row['total']}" if row else "Sem dados."

    elif tipo == "faturamento":
        cursor.execute(f"SELECT SUM(valor_total) AS total FROM pedidos {where_sql}", params)
        row = cursor.fetchone()
        return f"Faturamento total: R$ {row['total']:.2f}" if row and row['total'] else "Sem dados."

    elif tipo == "lucro":
        cursor.execute(f"SELECT SUM(valor_total - (custo_unitario * quantidade)) AS lucro FROM pedidos {where_sql}", params)
        row = cursor.fetchone()
        return f"Lucro estimado: R$ {row['lucro']:.2f}" if row and row['lucro'] else "Sem dados."

    elif tipo == "margem":
        cursor.execute(f"""
            SELECT 
                SUM(valor_total - (custo_unitario * quantidade)) AS lucro, 
                SUM(valor_total) AS receita
            FROM pedidos {where_sql}
        """, params)
        row = cursor.fetchone()
        if row and row['receita']:
            margem = (row['lucro'] / row['receita']) * 100
            return f"A margem bruta é de {margem:.2f}%"
        return "Sem dados."

    elif tipo == "faturamento_mensal":
        cursor.execute(f"""
            SELECT strftime('%Y-%m', data_pedido) AS mes, SUM(valor_total) AS total
            FROM pedidos {where_sql}
            GROUP BY mes ORDER BY mes
        """, params)
        rows = cursor.fetchall()
        if not rows:
            return "Sem dados mensais."
        return "\n".join([f"{r['mes']}: R$ {r['total']:.2f}" for r in rows])

    elif tipo == "vendas_por_categoria":
        cursor.execute(f"""
            SELECT categoria, SUM(quantidade) AS total
            FROM pedidos {where_sql}
            GROUP BY categoria
        """, params)
        rows = cursor.fetchall()
        if not rows:
            return "Sem dados por categoria."
        return "\n".join([f"{r['categoria']}: {r['total']} unidades" for r in rows])

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