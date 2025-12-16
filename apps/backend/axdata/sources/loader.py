"""Source manifest loader with caching."""
from __future__ import annotations
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Cache for manifests
_manifest_cache: Optional[List[Dict[str, Any]]] = None
_manifest_cache_timestamp: Optional[datetime] = None
_manifest_cache_dir: Optional[Path] = None


def load_manifests(manifest_dir: str | Path, use_cache: bool = True) -> List[Dict[str, Any]]:
    """
    Load all source manifests from directory with caching.
    
    Args:
        manifest_dir: Directory containing manifest JSON files
        use_cache: Whether to use cache (default: True)
    
    Returns:
        List of source manifests
    """
    global _manifest_cache, _manifest_cache_timestamp, _manifest_cache_dir
    
    manifest_path = Path(manifest_dir)
    if not manifest_path.exists():
        logger.warning(f"Manifest directory {manifest_dir} does not exist")
        return []
    
    # Check cache
    if use_cache and _manifest_cache is not None and _manifest_cache_dir == manifest_path:
        # Check if any manifest files were modified
        try:
            max_mtime = max(
                (p.stat().st_mtime for p in manifest_path.glob("*.json")),
                default=0
            )
            
            if _manifest_cache_timestamp and max_mtime <= _manifest_cache_timestamp.timestamp():
                logger.debug(f"Using cached manifests ({len(_manifest_cache)} manifests)")
                return _manifest_cache
        except Exception as e:
            logger.warning(f"Error checking manifest cache: {e}. Reloading...")
    
    # Load manifests
    manifests = []
    for p in manifest_path.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                manifest = json.load(f)
                manifests.append(manifest)
                logger.debug(f"Loaded manifest: {manifest.get('source_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Error loading manifest {p}: {e}")
    
    # Update cache
    if use_cache:
        _manifest_cache = manifests
        _manifest_cache_timestamp = datetime.now()
        _manifest_cache_dir = manifest_path
        logger.debug(f"Cached {len(manifests)} manifests")
    
    logger.info(f"Loaded {len(manifests)} source manifests")
    return manifests


def clear_manifest_cache():
    """Clear the manifest cache."""
    global _manifest_cache, _manifest_cache_timestamp, _manifest_cache_dir
    _manifest_cache = None
    _manifest_cache_timestamp = None
    _manifest_cache_dir = None
    logger.info("Manifest cache cleared")


def get_manifest_path() -> Path:
    """Get the default manifest directory path."""
    # Path relative to this file
    current_file = Path(__file__)
    return current_file.parent / "manifests"
