import sys
from datetime import datetime, timezone
from backend import SessionLocal, DBWorkout, DBExercise, DBSet

def limpar_banco():
    db = SessionLocal()
    try:
        # Apagamos usando o ORM. Funciona em qualquer banco de dados!
        db.query(DBSet).delete()
        db.query(DBExercise).delete()
        db.query(DBWorkout).delete()
        
        db.commit()
        print("🗑️ Todo o histórico do banco de dados foi limpo com sucesso!")
    except Exception as e:
        db.rollback()
        print(f"Erro ao limpar o banco: {e}")
    finally:
        db.close()

def popular_historico():
    db = SessionLocal()

    # Histórico mock utilizando objetos datetime com timezone UTC
    treinos_mock = [
        {
            "data": datetime.fromisoformat("2026-09-20T10:00:00+00:00"), 
            "exercicios": [
                {"nome": "Agachamento Livre", "series": [(60, 10), (60, 10), (65, 8)]},
                {"nome": "Supino Reto", "series": [(50, 10), (50, 8)]}
            ]
        },
        {
            "data": datetime.fromisoformat("2026-09-27T10:00:00+00:00"), 
            "exercicios": [
                {"nome": "Agachamento Livre", "series": [(65, 10), (70, 8), (70, 8)]},
                {"nome": "Supino Reto", "series": [(55, 10), (60, 6)]}
            ]
        },
        {
            "data": datetime.fromisoformat("2026-10-04T10:00:00+00:00"), 
            "exercicios": [
                {"nome": "Agachamento Livre", "series": [(70, 10), (75, 8), (80, 6)]},
                {"nome": "Supino Reto", "series": [(60, 10), (65, 6), (65, 5)]},
                {"nome": "Leg Press 45", "series": [(100, 12), (120, 10), (150, 6)]}
            ]
        }
    ]

    try:
        for treino in treinos_mock:
            # 1. Instancia o Treino
            novo_treino = DBWorkout(
                date_created=treino["data"], 
                date_finished=treino["data"], 
                is_active=False
            )
            db.add(novo_treino)

            # 2. Instancia Exercícios e Séries vinculados ao treino
            for ex in treino["exercicios"]:
                novo_ex = DBExercise(name=ex["nome"], workout=novo_treino)
                db.add(novo_ex)

                for peso, reps in ex["series"]:
                    nova_serie = DBSet(weight=float(peso), reps=int(reps), exercise=novo_ex)
                    db.add(nova_serie)
        
        db.commit()
        print("✅ Histórico mock inserido com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao popular o banco: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "popular":
            popular_historico()
        elif comando == "limpar":
            limpar_banco()
        else:
            print("❌ Comando não reconhecido. Use 'popular' ou 'limpar'.")
    else:
        print("⚠️  Por favor, informe o que deseja fazer.")
        print("Uso correto: python manipular_banco.py popular")
        print("             python manipular_banco.py limpar")