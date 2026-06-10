import streamlit as st
import json
import os
from groq import Groq
from mcp_server import consultar_banco_pncp # Importa do servidor desacoplado

st.set_page_config(
    page_title="Assistente PNCP Local", page_icon="🦙", layout="centered"
)
st.title("🦙 Chatbot Groq — Llama 3 & PNCP")
st.write("Pergunte sobre as contratações do banco usando a ultra velocidade do Groq.")

# 🎯 Centralização do modelo correto para evitar falhas de execução na API
MODEL_NAME = "llama-3.3-70b-versatile"

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "system",
            "content": (
                "Você é um analista de dados especialista em compras públicas brasileiro. Você tem acesso a um banco "
                "de dados SQLite por meio da ferramenta 'consultar_banco_pncp'. Sempre que o usuário fizer uma pergunta "
                "sobre os dados, você DEVE gerar a query SQL utilizando as seguintes colunas disponíveis se necessário: "
                "[numeroControlePNCP, data_publicacao, descricao, entidade, linkOrigem, modalidade, municipio, status, uf, valor, valorTotalHomologado, anoCompra]. "
                "Chame a ferramenta, analise o retorno em Markdown e formule sua resposta final em português de forma clara. "
                "Nunca invente dados que não retornaram do banco de dados."
            ),
        }
    ]

# 💡 CORREÇÃO: Filtra mensagens sem texto (como chamadas de ferramenta intermediárias) para não quebrar o Streamlit
for message in st.session_state.messages:
    if message["role"] != "system" and message.get("content"):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Pergunte algo sobre os dados salvos..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()

        # Configuração das ferramentas seguindo a especificação do Groq
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "consultar_banco_pncp",
                    "description": "Executa uma query SQL SELECT válida no banco SQLite do PNCP.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query_sql": {
                                "type": "string",
                                "description": "A query SQL de leitura completa. Exemplo: SELECT entidade, valorTotalHomologado FROM contratacoes_pncp WHERE uf='PE' LIMIT 5",
                            }
                        },
                        "required": ["query_sql"],
                    },
                },
            }
        ]

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=st.session_state.messages,
            tools=tools,
            tool_choice="auto"
        )

        response_message = response.choices[0].message

        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "consultar_banco_pncp":
                    args = json.loads(tool_call.function.arguments)
                    sql_gerado = args.get("query_sql")

                    st.caption(f"🔍 *Llama 3 (Groq) gerou a consulta:* `{sql_gerado}`")

                    # Executa a função localmente (comportamento desacoplado)
                    resultado_banco = consultar_banco_pncp(query_sql=sql_gerado)

                    # Registra a intenção da ferramenta no histórico de mensagens
                    st.session_state.messages.append(
                        {
                            "role": "assistant",
                            "content": response_message.content or "",
                            "tool_calls": [
                                {
                                    "id": tool_call.id,
                                    "type": "function",
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments,
                                    },
                                }
                            ],
                        }
                    )

                    # Registra o retorno real do banco de dados
                    st.session_state.messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": "consultar_banco_pncp",
                            "content": resultado_banco,
                        }
                    )

                    # 💡 CORREÇÃO CRÍTICA: Utiliza o MODEL_NAME correto em vez de "llama3.1" para evitar o erro 404
                    segunda_resposta = client.chat.completions.create(
                        model=MODEL_NAME, 
                        messages=st.session_state.messages
                    )

                    texto_final = segunda_resposta.choices[0].message.content
                    response_placeholder.markdown(texto_final)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": texto_final}
                    )
        else:
            texto_final = response_message.content
            response_placeholder.markdown(texto_final)
            st.session_state.messages.append(
                {"role": "assistant", "content": texto_final}
            )