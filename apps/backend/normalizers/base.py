"""Base normalizer interface - abstract contract for all domain normalizers."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None


class BaseNormalizer(ABC):
    """
    Interfaccia astratta per tutti i normalizer di dominio.
    
    Ogni normalizer DEVE implementare questi metodi per trasformare
    dati grezzi raccolti dal Collector in dataset conformi agli standard
    internazionali del dominio (SDMX, CDISC, FAIR, OpenML, UN SDG, ecc.).
    
    Flusso:
        RAW DATA (API / CSV / JSON)
            ↓
        Normalizer (regole di dominio)
            ↓
        DATASET STANDARD + MANIFEST + DICTIONARY
    """
    
    domain: str  # es. "economics", "biomedical", "physics", "math", "demography"
    
    def __init__(self, domain: str):
        """
        Initialize normalizer with domain.
        
        Args:
            domain: Domain name (e.g., "economics", "biomedical")
        """
        self.domain = domain
    
    @abstractmethod
    def normalize(
        self,
        raw_assets: List[Dict[str, Any]],
        dataset_plan: Dict[str, Any]
    ) -> Any:
        """
        Trasforma i dati grezzi raccolti dal Collector
        in un dataset normalizzato secondo il dominio.
        
        Args:
            raw_assets: Lista di asset grezzi dal Collector
                Ogni asset contiene:
                - "data": dati grezzi (DataFrame, dict, list)
                - "source": informazioni sulla fonte
                - "metadata": metadati aggiuntivi
            dataset_plan: DatasetPlan completo con:
                - domain: dominio del dataset
                - sources: fonti dati
                - transformations: trasformazioni da applicare
                - outputs: formati di output
        
        Returns:
            DataFrame normalizzato (o List[Dict] se pandas non disponibile)
        """
        pass
    
    @abstractmethod
    def build_data_dictionary(
        self,
        dataframe: Any
    ) -> List[Dict[str, Any]]:
        """
        Genera la struttura colonne per data_dictionary.json.
        
        Args:
            dataframe: DataFrame normalizzato (o List[Dict])
        
        Returns:
            Lista di dizionari con informazioni su ogni colonna:
            [
                {
                    "name": "column_name",
                    "type": "string|integer|float|date|boolean",
                    "role": "dimension|measure|attribute",
                    "nullable": bool,
                    "description": "...",
                    "unit": "...",
                    ...
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def validate(
        self,
        dataframe: Any
    ) -> None:
        """
        Valida il dataset finale.
        
        Deve lanciare Exception se non conforme agli standard del dominio.
        
        Args:
            dataframe: DataFrame normalizzato (o List[Dict])
        
        Raises:
            ValueError: Se il dataset non è valido
        """
        pass
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Ritorna metadati sul normalizer (standard, versione, ecc.).
        
        Returns:
            Dizionario con metadati del normalizer
        """
        return {
            "domain": self.domain,
            "description": f"Normalizer for {self.domain} domain"
        }
