#!/usr/bin/env python3
"""
Script per configurare le API keys mancanti.
Aiuta l'utente a configurare tutte le chiavi necessarie.
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
project_root = Path(__file__).parent.parent
backend_env = project_root / "apps" / "backend" / ".env"
if backend_env.exists():
    load_dotenv(backend_env, override=True)

sys.path.insert(0, str(project_root / "apps" / "backend"))

from core.api_keys_validator import get_configuration_status, APIKeyStatus

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

API_KEYS_FILE = project_root / "API_KEYS.md"


def print_header():
    """Print header."""
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}🔑 CONFIGURAZIONE API KEYS{NC}")
    print(f"{BLUE}{'='*70}{NC}\n")


def print_status():
    """Print current configuration status."""
    status = get_configuration_status()
    
    print(f"{CYAN}📊 Stato Configurazione:{NC}")
    print(f"  Chiavi totali: {status['total_keys']}")
    print(f"  Chiavi valide: {GREEN}{status['valid_keys']}{NC}")
    print(f"  Chiavi mancanti: {RED}{status['missing_keys']}{NC}")
    print(f"  Completamento: {status['completion_percentage']:.1f}%\n")
    
    if status['missing']:
        print(f"{YELLOW}⚠ Chiavi mancanti o non valide:{NC}")
        for service, key_name, message in status['missing']:
            print(f"  {RED}•{NC} {service} - {key_name}: {message}")
        print()
    
    return status


def show_instructions():
    """Show instructions for configuring API keys."""
    print(f"{CYAN}📝 ISTRUZIONI:{NC}\n")
    
    print(f"{YELLOW}1. STRIPE:{NC}")
    print("   a. Vai su https://dashboard.stripe.com/test/apikeys")
    print("   b. Copia 'Secret key' (inizia con sk_test_)")
    print("   c. Copia 'Publishable key' (inizia con pk_test_)")
    print("   d. Per webhook: vai su Developers > Webhooks e crea un endpoint")
    print("   e. Copia il 'Signing secret' (inizia con whsec_)\n")
    
    print(f"{YELLOW}2. PAYPAL:{NC}")
    print("   a. Vai su https://developer.paypal.com/dashboard")
    print("   b. Crea una nuova app (Sandbox per test)")
    print("   c. Copia 'Client ID' e 'Secret'")
    print("   d. Per webhook: crea un webhook e copia l'ID\n")
    
    print(f"{YELLOW}3. AGGIORNA API_KEYS.md:{NC}")
    print(f"   Modifica il file: {API_KEYS_FILE}")
    print("   Aggiungi le chiavi nelle sezioni corrispondenti\n")


def generate_template():
    """Generate template for missing keys."""
    status = get_configuration_status()
    
    if not status['missing']:
        print(f"{GREEN}✅ Tutte le chiavi sono configurate!{NC}\n")
        return
    
    print(f"{CYAN}📋 Template per API_KEYS.md:{NC}\n")
    print("Aggiungi queste sezioni al file API_KEYS.md:\n")
    
    stripe_missing = [k for s, k, _ in status['missing'] if s == "Stripe"]
    paypal_missing = [k for s, k, _ in status['missing'] if s == "PayPal"]
    
    if stripe_missing:
        print("## 💳 Stripe")
        print()
        if "Secret Key" in stripe_missing:
            print("**Secret Key (Test)**:")
            print("```")
            print("sk_test_... (sostituisci con la tua chiave)")
            print("```")
            print()
        if "Publishable Key" in stripe_missing:
            print("**Publishable Key (Test)**:")
            print("```")
            print("pk_test_... (sostituisci con la tua chiave)")
            print("```")
            print()
        if "Webhook Secret" in stripe_missing:
            print("**Webhook Secret**:")
            print("```")
            print("whsec_... (sostituisci con il tuo webhook secret)")
            print("```")
            print()
        print("---")
        print()
    
    if paypal_missing:
        print("## 💰 PayPal")
        print()
        if "Client ID" in paypal_missing:
            print("**Client ID**:")
            print("```")
            print("... (sostituisci con il tuo Client ID)")
            print("```")
            print()
        if "Client Secret" in paypal_missing:
            print("**Client Secret**:")
            print("```")
            print("... (sostituisci con il tuo Client Secret)")
            print("```")
            print()
        if "Webhook ID" in paypal_missing:
            print("**Webhook ID**:")
            print("```")
            print("... (sostituisci con il tuo Webhook ID)")
            print("```")
            print()
        print("---")
        print()


def main():
    """Main function."""
    print_header()
    
    # Show current status
    status = print_status()
    
    # Show instructions
    show_instructions()
    
    # Generate template
    if status['missing_keys'] > 0:
        generate_template()
        print(f"\n{YELLOW}💡 Dopo aver aggiunto le chiavi, esegui di nuovo questo script per verificare.{NC}\n")
    else:
        print(f"\n{GREEN}✅ Tutte le chiavi sono configurate correttamente!{NC}\n")
    
    return 0 if status['missing_keys'] == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

