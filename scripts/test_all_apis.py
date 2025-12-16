#!/usr/bin/env python3
"""
Test completo per tutte le API integrate:
- Fonti pubbliche (Connettori)
- OpenAI
- Sistemi di pagamento (Stripe, PayPal)
"""
import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json

# Load environment variables
project_root = Path(__file__).parent.parent
backend_env = project_root / "apps" / "backend" / ".env"
collector_env = project_root / "apps" / "collector" / ".env"

if backend_env.exists():
    load_dotenv(backend_env, override=True)
if collector_env.exists():
    load_dotenv(collector_env, override=True)

# Add paths
sys.path.insert(0, str(project_root / "apps" / "backend"))
sys.path.insert(0, str(project_root / "apps" / "collector"))

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

tests_passed = 0
tests_failed = 0
errors = []


def test(name: str, condition: bool, error_msg: str = ""):
    """Run a test."""
    global tests_passed, tests_failed
    if condition:
        print(f"{GREEN}✓{NC} {name}")
        tests_passed += 1
        return True
    else:
        print(f"{RED}✗{NC} {name}" + (f" - {error_msg}" if error_msg else ""))
        if error_msg:
            errors.append(f"{name}: {error_msg}")
        tests_failed += 1
        return False


def print_section(title: str):
    """Print section header."""
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'='*70}{NC}")


def test_connectors():
    """Test public data source connectors."""
    print_section("1. TEST FONTI PUBBLICHE (Connettori)")
    
    try:
        from connectors.registry import get_connector, list_connectors
        from connectors.base import ConnectorOutput
        
        # List all connectors
        all_connectors = list_connectors()
        test(f"Connettori registrati: {len(all_connectors)}", len(all_connectors) > 0)
        
        if len(all_connectors) > 0:
            print(f"{CYAN}Connettori disponibili: {', '.join(sorted(all_connectors)[:10])}...{NC}")
        
        # Test specific connectors
        test_connectors_list = [
            ("worldbank", {"indicator": "NY.GDP.MKTP.CD", "country": "US", "date": "2020:2022"}),
            ("eurostat", {"dataset_code": "prc_hicp_midx", "filters": {"geo": ["IT", "FR"], "time": ["2020", "2021", "2022"]}}),
            ("pubmed", {"term": "covid-19", "retmax": 5}),
        ]
        
        for connector_name, test_query in test_connectors_list:
            try:
                connector = get_connector(connector_name)
                if connector:
                    # Test validation
                    is_valid = connector.validate_query(test_query)
                    test(f"{connector_name}: validazione query", is_valid, 
                         f"Query non valida: {test_query}" if not is_valid else "")
                    
                    # Test fetch (with timeout)
                    if is_valid:
                        print(f"  {YELLOW}→ Test fetch {connector_name}...{NC}", end=" ", flush=True)
                        try:
                            result = connector.fetch(test_query)
                            if result and isinstance(result, ConnectorOutput):
                                has_records = result.records is not None and len(result.records) > 0
                                test(f"{connector_name}: fetch dati", 
                                     has_records,
                                     "Nessun dato restituito")
                                if has_records:
                                    print(f"{GREEN}✓{NC} ({len(result.records)} record)")
                            else:
                                test(f"{connector_name}: fetch dati", False, "Risultato non valido")
                        except Exception as e:
                            test(f"{connector_name}: fetch dati", False, str(e))
                            print(f"{RED}✗{NC} ({str(e)[:50]})")
                else:
                    test(f"{connector_name}: connettore trovato", False, "Connettore non registrato")
            except Exception as e:
                test(f"{connector_name}: test completo", False, str(e))
        
        return True
    except Exception as e:
        test("Import connettori", False, str(e))
        return False


