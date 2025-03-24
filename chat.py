import streamlit as st
import requests
import uuid

# 🔧 CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Delivery Insights",
    page_icon="🍕",
    layout="centered"
)

# 🎨 ESTILO PERSONALIZADO
st.markdown("""
    <style>
        .main {
            background-color: #f9f9f9;
        }
        h1, h3 {
            text-align: center;
            font-family: 'Segoe UI', sans-serif;
        }
        .stChatInput input {
            border-radius: 8px !important;
            padding: 10px !important;
        }
    </style>
""", unsafe_allow_html=True)

# 🧑‍🍳 CABEÇALHO
st.markdown("<h1>🍕 Delivery Insights</h1>", unsafe_allow_html=True)
st.markdown("<h3>Converse com a IA e entenda os dados do seu delivery</h3>", unsafe_allow_html=True)

# 📷 IMAGEM DE DESTAQUE (altere conforme necessário)
st.image("delivery_banner.webp", use_container_width=True)

# 📌 EXEMPLOS DE PERGUNTAS
with st.expander("❓ Exemplos de perguntas"):
    st.markdown("""
    - Qual o ticket médio em São Paulo?
    - Quais produtos mais vendidos no bairro Moema?
    - Quantos pedidos foram feitos em janeiro?
    - Quanto tempo leva a entrega média no Rio de Janeiro?
    """)

# 🔁 BOTÃO DE RESET
if st.button("🔄 Nova conversa"):
    st.session_state.messages = []
    st.experimental_rerun()

# 🆔 CLIENT ID ÚNICO POR SESSÃO
if "client_id" not in st.session_state:
    st.session_state.client_id = str(uuid.uuid4())

# 💬 HISTÓRICO DE MENSAGENS
if "messages" not in st.session_state:
    st.session_state.messages = []

# 🔗 ENVIA PERGUNTA PARA A API
def ask_question(question):
    url ="http://20.197.225.152:5000/ask"  # ou o endpoint da sua API em produção
    payload = {
        "client_id": st.session_state.client_id,
        "question": question
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        return response.json().get("answer", "Erro ao obter resposta.")
    return f"Erro: {response.status_code} - {response.text}"

# 🧾 MOSTRA MENSAGENS ANTERIORES
for message in st.session_state.messages:
    avatar = "👤" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"]):
        st.markdown(f"{avatar} {message['content']}")

# 📥 INPUT DO USUÁRIO
prompt = st.chat_input("Ex: Qual o ticket médio em São Paulo?")
if prompt:
    # Usuário
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(f"👤 {prompt}")
    
    # IA responde com spinner
    with st.chat_message("assistant"):
        with st.spinner("🤖 Pensando..."):
            answer = ask_question(prompt)
            st.markdown(f"🤖 {answer}")
    
    # Guarda no histórico
    st.session_state.messages.append({"role": "assistant", "content": answer})

