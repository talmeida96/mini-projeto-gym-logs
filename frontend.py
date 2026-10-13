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

# --- Função Utilitária para Formatar Data ---
def formatar_data_br(data_iso: str, incluir_hora: bool = False) -> str:
    """Transforma '2026-10-13T14:30:00' em '13/10/2026' ou '13/10/2026 às 14:30'"""
    try:
        dt = datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
        if incluir_hora:
            return dt.strftime("%d/%m/%Y às %H:%M")
        return dt.strftime("%d/%m/%Y")
    except:
        return data_iso # Fallback caso venha num formato inesperado

# --- Funções de API com Tratamento de Conexão ---
def checar_conexao():
    """Tenta um GET simples para ver se a API está online"""
    try:
        requests.get(f"{API_URL}/docs", timeout=2)
        return True
    except requests.exceptions.ConnectionError:
        return False

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

# --- Verificação de Segurança (Backend Online?) ---
if not checar_conexao():
    st.error("🔌 **Servidor Offline:** Não foi possível conectar ao banco de dados. Certifique-se de que o backend (Uvicorn) está rodando.")
    st.stop() # Interrompe a renderização do resto da página aqui

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
        # Formata a data de início para o padrão BR
        data_inicio = formatar_data_br(active_workout['date_created'])
        st.success(f"Treino em andamento (Iniciado em: {data_inicio})")
        workout_id = active_workout["id"]
        
        with st.expander("➕ Adicionar Exercício", expanded=True):
            existing_names = get_exercise_names()
            
            st.write("Selecione um exercício do histórico ou adicione um novo:")
            
            cols_add = st.columns([0.85, 0.15])
            with cols_add[0]:
                selected_ex = st.selectbox(
                    "Exercícios do seu histórico", 
                    options=["(Selecione um exercício)"] + existing_names,
                    label_visibility="collapsed"
                )
            with cols_add[1]:
                if st.button("➕", use_container_width=True, help="Criar um novo exercício"):
                    modal_novo_exercicio(existing_names, workout_id)
            
            if st.button("Adicionar ao Treino"):
                if selected_ex and selected_ex != "(Selecione um exercício)":
                    add_exercise(workout_id, selected_ex)
                else:
                    st.warning("Por favor, selecione um exercício na lista.")
        
        st.divider()
        
        for ex in active_workout.get("exercises", []):
            cols_ex = st.columns([0.8, 0.2])
            with cols_ex[0]:
                st.subheader(f"💪 {ex['name']}")
            with cols_ex[1]:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("🗑️ Excluir", key=f"del_ex_{ex['id']}"):
                    delete_exercise(ex['id'])
            
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
                
            if ex["sets"]:
                default_weight = float(ex["sets"][-1]["weight"])
                default_reps = int(ex["sets"][-1]["reps"])
            else:
                past_params = get_last_set_params(ex["name"])
                default_weight = float(past_params["weight"])
                default_reps = int(past_params["reps"])
                
            cols = st.columns([1, 1, 1])
            with cols[0]:
                weight = st.number_input("Carga (kg)", min_value=0.0, step=1.0, value=default_weight, key=f"w_{ex['id']}")
            with cols[1]:
                reps = st.number_input("Repetições", min_value=1, step=1, value=default_reps, key=f"r_{ex['id']}")
            with cols[2]:
                st.write("") 
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
            # Substitui o fatiamento simples pela formatação elegante
            date_str = formatar_data_br(workout["date_finished"], incluir_hora=True)
            
            with st.expander(f"Treino - {date_str}"):
                for ex in workout.get("exercises", []):
                    st.markdown(f"**{ex['name']}**")
                    if not ex["sets"]:
                        st.write("Sem séries registradas.")
                    for i, s in enumerate(ex["sets"]):
                        st.write(f"- Série {i+1}: {s['weight']} kg x {s['reps']} reps")

with tab3:
    st.header("📈 Evolução de Carga")
    history = get_history()
    
    if not history:
        st.info("Finalize seu primeiro treino para visualizar a evolução de cargas.")
    else:
        dados_grafico = []
        
        for workout in reversed(history):
            if workout["date_finished"]:
                data_str = formatar_data_br(workout["date_finished"], incluir_hora=False)
                
                for ex in workout.get("exercises", []):
                    if ex["sets"]:
                        for s in ex["sets"]:
                            dados_grafico.append({
                                "Data": data_str,
                                "Exercício": ex["name"],
                                "Carga (kg)": s["weight"],
                                "Repetições": s["reps"]
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
                df_filtrado.reset_index(drop=True, inplace=True)
                df_filtrado["Ordem"] = df_filtrado.index
                
                carga_maxima = df_filtrado["Carga (kg)"].max()
                limite_y = carga_maxima if carga_maxima > 0 else 10
                
                chart = alt.Chart(df_filtrado).mark_line(
                    color='#4a90e2', 
                    point={
                        'color': "#f3ff4b",
                        'size': 100,        
                        'filled': True      
                    }
                ).encode(
                    x=alt.X('Data:N', title='Data do Treino', sort=None),
                    y=alt.Y('Carga (kg):Q', scale=alt.Scale(domain=[0, limite_y])),
                    order=alt.Order('Ordem:Q'),
                    tooltip=['Data', 'Carga (kg)', 'Repetições'] 
                ).properties(
                    height=400
                )

                st.altair_chart(chart, use_container_width=True)