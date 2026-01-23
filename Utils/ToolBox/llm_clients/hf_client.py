from __future__ import annotations

import os
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, logging as hf_logging
from transformers.utils import logging as hf_utils_logging


def quiet_hf() -> None:
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_NO_ADVISORY_WARNINGS", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    hf_logging.set_verbosity_error()
    try:
        hf_utils_logging.disable_progress_bar()
    except Exception:
        pass
    logging.getLogger("transformers").setLevel(logging.ERROR)
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


@dataclass
class HFClient:
    model_id: str
    device: str = "auto"
    dtype: str = "auto"

    def __post_init__(self):
        quiet_hf()

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, use_fast=True)

        torch_dtype = None
        if self.dtype == "float16":
            torch_dtype = torch.float16
        elif self.dtype == "bfloat16":
            torch_dtype = torch.bfloat16
        elif self.dtype == "float32":
            torch_dtype = torch.float32

        device_map = "auto" if self.device == "auto" else None
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            torch_dtype=torch_dtype,
            device_map=device_map,
            low_cpu_mem_usage=True,
        )
        if self.device in ("cpu", "cuda", "mps"):
            self.model.to(self.device)
        self.model.eval()

    @torch.inference_mode()
    def generate(self, prompt: str, gen: Dict[str, Any]) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt")
        inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        out = self.model.generate(
            **inputs,
            max_new_tokens=int(gen.get("max_new_tokens", 220)),
            do_sample=float(gen.get("temperature", 0.2)) > 0,
            temperature=float(gen.get("temperature", 0.2)),
            top_p=float(gen.get("top_p", 0.95)),
            repetition_penalty=float(gen.get("repetition_penalty", 1.0)),
            pad_token_id=self.tokenizer.eos_token_id,
        )
        text = self.tokenizer.decode(out[0], skip_special_tokens=True)
        if text.startswith(prompt):
            return text[len(prompt):].strip()
        return text.strip()