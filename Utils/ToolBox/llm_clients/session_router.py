from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

from Utils.ToolBox.llm_clients.hf_client import HFClient


logger = logging.getLogger(__name__)


RunMode = Literal["shared", "per_agent"]


@dataclass
class SessionRouter:
    """
    Manages LLM clients for multi-agent pipeline with different strategies:
    - shared mode: single model for all roles
    - per_agent mode: lazy load different models by role
    
    Args:
        run_mode: "shared" (single model) or "per_agent" (role-specific models)
        shared_model_id: model ID when run_mode="shared"
        agent_models: dict mapping role -> model_id when run_mode="per_agent"
        device: "auto", "cpu", "cuda", or "mps"
        dtype: "auto", "float16", "bfloat16", or "float32"
        keep_loaded: if True, cache models; if False, evict after each role usage
        quantize: if True, use 4-bit quantization (requires bitsandbytes)
        max_input_tokens: maximum input tokens before truncation (None = no limit)
    """
    run_mode: RunMode = "shared"
    shared_model_id: Optional[str] = None
    agent_models: Optional[Dict[str, str]] = None
    device: str = "auto"
    dtype: str = "auto"
    keep_loaded: bool = True
    quantize: bool = False
    max_input_tokens: Optional[int] = None
    
    def __post_init__(self):
        self._clients: Dict[str, HFClient] = {}
        self._current_role: Optional[str] = None
        
        if self.run_mode == "shared":
            if not self.shared_model_id:
                raise ValueError("shared_model_id required when run_mode='shared'")
            # Pre-load shared model
            logger.info(f"Loading shared model: {self.shared_model_id}")
            self._clients["shared"] = HFClient(
                model_id=self.shared_model_id,
                device=self.device,
                dtype=self.dtype,
                quantize=self.quantize,
                max_input_tokens=self.max_input_tokens,
            )
        elif self.run_mode == "per_agent":
            if not self.agent_models:
                raise ValueError("agent_models required when run_mode='per_agent'")
            # Lazy load per-agent models on first use
            logger.info(f"Per-agent mode with models: {self.agent_models}")
        else:
            raise ValueError(f"Invalid run_mode: {self.run_mode}")
    
    def get_client(self, role: str) -> HFClient:
        """Get or create HFClient for the given role."""
        if self.run_mode == "shared":
            return self._clients["shared"]
        
        # per_agent mode
        if role not in self._clients:
            if role not in self.agent_models:
                raise ValueError(f"No model configured for role: {role}")
            
            model_id = self.agent_models[role]
            logger.info(f"Loading model for role '{role}': {model_id}")
            self._clients[role] = HFClient(
                model_id=model_id,
                device=self.device,
                dtype=self.dtype,
                quantize=self.quantize,
                max_input_tokens=self.max_input_tokens,
            )
        
        self._current_role = role
        return self._clients[role]
    
    def release_role(self, role: str) -> None:
        """Release model for role if keep_loaded=False."""
        if not self.keep_loaded and role in self._clients and self.run_mode == "per_agent":
            logger.info(f"Releasing model for role: {role}")
            del self._clients[role]
            # Force garbage collection
            import gc
            import torch
            gc.collect()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
    
    def cleanup(self) -> None:
        """Release all models."""
        logger.info("Cleaning up all models")
        self._clients.clear()
        import gc
        import torch
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