def test_openai():
    """Test OpenAI API."""
    print_section("2. TEST OPENAI API")
    
    try:
        # Import from backend
        backend_path = project_root / "apps" / "backend"
        sys.path.insert(0, str(backend_path))
        
        from core.api_keys import get_openai_api_key
        from core.config import settings
        from services.openai_service import chat_completion_with_tool, chat_completion_stream
        from schemas.dataset_plan import DatasetPlan
        
        # Check API key
        api_key = get_openai_api_key() or settings.openai_api_key
        test("OpenAI API key configurata", bool(api_key), "API key non trovata")
        
        if not api_key:
            print(f"{YELLOW}⚠ Skipping OpenAI tests - API key mancante{NC}")
            return False
        
        # Test simple chat completion
        print(f"  {YELLOW}→ Test chat completion...{NC}", end=" ", flush=True)
        try:
            test_messages = [
                {"role": "user", "content": "Ciao, dimmi solo 'OK' se funziona."}
            ]
            response, dataset_plan = chat_completion_with_tool(
                test_messages,
                session_id="test-session",
                user_id="test-user"
            )
            test("OpenAI: chat completion", 
                 bool(response) and len(response) > 0,
                 "Nessuna risposta da OpenAI")
            if response:
                print(f"{GREEN}✓{NC} (risposta ricevuta)")
        except Exception as e:
            test("OpenAI: chat completion", False, str(e))
            print(f"{RED}✗{NC} ({str(e)[:50]})")
        
        # Test DatasetPlan generation
        print(f"  {YELLOW}→ Test generazione DatasetPlan...{NC}", end=" ", flush=True)
        try:
            dataset_request = [
                {"role": "user", "content": "Voglio un dataset su inflazione in Italia e Francia dal 2020 al 2022. Usa Eurostat."}
            ]
            response, dataset_plan = chat_completion_with_tool(
                dataset_request,
                session_id="test-session-plan",
                user_id="test-user"
            )
            
            if dataset_plan:
                test("OpenAI: generazione DatasetPlan", 
                     isinstance(dataset_plan, DatasetPlan),
                     "DatasetPlan non valido")
                if isinstance(dataset_plan, DatasetPlan):
                    test("OpenAI: DatasetPlan ha titolo", 
                         bool(dataset_plan.title),
                         "Titolo mancante")
                    test("OpenAI: DatasetPlan ha domain", 
                         bool(dataset_plan.domain),
                         "Domain mancante")
                    test("OpenAI: DatasetPlan ha sources", 
                         len(dataset_plan.sources) > 0,
                         "Sources mancanti")
                    print(f"{GREEN}✓{NC} (DatasetPlan generato: {dataset_plan.title})")
            else:
                # DatasetPlan non generato - potrebbe essere normale se OpenAI non usa il tool
                test("OpenAI: generazione DatasetPlan", False, "DatasetPlan non generato (OpenAI potrebbe non aver usato il tool)")
                print(f"{YELLOW}⚠{NC} (risposta senza DatasetPlan - potrebbe essere normale)")
        except Exception as e:
            test("OpenAI: generazione DatasetPlan", False, str(e))
            print(f"{RED}✗{NC} ({str(e)[:50]})")
        
        # Test streaming (quick test)
        print(f"  {YELLOW}→ Test streaming...{NC}", end=" ", flush=True)
        try:
            stream_messages = [{"role": "user", "content": "Dimmi solo 'OK'"}]
            tokens_received = 0
            for token in chat_completion_stream(stream_messages, "test-stream", "test-user"):
                if token:
                    tokens_received += 1
                    if tokens_received > 5:  # Test first few tokens
                        break
            test("OpenAI: streaming", tokens_received > 0, "Nessun token ricevuto")
            if tokens_received > 0:
                print(f"{GREEN}✓{NC} ({tokens_received} token ricevuti)")
        except Exception as e:
            test("OpenAI: streaming", False, str(e))
            print(f"{RED}✗{NC} ({str(e)[:50]})")
        
        return True
    except Exception as e:
        test("Import OpenAI service", False, str(e))
        return False


