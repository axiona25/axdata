"""Connector modules for external data sources."""
from connectors.registry import register_connector, get_connector, list_connectors

# MVP Indispensabili
from connectors.worldbank import WorldBankConnector
from connectors.eurostat import EurostatConnector
from connectors.pubmed import PubMedConnector
from connectors.imf import IMFConnector
from connectors.oecd import OECDConnector
from connectors.un_data import UNDataConnector
from connectors.istat import ISTATConnector
from connectors.clinicaltrials import ClinicalTrialsConnector
from connectors.who_gho import WHOGHOConnector
from connectors.openml import OpenMLConnector

# Estensione Forte
from connectors.ecb import ECBConnector
from connectors.cdc import CDCConnector
from connectors.ilo import ILOConnector
from connectors.wid import WIDConnector
from connectors.noaa import NOAAConnector
from connectors.copernicus import CopernicusConnector
from connectors.nasa import NASAConnector
from connectors.cern_opendata import CERNOpenDataConnector
from connectors.pangaea import PANGAEAConnector
from connectors.esa import ESAConnector
from connectors.eu_clinical_trials import EUClinicalTrialsConnector
from connectors.un_population import UNPopulationConnector
from connectors.global_carbon import GlobalCarbonConnector
from connectors.wmo import WMOConnector
from connectors.wolfram import WolframConnector
from connectors.uci_ml import UCIMLConnector

# Register all connectors
# MVP Indispensabili
register_connector(WorldBankConnector())
register_connector(EurostatConnector())
register_connector(PubMedConnector())
register_connector(IMFConnector())
register_connector(OECDConnector())
register_connector(UNDataConnector())
register_connector(ISTATConnector())
register_connector(ClinicalTrialsConnector())
register_connector(WHOGHOConnector())
register_connector(OpenMLConnector())

# Estensione Forte
register_connector(ECBConnector())
register_connector(CDCConnector())
register_connector(ILOConnector())
register_connector(WIDConnector())
register_connector(NOAAConnector())
register_connector(CopernicusConnector())
register_connector(NASAConnector())
register_connector(CERNOpenDataConnector())
register_connector(PANGAEAConnector())
register_connector(ESAConnector())
register_connector(EUClinicalTrialsConnector())
register_connector(UNPopulationConnector())
register_connector(GlobalCarbonConnector())
register_connector(WMOConnector())
register_connector(WolframConnector())
register_connector(UCIMLConnector())

__all__ = [
    "register_connector",
    "get_connector",
    "list_connectors",
    # MVP Indispensabili
    "WorldBankConnector",
    "EurostatConnector",
    "PubMedConnector",
    "IMFConnector",
    "OECDConnector",
    "UNDataConnector",
    "ISTATConnector",
    "ClinicalTrialsConnector",
    "WHOGHOConnector",
    "OpenMLConnector",
    # Estensione Forte
    "ECBConnector",
    "CDCConnector",
    "ILOConnector",
    "WIDConnector",
    "NOAAConnector",
    "CopernicusConnector",
    "NASAConnector",
    "CERNOpenDataConnector",
    "PANGAEAConnector",
    "ESAConnector",
    "EUClinicalTrialsConnector",
    "UNPopulationConnector",
    "GlobalCarbonConnector",
    "WMOConnector",
    "WolframConnector",
    "UCIMLConnector"
]
