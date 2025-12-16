"""OpenAI service for chat and DatasetPlan generation."""
import json
import logging
from typing import Generator, Optional, List, Dict, Any
from openai import OpenAI
from core.config import settings
from schemas.dataset_plan import DatasetPlan, DATASET_PLAN_TOOL_SCHEMA

logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=settings.openai_api_key)


def chat_completion_stream(
    messages: List[Dict[str, str]],
    session_id: str,
    user_id: str
) -> Generator[str, None, None]:
    """
    Stream chat completion from OpenAI.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        session_id: Chat session ID for logging
        user_id: User ID for logging
    
    Yields:
        Token strings from OpenAI stream
    """
    try:
        # Prepare messages for OpenAI
        openai_messages = [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]
        
        # Add system message if not present
        if not any(msg.get("role") == "system" for msg in openai_messages):
            openai_messages.insert(0, {
                "role": "system",
                "content": """You are an intelligent dataset creation assistant for AXDATA. Your role is to help researchers create datasets by understanding their requirements and automatically generating structured dataset plans.

IMPORTANT CONTEXT - YOU ALREADY HAVE ACCESS TO:
1. **26 Pre-configured Data Sources**: The system has access to these public data sources with APIs already configured:
   - Economics: worldbank, eurostat, imf, ecb, oecd, wid, ilo
   - Demography: istat, un_data, un_population, who_gho
   - Biomedical: pubmed, clinicaltrials, eu_clinical_trials, cdc, who_gho
   - Physics/Science: cern_opendata, nasa, esa, noaa, copernicus, wmo, global_carbon, pangaea
   - Math/ML: openml, uci_ml, wolfram
   
2. **Automatic Format Handling**: Output formats (CSV, JSON, Parquet) are automatically handled by the system. You don't need to ask about formats.

3. **Automatic Transformations**: Data normalization, deduplication, and transformations are automatically applied by the pipeline based on the domain.

4. **Automatic Documentation**: Metadata, manifest.json, and data dictionaries are automatically generated. You don't need to ask about documentation.

YOUR JOB:
1. **FIRST**: Analyze the user's request and explain what you will do:
   - Describe what dataset you will create
   - Explain which data sources you will use and why (e.g., "Userò ISTAT perché è la fonte ufficiale italiana per dati demografici regionali")
   - Explain what data you will collect (variables, time range, geographic scope)
   - Explain how the dataset will be structured
   
2. **THEN**: After explaining, generate the DatasetPlan using the create_dataset_plan tool

3. **IMPORTANT**: Always provide a clear explanation BEFORE generating the plan. The user needs to understand what will be created.

4. Only ask clarifying questions about the DATASET CONTENT itself if truly needed:
   * Specific variables/indicators needed (e.g., "Vuoi popolazione totale, densità, o entrambe?")
   * Time granularity (daily, monthly, yearly)
   * Geographic filters (specific regions, countries, or all)

5. DO NOT ask about:
   * Data sources (you have 26 available, choose the best ones automatically)
   * Output formats (handled automatically)
   * Transformations (handled automatically)
   * Documentation (generated automatically)

EXAMPLE RESPONSE FORMAT:
User: "Popolazione per regione in Italia dal 2015"

You should respond:
"Perfetto! Creerò un dataset sulla popolazione per regione in Italia dal 2015.

**Fonti dati:**
- Userò ISTAT (Istituto Nazionale di Statistica) come fonte principale, poiché è l'ente ufficiale italiano per le statistiche demografiche e fornisce dati affidabili a livello regionale.

**Cosa raccoglierò:**
- Dati sulla popolazione per ciascuna delle 20 regioni italiane
- Periodo: dal 2015 ad oggi
- Aggiornamenti annuali o mensili a seconda della disponibilità

**Struttura del dataset:**
Il dataset conterrà colonne per: regione, anno, popolazione totale, e eventuali metadati aggiuntivi.

Procedo con la creazione del piano?"

Then generate the DatasetPlan."""
            })
        
        # Call OpenAI with streaming
        stream = client.chat.completions.create(
            model=settings.openai_model,
            messages=openai_messages,
            tools=[DATASET_PLAN_TOOL_SCHEMA],
            tool_choice="auto",  # Let model decide when to use tool
            stream=True,
            temperature=0.7
        )
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
            
            # Handle tool calls
            if chunk.choices[0].delta.tool_calls:
                for tool_call in chunk.choices[0].delta.tool_calls:
                    if tool_call.function:
                        logger.info(f"Tool call detected: {tool_call.function.name}")
    
    except Exception as e:
        logger.error(f"Error in OpenAI chat stream: {e}", exc_info=True)
        yield f"\n\n[Error: {str(e)}]"


