#!/usr/bin/env python3
"""
Test completo di tutti i connettori per verificare se le API esterne rispondono.
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Tuple
import time

# Load environment variables
project_root = Path(__file__).parent.parent
collector_env = project_root / "apps" / "collector" / ".env"

if collector_env.exists():
    load_dotenv(collector_env, override=True)

# Add paths
sys.path.insert(0, str(project_root / "apps" / "collector"))

# Colors
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
CYAN = '\033[0;36m'
NC = '\033[0m'

results = {
    "working": [],
    "failing": [],
    "timeout": [],
    "validation_error": []
}


def test_connector(name: str, query: Dict, timeout: int = 30) -> Tuple[bool, str, int]:
    """
    Test a single connector.
    
    Returns:
        (success, message, records_count)
    """
    try:
        from connectors.registry import get_connector
        from connectors.base import ConnectorOutput
        
        connector = get_connector(name)
        if not connector:
            return False, "Connettore non trovato", 0
        
        # Test validation
        if not connector.validate_query(query):
            return False, "Query non valida", 0
        
        # Test fetch with timeout
        start_time = time.time()
        try:
            result = connector.fetch(query)
            elapsed = time.time() - start_time
            
            if result and isinstance(result, ConnectorOutput):
                records_count = len(result.records) if result.records else 0
                if records_count > 0:
                    return True, f"OK ({records_count} record, {elapsed:.2f}s)", records_count
                else:
                    return False, f"Nessun record restituito ({elapsed:.2f}s)", 0
            else:
                return False, "Risultato non valido", 0
        except Exception as e:
            elapsed = time.time() - start_time
            error_msg = str(e)
            if "timeout" in error_msg.lower() or elapsed > timeout:
                return False, f"Timeout ({elapsed:.2f}s)", 0
            elif "HTTP" in error_msg or "status" in error_msg.lower():
                return False, f"Errore HTTP: {error_msg[:50]}", 0
            else:
                return False, f"Errore: {error_msg[:50]}", 0
    
    except Exception as e:
        return False, f"Errore import/test: {str(e)[:50]}", 0


def main():
    """Test all connectors."""
    print(f"\n{BLUE}{'='*70}{NC}")
    print(f"{BLUE}🧪 TEST COMPLETO CONNETTORI (26 fonti pubbliche){NC}")
    print(f"{BLUE}{'='*70}{NC}\n")
    
    try:
        from connectors.registry import list_connectors, get_connector
        
        all_connectors = sorted(list_connectors())
        print(f"{CYAN}Connettori trovati: {len(all_connectors)}{NC}\n")
        
        # Test queries per diversi tipi di connettori (corrette)
        test_queries = {
            "worldbank": {"indicator": "NY.GDP.MKTP.CD", "country": "US", "date": "2020:2022"},
            "eurostat": {"dataset_code": "demo_pjan", "filters": {"geo": ["IT"], "time": ["2020"], "sex": ["T"], "age": ["TOTAL"]}},  # Eurostat popolazione
            "pubmed": {"term": "covid-19", "retmax": 5},
            "imf": {"dataset": "IFS", "indicator": "NGDP_RPCH", "country": "US", "start_period": "2020", "end_period": "2022"},
            "oecd": {"dataset": "SNA_TABLE1", "filter": "USA", "startTime": "2020", "endTime": "2022"},
            "un_data": {"dataflow": "DF_UNDATA_POPULATION", "indicator": "SP.POP.TOTL", "country": "USA", "startTime": "2020", "endTime": "2020"},
            "istat": {"dataflow": "DCIS_POPRES1", "filter": "IT", "startTime": "2020", "endTime": "2022"},
            "clinicaltrials": {"query": "covid-19", "pageSize": 5},
            "who_gho": {"indicator": "WHOSIS_000001"},  # WHO GHO - indicator only
            "openml": {"search": "classification", "limit": 5},
            "ecb": {"dataflow": "EXR", "key": "D.USD.EUR.SP00.A", "startPeriod": "2020-01", "endPeriod": "2022-12"},
            "cdc": {"dataset": "p5x4-u35c", "limit": 5},  # CDC dataset ID (Page Views by Minute)
            "ilo": {"dataflow": "DF_ILOSTAT_EES_SEX_AGE_RT_A", "indicator": "EES_SEX_AGE_RT_A", "country": "USA", "startPeriod": "2020", "endPeriod": "2022"},
            "wid": {"indicator": "sptinc992j", "country": "US", "year": "2020"},  # WID potrebbe richiedere formato specifico
            "noaa": {"dataset": "daily-summaries", "station": "USW00094728", "start_date": "2020-01-01", "end_date": "2020-12-31"},
            "copernicus": {"dataset": "reanalysis-era5-single-levels", "variable": "2m_temperature"},
            "nasa": {"dataset": "08-05-2010-uh60"},
            "cern_opendata": {"experiment": "CMS", "year": "2011"},
            "pangaea": {"search": "temperature", "limit": 5},
            "esa": {"mission": "Sentinel-2", "limit": 5},
            "eu_clinical_trials": {"query": "covid-19", "limit": 5},
            "un_population": {"indicator": "SP_POP_TOTL", "location": "840", "start_year": 2020, "end_year": 2022},  # 840 = USA
            "global_carbon": {"indicator": "fossil_fuel", "country": "USA"},
            "wmo": {"dataset": "temperature", "country": "USA"},
            "wolfram": {"search": "GDP", "limit": 5},
            "uci_ml": {"dataset": "iris"}
        }
        
        print(f"{YELLOW}Testando {len(all_connectors)} connettori...{NC}\n")
        
        for i, connector_name in enumerate(all_connectors, 1):
            print(f"[{i}/{len(all_connectors)}] {CYAN}{connector_name}{NC}... ", end="", flush=True)
            
            # Get test query for this connector
            query = test_queries.get(connector_name, {})
            
            # If no specific query, try a generic one
            if not query:
                connector = get_connector(connector_name)
                if connector:
                    # Try to create a minimal valid query
                    query = {"limit": 5}  # Generic fallback
            
            success, message, records = test_connector(connector_name, query)
            
            if success:
                print(f"{GREEN}✓{NC} {message}")
                results["working"].append((connector_name, records))
            else:
                if "timeout" in message.lower():
                    print(f"{RED}✗{NC} {message}")
                    results["timeout"].append((connector_name, message))
                elif "non valida" in message.lower() or "validation" in message.lower():
                    print(f"{YELLOW}⚠{NC} {message}")
                    results["validation_error"].append((connector_name, message))
                else:
                    print(f"{RED}✗{NC} {message}")
                    results["failing"].append((connector_name, message))
            
            # Delay più lungo per evitare rate limiting (aumentato per API sensibili)
            time.sleep(3)
        
        # Summary
        print(f"\n{BLUE}{'='*70}{NC}")
        print(f"{BLUE}📊 RISULTATI{NC}")
        print(f"{BLUE}{'='*70}{NC}\n")
        
        total = len(all_connectors)
        working = len(results["working"])
        failing = len(results["failing"])
        timeout = len(results["timeout"])
        validation = len(results["validation_error"])
        
        print(f"{GREEN}✓ Funzionanti: {working}/{total} ({working/total*100:.1f}%){NC}")
        if results["working"]:
            print(f"  Connettori:")
            for name, records in results["working"]:
                print(f"    {GREEN}•{NC} {name} ({records} record)")
        
        if timeout > 0:
            print(f"\n{YELLOW}⏱ Timeout: {timeout}{NC}")
            for name, msg in results["timeout"]:
                print(f"    {YELLOW}•{NC} {name}: {msg}")
        
        if validation > 0:
            print(f"\n{YELLOW}⚠ Errori validazione: {validation}{NC}")
            for name, msg in results["validation_error"]:
                print(f"    {YELLOW}•{NC} {name}: {msg}")
        
        if failing > 0:
            print(f"\n{RED}✗ Non funzionanti: {failing}{NC}")
            for name, msg in results["failing"]:
                print(f"    {RED}•{NC} {name}: {msg[:60]}")
        
        print(f"\n{CYAN}Success Rate: {working/total*100:.1f}%{NC}\n")
        
        if working == total:
            print(f"{GREEN}✅ TUTTI I CONNETTORI FUNZIONANO!{NC}\n")
            return 0
        elif working >= total * 0.8:
            print(f"{YELLOW}⚠ La maggior parte dei connettori funziona ({working}/{total}){NC}\n")
            return 0
        else:
            print(f"{RED}❌ Alcuni connettori non funzionano ({working}/{total}){NC}\n")
            return 1
    
    except Exception as e:
        print(f"{RED}Errore durante il test: {e}{NC}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