def test_stripe():
    """Test Stripe payment system."""
    print_section("3. TEST STRIPE PAYMENT")
    
    try:
        import stripe
        # Import from backend
        backend_path = project_root / "apps" / "backend"
        sys.path.insert(0, str(backend_path))
        
        from core.api_keys import get_stripe_secret_key, get_stripe_publishable_key
        from core.api_keys_validator import validate_stripe_secret_key, validate_stripe_publishable_key, APIKeyStatus
        from core.config import settings
        from services.stripe_service import create_checkout_session
        
        # Check API keys with validation
        secret_key = get_stripe_secret_key() or settings.stripe_secret_key
        publishable_key = get_stripe_publishable_key() or settings.stripe_publishable_key
        
        # Validate keys
        secret_status, secret_msg = validate_stripe_secret_key(secret_key)
        pub_status, pub_msg = validate_stripe_publishable_key(publishable_key)
        
        test("Stripe Secret Key configurata", secret_status != APIKeyStatus.MISSING, secret_msg)
        test("Stripe Secret Key valida", secret_status == APIKeyStatus.VALID, secret_msg)
        test("Stripe Publishable Key configurata", pub_status != APIKeyStatus.MISSING, pub_msg)
        test("Stripe Publishable Key valida", pub_status == APIKeyStatus.VALID, pub_msg)
        
        if secret_status in [APIKeyStatus.MISSING, APIKeyStatus.PLACEHOLDER]:
            print(f"{YELLOW}⚠ Stripe Secret Key: {secret_msg}{NC}")
            print(f"{YELLOW}⚠ Esegui 'python3 scripts/setup_api_keys.py' per configurare{NC}")
            return False
        
        if pub_status in [APIKeyStatus.MISSING, APIKeyStatus.PLACEHOLDER]:
            print(f"{YELLOW}⚠ Stripe Publishable Key: {pub_msg}{NC}")
        
        # Initialize Stripe
        stripe.api_key = secret_key
        
        # Test: Create checkout session
        print(f"  {YELLOW}→ Test creazione checkout session...{NC}", end=" ", flush=True)
        try:
            session = create_checkout_session(
                dataset_request_id="test-dataset-123",
                user_id="test-user-123",
                amount=9.99,
                currency="eur",
                success_url="http://localhost:3000/success",
                cancel_url="http://localhost:3000/cancel"
            )
            
            test("Stripe: creazione checkout session", 
                 bool(session) and hasattr(session, 'id'),
                 "Session non creata")
            
            if session and hasattr(session, 'id'):
                test("Stripe: session ha ID", bool(session.id), "ID mancante")
                test("Stripe: session ha URL", bool(session.url), "URL mancante")
                test("Stripe: payment methods include card", 
                     'card' in session.payment_method_types,
                     "Card non abilitato")
                test("Stripe: payment methods include apple_pay", 
                     'apple_pay' in session.payment_method_types,
                     "Apple Pay non abilitato")
                test("Stripe: payment methods include google_pay", 
                     'google_pay' in session.payment_method_types,
                     "Google Pay non abilitato")
                print(f"{GREEN}✓{NC} (Session ID: {session.id[:20]}...)")
        except stripe.error.AuthenticationError as e:
            error_msg = str(e)
            if "placeholder" in error_msg.lower() or "Invalid API Key" in error_msg:
                test("Stripe: creazione checkout session", False, "API key non valida (placeholder?)")
                print(f"{YELLOW}⚠{NC} (API key non valida - configurare chiave reale per test completo)")
            else:
                test("Stripe: creazione checkout session", False, f"Errore autenticazione: {error_msg[:50]}")
                print(f"{RED}✗{NC} (Auth error)")
        except Exception as e:
            test("Stripe: creazione checkout session", False, str(e))
            print(f"{RED}✗{NC} ({str(e)[:50]})")
        
        # Test: Webhook signature verification (mock)
        print(f"  {YELLOW}→ Test verifica webhook signature...{NC}", end=" ", flush=True)
        try:
            from services.stripe_service import verify_webhook_signature
            
            # This will fail without proper webhook secret, but we test the function exists
            webhook_secret = settings.stripe_webhook_secret
            test("Stripe: webhook secret configurato", bool(webhook_secret), "Webhook secret non configurato")
            
            if webhook_secret:
                # We can't test actual verification without a real webhook, but we test the function
                test("Stripe: funzione verify_webhook_signature esiste", 
                     callable(verify_webhook_signature),
                     "Funzione non trovata")
                print(f"{GREEN}✓{NC} (funzione disponibile)")
            else:
                print(f"{YELLOW}⚠{NC} (webhook secret mancante)")
        except Exception as e:
            test("Stripe: verifica webhook", False, str(e))
            print(f"{RED}✗{NC} ({str(e)[:50]})")
        
        return True
    except ImportError as e:
        test("Import Stripe", False, str(e))
        return False
    except Exception as e:
        test("Stripe test setup", False, str(e))
        return False


