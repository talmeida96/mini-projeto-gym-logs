import os
import streamlit as st
import requests
from datetime import datetime
import pandas as pd
import altair as alt
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# Busca a URL da API do .env, com fallback para o localhost
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="App de Treino", layout="centered")
st.title("🏋️ Controle de Treinos")

# --- Funções de API ---
def get_active_workout():
    response = requests.get(f"{API_URL}/workouts/active")
    return response.json() if response.status_code == 200 and response.json() else None

def start_workout():
    requests.post(f"{API_URL}/workouts/start")
    st.rerun()

def finish_workout(workout_id):
    requests.post(f"{API_URL}/workouts/{workout_id}/finish")
    st.rerun()

def add_exercise(workout_id, name):
    requests.post(f"{API_URL}/workouts/{workout_id}/exercises", json={"name": name})
    st.rerun()

def add_set(exercise_id, weight, reps):
    requests.post(f"{API_URL}/exercises/{exercise_id}/sets", json={"weight": weight, "reps": reps})
    st.rerun()

def get_history():
    response = requests.get(f"{API_URL}/workouts/history")
    return response.json() if response.status_code == 200 else []

def get_exercise_names():
    response = requests.get(f"{API_URL}/exercises/names")
    return response.json() if response.status_code == 200 else []

def get_last_set_params(exercise_name):
    # Passamos o nome como params para o requests formatar a URL corretamente (?name=...)
    response = requests.get(f"{API_URL}/exercises/last-params", params={"name": exercise_name})
    if response.status_code == 200:
        return response.json()
    return {"weight": 0.0, "reps": 1}

def delete_set(set_id):
    requests.delete(f"{API_URL}/sets/{set_id}")
    st.rerun()

def delete_exercise(exercise_id):
    requests.delete(f"{API_URL}/exercises/{exercise_id}")
    st.rerun()

# --- Navegação ---
tab1, tab2, tab3 = st.tabs(["Treino Atual", "Histórico", "Evolução de Carga"])

@st.dialog("Criar Novo Exercício")
def modal_novo_exercicio(existing_names, workout_id):
    st.write("Digite o nome do novo exercício:")
    novo_nome = st.text_input("Nome", label_visibility="collapsed")
    
    if st.button("Salvar e Adicionar ao Treino", type="primary"):
        nome_formatado = novo_nome.strip()
        
        if not nome_formatado:
            st.error("O nome não pode estar vazio.")
        else:
            # Validação: impede que um nome que já existe no histórico seja criado de novo
            nomes_lower = [nome.lower() for nome in existing_names]
            if nome_formatado.lower() in nomes_lower:
                st.error(f"O exercício '{nome_formatado}' já existe! Feche esta janela e selecione-o na lista.")
            else:
                add_exercise(workout_id, nome_formatado)
                st.rerun()

with tab1:
    active_workout = get_active_workout()
    
    if not active_workout:
        st.info("Nenhum treino em andamento.")
        if st.button("Iniciar Novo Treino", type="primary"):
            start_workout()
    else:
        st.success(f"Treino em andamento (Iniciado em: {active_workout['date_created'][:10]})")
        workout_id = active_workout["id"]
        
        # --- NOVO BLOCO: Adicionar novo exercício ---
        with st.expander("➕ Adicionar Exercício", expanded=True):
            existing_names = get_exercise_names()
            
            st.write("Selecione um exercício do histórico ou adicione um novo:")
            
            # Criamos as colunas conforme o rascunho na imagem (Dropdown e botão de +)
            cols_add = st.columns([0.85, 0.15])
            
            with cols_add[0]:
                selected_ex = st.selectbox(
                    "Exercícios do seu histórico", 
                    options=["(Selecione um exercício)"] + existing_names,
                    label_visibility="collapsed"
                )
                
            with cols_add[1]:
                # Botão de "+" que aciona o modal
                if st.button("➕", use_container_width=True, help="Criar um novo exercício"):
                    modal_novo_exercicio(existing_names, workout_id)
            
            # Botão para adicionar o exercício selecionado no dropdown ao treino atual
            if st.button("Adicionar ao Treino"):
                if selected_ex and selected_ex != "(Selecione um exercício)":
                    add_exercise(workout_id, selected_ex)
                else:
                    st.warning("Por favor, selecione um exercício na lista.")
        
        st.divider()
        
        # Listar exercícios e séries do treino ativo
        for ex in active_workout.get("exercises", []):
            
            # Cabeçalho do exercício com botão de excluir
            cols_ex = st.columns([0.8, 0.2])
            with cols_ex[0]:
                st.subheader(f"💪 {ex['name']}")
            with cols_ex[1]:
                # Adicionamos uma margem top no markdown para alinhar melhor visualmente
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Excluir", key=f"del_ex_{ex['id']}"):
                    delete_exercise(ex['id'])
            
            # Tabela de séries com opção de deleção individual
            if ex["sets"]:
                for i, s in enumerate(ex["sets"]):
                    cols_set = st.columns([0.8, 0.2])
                    with cols_set[0]:
                        st.write(f"**Série {i+1}:** {s['weight']} kg x {s['reps']} reps")
                    with cols_set[1]:
                        if st.button("🗑️ Excluir", key=f"del_set_{s['id']}"):
                            delete_set(s['id'])
            else:
                st.write("*Nenhuma série registrada ainda.*")
                
            # --- Lógica de preenchimento automático inserida aqui ---
            if ex["sets"]:
                # Cenário 2: Já existem séries hoje. Puxa os dados da última série gravada agora.
                default_weight = float(ex["sets"][-1]["weight"])
                default_reps = int(ex["sets"][-1]["reps"])
            else:
                # Cenário 1: Nenhuma série hoje. Puxa do histórico geral do banco.
                past_params = get_last_set_params(ex["name"])
                default_weight = float(past_params["weight"])
                default_reps = int(past_params["reps"])
                
            # Form para adicionar série ao exercício
            cols = st.columns([1, 1, 1])
            with cols[0]:
                # value=default_weight aplicado
                weight = st.number_input("Carga (kg)", min_value=0.0, step=1.0, value=default_weight, key=f"w_{ex['id']}")
            with cols[1]:
                # value=default_reps aplicado
                reps = st.number_input("Repetições", min_value=1, step=1, value=default_reps, key=f"r_{ex['id']}")
            with cols[2]:
                st.write("") # Espaçamento
                st.write("")
                if st.button("Gravar Série", key=f"btn_{ex['id']}"):
                    add_set(ex['id'], weight, reps)
            st.divider()
            
        if st.button("✅ Finalizar e Salvar Treino", type="primary", use_container_width=True):
            finish_workout(workout_id)

