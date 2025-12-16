#!/usr/bin/env python3
"""Script per caricare il logo AXDATA nel database."""

import sys
from pathlib import Path

# Aggiungi il percorso del backend al PYTHONPATH
backend_path = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(backend_path))

from db.session import SessionLocal
from db.models.app_asset import AppAsset

def load_logo():
    """Carica il logo AXDATA nel database."""
    project_root = Path(__file__).resolve().parents[2]
    logo_path = project_root / "UI" / "Logo Axdata.png"
    
    if not logo_path.exists():
        print(f"❌ Logo non trovato in: {logo_path}")
        return False
    
    db = SessionLocal()
    try:
        # Verifica se il logo esiste già
        existing = db.query(AppAsset).filter(AppAsset.key == "logo").first()
        
        if existing:
            # Aggiorna il logo esistente
            data = logo_path.read_bytes()
            existing.data = data
            existing.content_type = "image/png"
            db.commit()
            print(f"✅ Logo AXDATA aggiornato nel database")
            return True
        else:
            # Crea nuovo logo
            data = logo_path.read_bytes()
            db.add(AppAsset(key="logo", content_type="image/png", data=data))
            db.commit()
            print(f"✅ Logo AXDATA caricato nel database da: {logo_path}")
            return True
    except Exception as e:
        db.rollback()
        print(f"❌ Errore nel caricamento del logo: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = load_logo()
    sys.exit(0 if success else 1)
