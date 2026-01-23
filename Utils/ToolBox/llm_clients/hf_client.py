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
    # Reduce CUDA memory fragmentation
    os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")
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
    quantize: bool = False
    max_input_tokens: Optional[int] = None

    def __post_init__(self):
        quiet_hf()

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, use_fast=True)
        if not self.tokenizer.pad_token:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        torch_dtype = None
        if self.dtype == "float16":
            torch_dtype = torch.float16
        elif self.dtype == "bfloat16":
            torch_dtype = torch.bfloat16
        elif self.dtype == "float32":
            torch_dtype = torch.float32

        load_kwargs = {
            "low_cpu_mem_usage": True,
        }
        
        if self.quantize:
            # 4-bit quantization for memory efficiency
            try:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch_dtype or torch.float16,
                    bnb_4bit_use_double_quant=True,
                    bnb_4bit_quant_type="nf4",
                )
                load_kwargs["quantization_config"] = quantization_config
                load_kwargs["device_map"] = "auto"
            except ImportError:
                logging.warning("bitsandbytes not available, falling back to non-quantized loading")
                self.quantize = False
        
        if not self.quantize:
            # Non-quantized loading
            load_kwargs["torch_dtype"] = torch_dtype
            if self.device == "auto":
                load_kwargs["device_map"] = "auto"

        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_id,
            **load_kwargs
        )
        
        # Only call .to() if not using device_map (which handles placement)
        if not self.quantize and self.device in ("cpu", "cuda", "mps"):
            self.model.to(self.device)
        
        self.model.eval()

    @torch.inference_mode()
    def generate(self, prompt: str, gen: Dict[str, Any]) -> str:
        # Truncate input if max_input_tokens is set
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=False)
        
        if self.max_input_tokens is not None:
            input_ids = inputs["input_ids"][0]
            if len(input_ids) > self.max_input_tokens:
                # Truncate from the start to keep the most recent context
                input_ids = input_ids[-self.max_input_tokens:]
                inputs["input_ids"] = input_ids.unsqueeze(0)
                if "attention_mask" in inputs:
                    inputs["attention_mask"] = inputs["attention_mask"][:, -self.max_input_tokens:]
        
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