with tab2:
    st.header("Histórico de Treinos")
    history = get_history()
    
    if not history:
        st.write("Nenhum treino finalizado.")
    else:
        for workout in history:
            date_str = workout["date_finished"][:16].replace("T", " ")
            with st.expander(f"Treino - {date_str}"):
                for ex in workout.get("exercises", []):
                    st.markdown(f"**{ex['name']}**")
                    if not ex["sets"]:
                        st.write("Sem séries registradas.")
                    for i, s in enumerate(ex["sets"]):
                        st.write(f"- Série {i+1}: {s['weight']} kg x {s['reps']} reps")

# --- Evolução de Carga ---
with tab3:
    st.header("📈 Evolução de Carga")
    history = get_history()
    
    if not history:
        st.info("Finalize seu primeiro treino para visualizar a evolução de cargas.")
    else:
        dados_grafico = []
        
        # Lemos o history de trás para frente (reversed) para ficar em ordem cronológica (antigo -> novo)
        for workout in reversed(history):
            if workout["date_finished"]:
                data_str = workout["date_finished"][:10]
                
                for ex in workout.get("exercises", []):
                    if ex["sets"]:
                        # Agora pegamos TODAS as séries gravadas no dia, na ordem em que foram feitas
                        for s in ex["sets"]:
                            dados_grafico.append({
                                "Data": data_str,
                                "Exercício": ex["name"],
                                "Carga (kg)": s["weight"]
                            })
        
        if not dados_grafico:
            st.write("Nenhuma série gravada com carga para gerar o gráfico.")
        else:
            df = pd.DataFrame(dados_grafico)
            
            exercicios_disponiveis = sorted(df["Exercício"].unique())
            ex_selecionado = st.selectbox(
                "Selecione o exercício para analisar:", 
                options=exercicios_disponiveis
            )
            
            df_filtrado = df[df["Exercício"] == ex_selecionado].copy()
            
            if df_filtrado.empty:
                st.write("Nenhum dado para este exercício.")
            else:
                # Cria uma coluna de ordem cronológica para forçar a linha a conectar os pontos na sequência certa
                df_filtrado.reset_index(drop=True, inplace=True)
                df_filtrado["Ordem"] = df_filtrado.index
                
                # Define o limite máximo do eixo Y
                carga_maxima = df_filtrado["Carga (kg)"].max()
                limite_y = carga_maxima if carga_maxima > 0 else 10 # Evita quebrar se a carga for 0 (peso corporal)
                
                # Montamos o gráfico customizado com Altair
                chart = alt.Chart(df_filtrado).mark_line(
                    color='#4a90e2', # Cor da linha (ex: um tom de azul)
                    point={
                        'color': "#f3ff4b", # Cor dos pontos (ex: o vermelho/coral padrão do Streamlit)
                        'size': 100,        # Tamanho do ponto para dar mais destaque
                        'filled': True      # Preenche o ponto com a cor
                    }
                ).encode(
                    x=alt.X('Data:N', title='Data do Treino', sort=None),
                    y=alt.Y('Carga (kg):Q', scale=alt.Scale(domain=[0, limite_y])),
                    order=alt.Order('Ordem:Q'),
                    tooltip=['Data', 'Carga (kg)']
                ).properties(
                    height=400
                )

                st.altair_chart(chart, use_container_width=True)