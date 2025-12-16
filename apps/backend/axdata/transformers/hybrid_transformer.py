"""Hybrid/Knowledge-Enriched transformer - data + semantic enrichment."""
from typing import Any, Dict, List, Optional
from axdata.transformers.base import BaseTransformer


class HybridTransformer(BaseTransformer):
    """Transform data into hybrid/knowledge-enriched format."""
    
    def __init__(self):
        super().__init__("hybrid")
    
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform to hybrid format.
        
        Rules:
        - Keep structured data
        - Add semantic relations
        - Add ontologies
        - Add automatic tags
        """
        if not raw_data:
            return []
        
        transformed = []
        
        for record in raw_data:
            # Keep original structured data
            enriched = dict(record)
            
            # Add semantic tags (simple keyword extraction)
            tags = self._extract_tags(record)
            enriched['semantic_tags'] = tags
            
            # Add entity mentions (simple NER simulation)
            entities = self._extract_entities(record)
            enriched['entities'] = entities
            
            # Add relations (placeholder - would use real NER/LLM)
            enriched['relations'] = []
            
            # Add ontology links (placeholder)
            enriched['ontology_links'] = []
            
            transformed.append(enriched)
        
        return transformed
    
    def _extract_tags(self, record: Dict[str, Any]) -> List[str]:
        """Extract semantic tags from record."""
        tags = []
        
        # Extract from text fields
        text_fields = ['text', 'content', 'description', 'title', 'abstract']
        all_text = ' '.join(
            str(record.get(field, ''))
            for field in text_fields
            if record.get(field)
        )
        
        # Simple keyword extraction (can be enhanced with real NLP)
        keywords = ['health', 'economy', 'climate', 'research', 'data', 'analysis']
        for keyword in keywords:
            if keyword.lower() in all_text.lower():
                tags.append(keyword)
        
        # Add tags from categorical fields
        for key, value in record.items():
            if isinstance(value, str) and len(value) < 50:  # Likely categorical
                tags.append(f"{key}:{value}")
        
        return tags[:10]  # Limit to 10 tags
    
    def _extract_entities(self, record: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract named entities (simplified)."""
        entities = []
        
        # Look for common entity patterns
        entity_fields = {
            'person': ['author', 'researcher', 'name'],
            'organization': ['organization', 'institution', 'company'],
            'location': ['country', 'region', 'city', 'location'],
            'date': ['date', 'year', 'timestamp']
        }
        
        for entity_type, fields in entity_fields.items():
            for field in fields:
                if field in record and record[field]:
                    entities.append({
                        "type": entity_type,
                        "value": str(record[field]),
                        "field": field
                    })
        
        return entities