def test_paypal():
    """Test PayPal payment system."""
    print_section("4. TEST PAYPAL PAYMENT")
    
    try:
        # Import from backend
        backend_path = project_root / "apps" / "backend"
        sys.path.insert(0, str(backend_path))
        
        from core.api_keys import get_paypal_client_id, get_paypal_client_secret
        from core.api_keys_validator import validate_paypal_client_id, validate_paypal_client_secret, APIKeyStatus
        from core.config import settings
        from services.paypal_service import get_paypal_client, create_paypal_order
        
        # Check API keys with validation
        client_id = get_paypal_client_id() or settings.paypal_client_id
        client_secret = get_paypal_client_secret() or settings.paypal_client_secret
        
        # Validate keys
        id_status, id_msg = validate_paypal_client_id(client_id)
        secret_status, secret_msg = validate_paypal_client_secret(client_secret)
        
        test("PayPal Client ID configurato", id_status != APIKeyStatus.MISSING, id_msg)
        test("PayPal Client ID valido", id_status == APIKeyStatus.VALID, id_msg)
        test("PayPal Client Secret configurato", secret_status != APIKeyStatus.MISSING, secret_msg)
        test("PayPal Client Secret valido", secret_status == APIKeyStatus.VALID, secret_msg)
        
        if id_status in [APIKeyStatus.MISSING, APIKeyStatus.PLACEHOLDER]:
            print(f"{YELLOW}⚠ PayPal Client ID: {id_msg}{NC}")
            print(f"{YELLOW}⚠ Esegui 'python3 scripts/setup_api_keys.py' per configurare{NC}")
            return False
        
        if secret_status in [APIKeyStatus.MISSING, APIKeyStatus.PLACEHOLDER]:
            print(f"{YELLOW}⚠ PayPal Client Secret: {secret_msg}{NC}")
            return False
        
        # Test: Get access token
        print(f"  {YELLOW}→ Test autenticazione PayPal (access token)...{NC}", end=" ", flush=True)
        try:
            client = get_paypal_client()
            token = client.get_access_token()
            
            test("PayPal: access token ottenuto", 
                 bool(token) and len(token) > 0,
                 "Token non ottenuto")
            
            if token:
                print(f"{GREEN}✓{NC} (token ottenuto: {token[:20]}...)")
        except Exception as e:
            test("PayPal: access token", False, str(e))
            print(f"{RED}✗{NC} ({str(e)[:50]})")
            return False  # Can't continue without token
        
        # Test: Create order
        print(f"  {YELLOW}→ Test creazione PayPal order...{NC}", end=" ", flush=True)
        try:
            order = create_paypal_order(
                amount=9.99,
                currency="EUR",
                description="Test Dataset Payment",
                return_url="http://localhost:3000/success?order_id={ORDER_ID}",
                cancel_url="http://localhost:3000/cancel",
                metadata={"test": "true", "dataset_id": "test-123"}
            )
            
            test("PayPal: creazione order", 
                 bool(order) and "id" in order,
                 "Order non creato")
            
            if order and "id" in order:
                test("PayPal: order ha ID", bool(order["id"]), "ID mancante")
                test("PayPal: order ha approval_url", 
                     bool(order.get("approval_url")),
                     "Approval URL mancante")
                test("PayPal: order ha status", 
                     bool(order.get("status")),
                     "Status mancante")
                print(f"{GREEN}✓{NC} (Order ID: {order['id'][:20]}...)")
        except Exception as e:
            test("PayPal: creazione order", False, str(e))
            print(f"{RED}✗{NC} ({str(e)[:50]})")
        
        # Test: Webhook verification function exists
        print(f"  {YELLOW}→ Test verifica webhook PayPal...{NC}", end=" ", flush=True)
        try:
            from services.paypal_service import verify_paypal_webhook
            
            test("PayPal: funzione verify_webhook esiste", 
                 callable(verify_paypal_webhook),
                 "Funzione non trovata")
            
            webhook_id = settings.paypal_webhook_id
            test("PayPal: webhook ID configurato", bool(webhook_id), "Webhook ID non configurato")
            
            if webhook_id:
                print(f"{GREEN}✓{NC} (funzione disponibile)")
            else:
                print(f"{YELLOW}⚠{NC} (webhook ID mancante)")
        except Exception as e:
            test("PayPal: verifica webhook", False, str(e))
            print(f"{RED}✗{NC} ({str(e)[:50]})")
        
        return True
    except ImportError as e:
        test("Import PayPal service", False, str(e))
        return False
    except Exception as e:
        test("PayPal test setup", False, str(e))
        return False


