"""Text/Document transformer - textual data format."""
from typing import Any, Dict, List, Optional
from axdata.transformers.base import BaseTransformer


class TextTransformer(BaseTransformer):
    """Transform data into text/document format."""
    
    def __init__(self):
        super().__init__("text")
    
    def transform(
        self,
        raw_data: List[Dict[str, Any]],
        ds_spec: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Transform to text/document format.
        
        Rules:
        - Extract full-text
        - Enrich with metadata
        - Deduplicate
        - Versioning
        """
        if not raw_data:
            return []
        
        transformed = []
        seen_texts = set()  # For deduplication
        
        for record in raw_data:
            # Extract text content
            text = self._extract_text(record)
            if not text:
                continue
            
            # Deduplicate
            text_hash = hash(text)
            if text_hash in seen_texts:
                continue
            seen_texts.add(text_hash)
            
            # Build document record
            doc = {
                "document_id": record.get("id") or record.get("document_id") or f"doc_{len(transformed)}",
                "text": text,
                "source": record.get("source") or record.get("source_id"),
                "language": self._detect_language(text),
                "date": record.get("date") or record.get("published_date") or record.get("timestamp"),
                "license": record.get("license"),
                "metadata": {
                    "title": record.get("title"),
                    "author": record.get("author"),
                    "url": record.get("url"),
                    "doi": record.get("doi")
                }
            }
            
            transformed.append(doc)
        
        return transformed
    
    def _extract_text(self, record: Dict[str, Any]) -> str:
        """Extract text content from record."""
        # Try common text field names
        text_fields = ['text', 'content', 'abstract', 'body', 'description', 'summary']
        
        for field in text_fields:
            if field in record and record[field]:
                text = record[field]
                if isinstance(text, str):
                    return text
                elif isinstance(text, list):
                    return ' '.join(str(t) for t in text)
        
        # Fallback: concatenate all string values
        text_parts = []
        for key, value in record.items():
            if isinstance(value, str) and len(value) > 10:  # Skip short strings (likely IDs)
                text_parts.append(value)
        
        return ' '.join(text_parts) if text_parts else ""
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection (can be enhanced)."""
        # Simple heuristic: check for common Italian words
        italian_words = ['il', 'la', 'di', 'che', 'e', 'un', 'una', 'per', 'in', 'con']
        text_lower = text.lower()
        italian_count = sum(1 for word in italian_words if word in text_lower)
        
        if italian_count > 3:
            return "it"
        
        # Default to English
        return "en"
