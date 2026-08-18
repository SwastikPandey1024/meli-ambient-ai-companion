"""
multimodal - Isolated Multimodal/Vision/OCR Provider Boundary (Future Phase)
=============================================================================
CRITICAL ARCHITECTURAL CONTRACT:
1. Do NOT couple vision or OCR pipelines into the core reasoning LLM (openai/gpt-oss-120b).
2. The core companion LLM is reserved exclusively for text reasoning, tool execution, and memory.
3. Multimodal adapters will run via an independent provider adapter interface when activated.
"""

from typing import Protocol, Optional, Dict, Any, List


class MultimodalProviderAdapter(Protocol):
    """Abstract protocol for future vision and OCR adapters."""
    
    @property
    def provider_name(self) -> str: ...
    
    @property
    def is_active(self) -> bool: ...
    
    async def process_image(self, image_bytes: bytes, prompt: str) -> Dict[str, Any]: ...
    
    async def extract_screen_text(self, image_bytes: bytes) -> str: ...
