import sqlite3
import sys

def limpar_banco():
    conn = sqlite3.connect("treinos.db")
    cursor = conn.cursor()

    try:
        # Apagamos primeiro as tabelas filhas e depois as tabelas pais 
        # para não haver conflito de integridade referencial
        cursor.execute("DELETE FROM sets")
        cursor.execute("DELETE FROM exercises")
        cursor.execute("DELETE FROM workouts")
        
        conn.commit()
        print("🗑️ Todo o histórico do banco de dados foi limpo com sucesso!")
    except Exception as e:
        print(f"Erro ao limpar o banco: {e}")
    finally:
        conn.close()

def popular_historico():
    conn = sqlite3.connect("treinos.db")
    cursor = conn.cursor()

    # Histórico simulando evolução de cargas em 3 datas diferentes no passado
    treinos_mock = [
        {
            "data": "2026-09-20 10:00:00", 
            "exercicios": [
                {"nome": "Agachamento Livre", "series": [(60, 10), (60, 10), (65, 8)]},
                {"nome": "Supino Reto", "series": [(50, 10), (50, 8)]}
            ]
        },
        {
            "data": "2026-09-27 10:00:00", 
            "exercicios": [
                {"nome": "Agachamento Livre", "series": [(65, 10), (70, 8), (70, 8)]},
                {"nome": "Supino Reto", "series": [(55, 10), (60, 6)]}
            ]
        },
        {
            "data": "2026-10-04 10:00:00", 
            "exercicios": [
                {"nome": "Agachamento Livre", "series": [(70, 10), (75, 8), (80, 6)]},
                {"nome": "Supino Reto", "series": [(60, 10), (65, 6), (65, 5)]},
                {"nome": "Leg Press 45", "series": [(100, 12), (120, 10), (150, 6)]}
            ]
        }
    ]

    try:
        for treino in treinos_mock:
            # 1. Insere o treino já finalizado (is_active = 0)
            cursor.execute(
                "INSERT INTO workouts (date_created, date_finished, is_active) VALUES (?, ?, 0)",
                (treino["data"], treino["data"])
            )
            workout_id = cursor.lastrowid

            # 2. Insere os exercícios e suas respectivas séries
            for ex in treino["exercicios"]:
                cursor.execute(
                    "INSERT INTO exercises (name, workout_id) VALUES (?, ?)",
                    (ex["nome"], workout_id)
                )
                exercise_id = cursor.lastrowid

                for peso, reps in ex["series"]:
                    cursor.execute(
                        "INSERT INTO sets (weight, reps, exercise_id) VALUES (?, ?, ?)",
                        (peso, reps, exercise_id)
                    )

        conn.commit()
        print("✅ Histórico mock inserido com sucesso!")
    except Exception as e:
        print(f"Erro ao popular o banco: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    # Pega o comando passado no terminal (ex: "limpar" ou "popular")
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
        print("Uso correto: python popular_banco.py popular")
        print("             python popular_banco.py limpar")