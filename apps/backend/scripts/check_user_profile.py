#!/usr/bin/env python3
"""Script per verificare i dati del profilo utente nel database."""
import sys
import os

# Aggiungi il path del backend al PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import text
from db.session import SessionLocal
from db.models.user import User, UserProfile

# Importa tutti i modelli per evitare errori di relazione
from db.models import user, dataset, payment, invoice, package, chat, audit_log, app_asset

def check_user_profile(email: str):
    """Verifica i dati del profilo utente per una data email."""
    db: Session = SessionLocal()
    try:
        # Trova l'utente per email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"❌ Utente con email '{email}' non trovato nel database.")
            return
        
        print(f"\n✅ Utente trovato:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Attivo: {user.is_active}")
        print(f"   Verificato: {user.is_verified}")
        print(f"   Creato il: {user.created_at}")
        
        # Trova il profilo
        profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
        
        if not profile:
            print(f"\n⚠️  Profilo non trovato per l'utente '{email}'.")
            print(f"   Questo spiega perché vedi '{email.split('@')[0]}' invece del nome completo.")
            return
        
        print(f"\n✅ Profilo trovato:")
        print(f"   ID Profilo: {profile.id}")
        print(f"   User ID: {profile.user_id}")
        print(f"   First Name: {profile.first_name or '(vuoto)'}")
        print(f"   Last Name: {profile.last_name or '(vuoto)'}")
        print(f"   Organization: {profile.organization or '(vuoto)'}")
        print(f"   Creato il: {profile.created_at}")
        print(f"   Aggiornato il: {profile.updated_at}")
        
        if profile.first_name and profile.last_name:
            full_name = f"{profile.first_name} {profile.last_name}"
            print(f"\n✅ Nome completo nel database: '{full_name}'")
            print(f"   Dovresti vedere questo nome nella dashboard.")
        else:
            print(f"\n⚠️  First Name o Last Name sono vuoti nel database.")
            print(f"   Per questo motivo vedi '{email.split('@')[0]}' come fallback.")
            if not profile.first_name:
                print(f"   - First Name è NULL/vuoto")
            if not profile.last_name:
                print(f"   - Last Name è NULL/vuoto")
        
    except Exception as e:
        print(f"❌ Errore durante la verifica: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    email = "r.amoroso80@gmail.com"  # Email dell'utente da verificare
    if len(sys.argv) > 1:
        email = sys.argv[1]
    
    print(f"🔍 Verifica profilo utente per: {email}\n")
    check_user_profile(email)