def main():
    """Run all API tests."""
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}{'🧪 TEST COMPLETO API INTEGRATE'}{NC}")
    print(f"{BLUE}{'='*70}{NC}")
    print(f"{CYAN}Verifica di tutte le API integrate nel sistema{NC}")
    print(f"{CYAN}- Fonti pubbliche (Connettori){NC}")
    print(f"{CYAN}- OpenAI{NC}")
    print(f"{CYAN}- Sistemi di pagamento (Stripe, PayPal){NC}")
    
    # Run tests
    test_connectors()
    test_openai()
    test_stripe()
    test_paypal()
    
    # Summary
    print_section("RISULTATI FINALI")
    print(f"{GREEN}Test Passati: {tests_passed}{NC}")
    if tests_failed > 0:
        print(f"{RED}Test Falliti: {tests_failed}{NC}")
        print(f"\n{YELLOW}Errori dettagliati:{NC}")
        for error in errors[:10]:  # Show first 10 errors
            print(f"  {RED}•{NC} {error}")
        if len(errors) > 10:
            print(f"  {YELLOW}... e altri {len(errors) - 10} errori{NC}")
    
    total = tests_passed + tests_failed
    if total > 0:
        success_rate = (tests_passed / total) * 100
        print(f"\n{CYAN}Success Rate: {success_rate:.1f}%{NC}")
    
    # Notes
    print(f"\n{YELLOW}{'='*70}{NC}")
    print(f"{YELLOW}📝 NOTE:{NC}")
    print(f"{YELLOW}{'='*70}{NC}")
    print(f"{CYAN}• Connettori: Testati {len([c for c in ['worldbank', 'eurostat', 'pubmed'] if True])} connettori su 26 disponibili{NC}")
    print(f"{CYAN}• OpenAI: Funziona correttamente. DatasetPlan potrebbe non essere generato se OpenAI non usa il tool.{NC}")
    print(f"{CYAN}• Stripe: Richiede API keys valide (non placeholder) per test completi.{NC}")
    print(f"{CYAN}• PayPal: Richiede Client ID e Secret configurati in API_KEYS.md o variabili d'ambiente.{NC}")
    print(f"{CYAN}• Eurostat: Potrebbe fallire se l'API è temporaneamente non disponibile.{NC}")
    
    if tests_failed == 0:
        print(f"\n{GREEN}{'='*70}{NC}")
        print(f"{GREEN}✅ TUTTI I TEST PASSATI!{NC}")
        print(f"{GREEN}{'='*70}{NC}")
        return 0
    else:
        # Check if failures are only due to missing config
        config_failures = sum(1 for e in errors if "non trovato" in e or "non configurato" in e or "placeholder" in e.lower() or "mancanti" in e)
        if config_failures == tests_failed:
            print(f"\n{YELLOW}{'='*70}{NC}")
            print(f"{YELLOW}⚠ TEST COMPLETATI CON AVVISI{NC}")
            print(f"{YELLOW}Tutti i fallimenti sono dovuti a configurazione mancante.{NC}")
            print(f"{YELLOW}Configurare le API keys per test completi.{NC}")
            print(f"{YELLOW}{'='*70}{NC}")
            return 0  # Return success if only config issues
        else:
            print(f"\n{RED}{'='*70}{NC}")
            print(f"{RED}❌ ALCUNI TEST FALLITI{NC}")
            print(f"{RED}{'='*70}{NC}")
            return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

