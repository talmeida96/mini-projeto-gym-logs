from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel, ConfigDict
import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env
load_dotenv()

# --- Database Setup ---
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./treinos.db")

if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLAlchemy Models ---
class DBWorkout(Base):
    __tablename__ = "workouts"
    id = Column(Integer, primary_key=True, index=True)
    date_created = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    date_finished = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    exercises = relationship("DBExercise", back_populates="workout", cascade="all, delete-orphan")

class DBExercise(Base):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id"))
    workout = relationship("DBWorkout", back_populates="exercises")
    sets = relationship("DBSet", back_populates="exercise", cascade="all, delete-orphan")

class DBSet(Base):
    __tablename__ = "sets"
    id = Column(Integer, primary_key=True, index=True)
    weight = Column(Float)
    reps = Column(Integer)
    exercise_id = Column(Integer, ForeignKey("exercises.id"))
    exercise = relationship("DBExercise", back_populates="sets")

Base.metadata.create_all(bind=engine)

# --- Pydantic Schemas ---
class SetCreate(BaseModel):
    weight: float
    reps: int

class SetResponse(SetCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ExerciseCreate(BaseModel):
    name: str

class ExerciseResponse(ExerciseCreate):
    id: int
    sets: List[SetResponse] = []
    model_config = ConfigDict(from_attributes=True)

class WorkoutResponse(BaseModel):
    id: int
    date_created: datetime
    date_finished: Optional[datetime]
    is_active: bool
    exercises: List[ExerciseResponse] = []
    model_config = ConfigDict(from_attributes=True)

# --- FastAPI App ---
app = FastAPI(title="Treino API MVP", description="API para controle e acompanhamento de treinos.")

# Configuração de CORS (Permite que outros frontends consumam esta API futuramente)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Rotas de Workouts ---
@app.post("/workouts/start", response_model=WorkoutResponse, tags=["Workouts"])
def start_workout(db: Session = Depends(get_db)):
    active = db.query(DBWorkout).filter(DBWorkout.is_active == True).first()
    if active:
        raise HTTPException(status_code=400, detail="Já existe um treino em andamento.")
    new_workout = DBWorkout()
    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)
    return new_workout

@app.get("/workouts/active", response_model=Optional[WorkoutResponse], tags=["Workouts"])
def get_active_workout(db: Session = Depends(get_db)):
    return db.query(DBWorkout).filter(DBWorkout.is_active == True).first()

@app.post("/workouts/{workout_id}/finish", tags=["Workouts"])
def finish_workout(workout_id: int, db: Session = Depends(get_db)):
    workout = db.query(DBWorkout).filter(DBWorkout.id == workout_id).first()
    if not workout or not workout.is_active:
        raise HTTPException(status_code=404, detail="Treino ativo não encontrado.")
    
    workout.is_active = False
    workout.date_finished = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Treino finalizado com sucesso."}

@app.get("/workouts/history", response_model=List[WorkoutResponse], tags=["Workouts"])
def get_history(db: Session = Depends(get_db)):
    return db.query(DBWorkout).filter(DBWorkout.is_active == False).order_by(DBWorkout.date_finished.desc()).all()

@app.post("/workouts/{workout_id}/exercises", response_model=ExerciseResponse, tags=["Workouts"])
def add_exercise(workout_id: int, exercise: ExerciseCreate, db: Session = Depends(get_db)):
    workout = db.query(DBWorkout).filter(DBWorkout.id == workout_id, DBWorkout.is_active == True).first()
    if not workout:
        raise HTTPException(status_code=400, detail="Treino não está ativo ou não existe.")
    
    db_exercise = DBExercise(name=exercise.name, workout_id=workout_id)
    db.add(db_exercise)
    db.commit()
    db.refresh(db_exercise)
    return db_exercise

# --- Rotas de Exercises e Sets ---
@app.post("/exercises/{exercise_id}/sets", response_model=SetResponse, tags=["Exercises & Sets"])
def add_set(exercise_id: int, set_data: SetCreate, db: Session = Depends(get_db)):
    exercise = db.query(DBExercise).filter(DBExercise.id == exercise_id).first()
    if not exercise or not exercise.workout.is_active:
        raise HTTPException(status_code=400, detail="Exercício inválido ou treino já finalizado.")
    
    db_set = DBSet(weight=set_data.weight, reps=set_data.reps, exercise_id=exercise_id)
    db.add(db_set)
    db.commit()
    db.refresh(db_set)
    return db_set

@app.get("/exercises/names", response_model=List[str], tags=["Exercises & Sets"])
def get_exercise_names(db: Session = Depends(get_db)):
    exercises = db.query(DBExercise.name).distinct().order_by(DBExercise.name).all()
    return [ex[0] for ex in exercises if ex[0]]

@app.get("/exercises/last-params", tags=["Exercises & Sets"])
def get_last_params(name: str, db: Session = Depends(get_db)):
    last_set = (
        db.query(DBSet)
        .join(DBExercise)
        .join(DBWorkout)
        .filter(DBExercise.name == name)
        .order_by(DBWorkout.date_created.desc(), DBSet.id.desc())
        .first()
    )
    
    if last_set:
        return {"weight": float(last_set.weight), "reps": int(last_set.reps)}
    return {"weight": 0.0, "reps": 1}

@app.delete("/sets/{set_id}", tags=["Exercises & Sets"])
def delete_set(set_id: int, db: Session = Depends(get_db)):
    db_set = db.query(DBSet).filter(DBSet.id == set_id).first()
    if not db_set:
        raise HTTPException(status_code=404, detail="Série não encontrada.")
    
    if not db_set.exercise.workout.is_active:
        raise HTTPException(status_code=400, detail="Não é possível alterar um treino já finalizado.")
        
    db.delete(db_set)
    db.commit()
    return {"message": "Série deletada com sucesso."}

@app.delete("/exercises/{exercise_id}", tags=["Exercises & Sets"])
def delete_exercise(exercise_id: int, db: Session = Depends(get_db)):
    exercise = db.query(DBExercise).filter(DBExercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercício não encontrado.")
        
    if not exercise.workout.is_active:
        raise HTTPException(status_code=400, detail="Não é possível alterar um treino já finalizado.")
        
    db.delete(exercise)
    db.commit()
    return {"message": "Exercício deletado com sucesso."}