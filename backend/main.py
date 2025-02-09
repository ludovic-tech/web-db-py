from fastapi import FastAPI, Depends, File, UploadFile
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os
import json
import logging
import sys
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Autoriser toutes les origines (tu peux restreindre à ton domaine si besoin)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Remplace "*" par ["http://formation.ludovic.io"] si besoin
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"], # Autorise toutes les méthodes HTTP (GET, POST, DELETE...)
    allow_headers=["*"],  # Autorise tous les headers
)

# Définir le niveau de logs dynamiquement
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, log_level),
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)  # Rediriger les logs vers la console (Docker)
    ]
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@db/mydatabase")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)

Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/items/")
def create_item(name: str, description: str, db: Session = Depends(get_db)):
    logger.info(f"Ajout d'un nouvel item: name={name}, description={description}")
    item = Item(name=name, description=description)
    db.add(item)
    db.commit()
    db.refresh(item)
    logger.info(f"Item ajouté avec succès: {item}")
    return item

@app.get("/items/")
def read_items(db: Session = Depends(get_db)):
    items = db.query(Item).all()
    logger.info(f"Récupération des items: {items}")
    return items

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item:
        logger.info(f"Suppression de l'item: {item}")
        db.delete(item)
        db.commit()
        return {"message": "Item deleted"}
    logger.warning(f"Tentative de suppression d'un item non existant: ID={item_id}")
    return {"error": "Item not found"}

@app.post("/upload-json/")
def upload_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = file.file.read()
    data = json.loads(contents)
    logger.info(f"Importation de {len(data)} éléments depuis un fichier JSON")
    for entry in data:
        item = Item(name=entry["name"], description=entry["description"])
        db.add(item)
    db.commit()
    logger.info("Importation réussie")
    return {"message": "JSON data imported successfully"}
