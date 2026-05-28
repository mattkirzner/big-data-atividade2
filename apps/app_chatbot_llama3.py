import streamlit as st
from openai import OpenAI
from mcp_server import consultar_banco_pncp
import json

st.set_page_config(page_title="Assistente PNCP Local", page_icon="🦙", layout="centered")
st.title("🦙 Chatbot Local - Llama 3 & PNCP")
st.write("Pergunte sobre as contratações do banco usando IA 100% local e gratuita.")

client = OpenAI(
    base_url="http://host.docker.internal:11434/v1",
    api_key="ollama" 
)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {       
            "role": "system", 
            "content": (
                "Você é um analista de dados especialista em compras públicas. Você tem acesso a um banco de dados SQLite "
                "por meio da ferramenta 'consultar_banco_pncp'. Sempre que o usuário fizer uma pergunta sobre os dados, "
                "você DEVE gerar a query SQL, chamar a ferramenta e usar o resultado retornado por ela para formular sua "
                "resposta final em português. Nunca invente dados e não fique apenas explicando o SQL, traga a resposta baseada no dado real."
            )
        }   
    ]

# Renderiza o chat na tela de forma segura usando dicionários
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("Pergunte algo sobre os dados salvos..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        
        tools = [{
            "type": "function",
            "function": {
                "name": "consultar_banco_pncp",
                "description": "Executa uma query SQL SELECT no banco SQLite local do PNCP.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query_sql": {
                            "type": "string",
                            "description": "A query SQL completa. Exemplo: SELECT SUM(valorTotalHomologado) FROM contratacoes_pncp WHERE uf='PE'"
                        }
                    },
                    "required": ["query_sql"]
                }
            }
        }]

        response = client.chat.completions.create(
            model="llama3.1", 
            messages=st.session_state.messages,
            tools=tools,
            tool_choice="auto"
        )
        
        response_message = response.choices[0].message
        
        # 💡 SOLUÇÃO: Se houver chamada de ferramenta, convertemos a estrutura para dicionários compatíveis
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                if tool_call.function.name == "consultar_banco_pncp":
                    args = json.loads(tool_call.function.arguments)
                    sql_gerado = args.get("query_sql")
                    
                    st.caption(f"🔍 *Llama 3.1 gerou a consulta:* `{sql_gerado}`")
                    
                    resultado_banco = consultar_banco_pncp(query_sql=sql_gerado)
                    
                    # 💡 Forçamos o salvamento em formato JSON/Dicionário estruturado puro
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response_message.content,
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_call.function.name,
                                "arguments": tool_call.function.arguments
                            }
                        }]
                    })
                    
                    st.session_state.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": "consultar_banco_pncp",
                        "content": resultado_banco
                    })
                    
                    segunda_resposta = client.chat.completions.create(
                        model="llama3.1",
                        messages=st.session_state.messages
                    )
                    
                    texto_final = segunda_resposta.choices[0].message.content
                    response_placeholder.markdown(texto_final)
                    st.session_state.messages.append({"role": "assistant", "content": texto_final})
        else:
            # Resposta direta sem ferramentas também entra como dicionário simples
            texto_final = response_message.content
            response_placeholder.markdown(texto_final)
            st.session_state.messages.append({"role": "assistant", "content": texto_final})