def chat_completion_with_tool(
    messages: List[Dict[str, str]],
    session_id: str,
    user_id: str
) -> tuple[str, Optional[DatasetPlan]]:
    """
    Get chat completion and extract DatasetPlan if tool is called.
    
    Returns:
        Tuple of (full_response, dataset_plan)
    """
    try:
        # Prepare messages
        openai_messages = [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]
        
        # Add system message if not present
        if not any(msg.get("role") == "system" for msg in openai_messages):
            openai_messages.insert(0, {
                "role": "system",
                "content": """You are an intelligent dataset creation assistant for AXDATA. Your role is to help researchers create datasets by understanding their requirements and automatically generating structured dataset plans.

IMPORTANT CONTEXT - YOU ALREADY HAVE ACCESS TO:
1. **26 Pre-configured Data Sources**: The system has access to these public data sources with APIs already configured:
   - Economics: worldbank, eurostat, imf, ecb, oecd, wid, ilo
   - Demography: istat, un_data, un_population, who_gho
   - Biomedical: pubmed, clinicaltrials, eu_clinical_trials, cdc, who_gho
   - Physics/Science: cern_opendata, nasa, esa, noaa, copernicus, wmo, global_carbon, pangaea
   - Math/ML: openml, uci_ml, wolfram
   
2. **Automatic Format Handling**: Output formats (CSV, JSON, Parquet) are automatically handled by the system. You don't need to ask about formats.

3. **Automatic Transformations**: Data normalization, deduplication, and transformations are automatically applied by the pipeline based on the domain.

4. **Automatic Documentation**: Metadata, manifest.json, and data dictionaries are automatically generated. You don't need to ask about documentation.

YOUR JOB:
1. **FIRST**: Analyze the user's request and explain what you will do:
   - Describe what dataset you will create
   - Explain which data sources you will use and why (e.g., "Userò ISTAT perché è la fonte ufficiale italiana per dati demografici regionali")
   - Explain what data you will collect (variables, time range, geographic scope)
   - Explain how the dataset will be structured
   
2. **THEN**: After explaining, generate the DatasetPlan using the create_dataset_plan tool

3. **IMPORTANT**: Always provide a clear explanation BEFORE generating the plan. The user needs to understand what will be created.

4. Only ask clarifying questions about the DATASET CONTENT itself if truly needed:
   * Specific variables/indicators needed (e.g., "Vuoi popolazione totale, densità, o entrambe?")
   * Time granularity (daily, monthly, yearly)
   * Geographic filters (specific regions, countries, or all)

5. DO NOT ask about:
   * Data sources (you have 26 available, choose the best ones automatically)
   * Output formats (handled automatically)
   * Transformations (handled automatically)
   * Documentation (generated automatically)

EXAMPLE RESPONSE FORMAT:
User: "Popolazione per regione in Italia dal 2015"

You should respond:
"Perfetto! Creerò un dataset sulla popolazione per regione in Italia dal 2015.

**Fonti dati:**
- Userò ISTAT (Istituto Nazionale di Statistica) come fonte principale, poiché è l'ente ufficiale italiano per le statistiche demografiche e fornisce dati affidabili a livello regionale.

**Cosa raccoglierò:**
- Dati sulla popolazione per ciascuna delle 20 regioni italiane
- Periodo: dal 2015 ad oggi
- Aggiornamenti annuali o mensili a seconda della disponibilità

**Struttura del dataset:**
Il dataset conterrà colonne per: regione, anno, popolazione totale, e eventuali metadati aggiuntivi.

Procedo con la creazione del piano?"

Then generate the DatasetPlan."""
            })
        
        # Call OpenAI
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=openai_messages,
            tools=[DATASET_PLAN_TOOL_SCHEMA],
            tool_choice="auto",
            temperature=0.7
        )
        
        message = response.choices[0].message
        full_response = message.content or ""
        dataset_plan = None
        
        # Check for tool calls
        if message.tool_calls:
            for tool_call in message.tool_calls:
                if tool_call.function.name == "create_dataset_plan":
                    try:
                        # Parse function arguments
                        args = json.loads(tool_call.function.arguments)
                        # Validate with Pydantic
                        dataset_plan = DatasetPlan(**args)
                        logger.info(f"DatasetPlan generated for session {session_id}: {dataset_plan.title}")
                    except Exception as e:
                        logger.error(f"Error parsing DatasetPlan: {e}", exc_info=True)
        
        return full_response, dataset_plan
    
    except Exception as e:
        logger.error(f"Error in OpenAI chat completion: {e}", exc_info=True)
        raise

