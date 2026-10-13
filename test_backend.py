import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importa as instâncias e modelos do seu arquivo principal
from backend import app, get_db, Base

# 1. Configuração do Banco em Memória (Rápido e Isolado)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool, # Mantém a mesma conexão na memória para todos os testes
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 2. Fixtures: Preparam e limpam o terreno para CADA teste
@pytest.fixture(scope="function")
def db_session():
    # Cria as tabelas do zero antes do teste
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Destrói as tabelas após o teste
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    # Substitui a injeção de dependência original (treinos.db) pela nossa em memória
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c

# 3. Testes Unitários e de Integração da API

def test_iniciar_novo_treino(client):
    response = client.post("/workouts/start")
    
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
    assert "id" in data

def test_impedir_dois_treinos_ativos(client):
    client.post("/workouts/start")
    response = client.post("/workouts/start")
    
    assert response.status_code == 400
    assert response.json()["detail"] == "Já existe um treino em andamento."

def test_adicionar_exercicio_em_treino_ativo(client):
    w_id = client.post("/workouts/start").json()["id"]
    response = client.post(f"/workouts/{w_id}/exercises", json={"name": "Agachamento Livre"})
    
    assert response.status_code == 200
    assert response.json()["name"] == "Agachamento Livre"

def test_finalizar_treino(client):
    w_id = client.post("/workouts/start").json()["id"]
    response = client.post(f"/workouts/{w_id}/finish")
    assert response.status_code == 200
    
    active_res = client.get("/workouts/active")
    assert active_res.json() is None

# --- NOVOS TESTES (Deleção) ---

def test_deletar_serie_sucesso(client):
    w_id = client.post("/workouts/start").json()["id"]
    ex_id = client.post(f"/workouts/{w_id}/exercises", json={"name": "Supino"}).json()["id"]
    set_id = client.post(f"/exercises/{ex_id}/sets", json={"weight": 60, "reps": 10}).json()["id"]
    
    response = client.delete(f"/sets/{set_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Série deletada com sucesso."

def test_deletar_exercicio_sucesso(client):
    w_id = client.post("/workouts/start").json()["id"]
    ex_id = client.post(f"/workouts/{w_id}/exercises", json={"name": "Supino"}).json()["id"]
    
    response = client.delete(f"/exercises/{ex_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Exercício deletado com sucesso."

def test_deletar_serie_em_treino_finalizado_deve_falhar(client):
    w_id = client.post("/workouts/start").json()["id"]
    ex_id = client.post(f"/workouts/{w_id}/exercises", json={"name": "Supino"}).json()["id"]
    set_id = client.post(f"/exercises/{ex_id}/sets", json={"weight": 60, "reps": 10}).json()["id"]
    
    client.post(f"/workouts/{w_id}/finish")
    
    response = client.delete(f"/sets/{set_id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Não é possível alterar um treino já finalizado."

def test_deletar_exercicio_em_treino_finalizado_deve_falhar(client):
    w_id = client.post("/workouts/start").json()["id"]
    ex_id = client.post(f"/workouts/{w_id}/exercises", json={"name": "Supino"}).json()["id"]
    
    client.post(f"/workouts/{w_id}/finish")
    
    response = client.delete(f"/exercises/{ex_id}")
    assert response.status_code == 400
    assert response.json()["detail"] == "Não é possível alterar um treino já finalizado."

# --- NOVOS TESTES (Nomes e Últimos Parâmetros) ---

def test_obter_nomes_de_exercicios_unicos(client):
    w_id = client.post("/workouts/start").json()["id"]
    client.post(f"/workouts/{w_id}/exercises", json={"name": "Supino Reto"})
    client.post(f"/workouts/{w_id}/exercises", json={"name": "Agachamento Livre"})
    client.post(f"/workouts/{w_id}/exercises", json={"name": "Supino Reto"}) # Duplicado propositalmente
    
    response = client.get("/exercises/names")
    assert response.status_code == 200
    nomes = response.json()
    
    # Deve retornar apenas 2 nomes e estar em ordem alfabética
    assert len(nomes) == 2
    assert nomes == ["Agachamento Livre", "Supino Reto"]

def test_obter_ultimos_parametros_do_exercicio(client):
    w_id = client.post("/workouts/start").json()["id"]
    ex_id = client.post(f"/workouts/{w_id}/exercises", json={"name": "Leg Press"}).json()["id"]
    
    # Adiciona duas séries
    client.post(f"/exercises/{ex_id}/sets", json={"weight": 150, "reps": 12})
    client.post(f"/exercises/{ex_id}/sets", json={"weight": 160, "reps": 10}) # Esta é a última série registrada
    
    client.post(f"/workouts/{w_id}/finish")
    
    # Busca os últimos parâmetros do Leg Press
    response = client.get("/exercises/last-params?name=Leg Press")
    assert response.status_code == 200
    data = response.json()
    
    assert data["weight"] == 160.0
    assert data["reps"] == 10

def test_obter_ultimos_parametros_de_exercicio_inexistente(client):
    # Se o exercício nunca foi feito, deve retornar o default (0.0 kg e 1 rep)
    response = client.get("/exercises/last-params?name=Exercício Novo")
    assert response.status_code == 200
    data = response.json()
    
    assert data["weight"] == 0.0
    assert data["reps"] == 1