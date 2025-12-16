"""Service to update manifest with billing and other post-export information."""
import logging
import json
import zipfile
import io
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def update_manifest_billing(
    manifest: Dict[str, Any],
    payment_provider: str,
    payment_status: str,
    payment_reference: Optional[str] = None,
    amount: Optional[float] = None,
    currency: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update manifest with billing information.
    
    Args:
        manifest: Manifest dictionary
        payment_provider: Payment provider (stripe, paypal, none)
        payment_status: Payment status (unpaid, pending, paid, refunded, failed)
        payment_reference: Optional payment reference
        amount: Optional amount
        currency: Optional currency
    
    Returns:
        Updated manifest
    """
    manifest["billing"] = {
        "payment_provider": payment_provider,
        "payment_status": payment_status
    }
    
    if payment_reference:
        manifest["billing"]["payment_reference"] = payment_reference
    
    if amount is not None:
        manifest["billing"]["amount"] = amount
    
    if currency:
        manifest["billing"]["currency"] = currency
    
    return manifest


def update_bundle_manifest(
    bundle_data: bytes,
    manifest_updates: Dict[str, Any]
) -> bytes:
    """
    Update manifest in bundle ZIP file.
    
    Args:
        bundle_data: Original bundle ZIP bytes
        manifest_updates: Updates to apply to manifest
    
    Returns:
        Updated bundle ZIP bytes
    """
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(io.BytesIO(bundle_data), 'r') as source_zip:
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as target_zip:
            # Copy all files except manifest.json
            for file_info in source_zip.filelist:
                if file_info.filename != "manifest.json":
                    target_zip.writestr(file_info, source_zip.read(file_info.filename))
            
            # Read and update manifest
            if "manifest.json" in [f.filename for f in source_zip.filelist]:
                manifest_json = source_zip.read("manifest.json")
                manifest = json.loads(manifest_json.decode('utf-8'))
                
                # Apply updates
                manifest.update(manifest_updates)
                
                # Write updated manifest
                updated_manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
                target_zip.writestr("manifest.json", updated_manifest_json.encode('utf-8'))
            else:
                # Create new manifest if not present
                manifest = manifest_updates
                manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False)
                target_zip.writestr("manifest.json", manifest_json.encode('utf-8'))
    
    buffer.seek(0)
    return buffer.getvalue()

