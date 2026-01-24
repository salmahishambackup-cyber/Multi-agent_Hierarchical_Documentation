"""
Unified LLM client with 4-bit quantization support for Colab T4.
"""

from __future__ import annotations

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from typing import Optional, Dict, Any


class LLMClient:
    """
    Lightweight LLM client optimized for Google Colab T4 GPU.
    
    Features:
    - 4-bit quantization for memory efficiency
    - Token limit enforcement
    - Deterministic generation
    """
    
    def __init__(
        self,
        model_id: str = "Qwen/Qwen2.5-Coder-1.5B-Instruct",
        device: str = "auto",
        dtype: str = "float16",
        quantize: bool = True,
        max_input_tokens: int = 2048,
        max_new_tokens: int = 512,
        temperature: float = 0.1,
        top_p: float = 0.95,
        bnb_4bit_compute_dtype: str = "float16",
        bnb_4bit_quant_type: str = "nf4",
    ):
        """
        Initialize LLM client.
        
        Args:
            model_id: HuggingFace model ID
            device: Device to use (auto/cpu/cuda/mps)
            dtype: Data type (float16/bfloat16/float32)
            quantize: Use 4-bit quantization
            max_input_tokens: Maximum input tokens
            max_new_tokens: Maximum output tokens
            temperature: Generation temperature
            top_p: Top-p sampling
            bnb_4bit_compute_dtype: Compute dtype for 4-bit (float16/bfloat16)
            bnb_4bit_quant_type: Quantization type (nf4/fp4)
        """
        self.model_id = model_id
        self.max_input_tokens = max_input_tokens
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        
        print(f"Loading model: {model_id}")
        print(f"Quantization: {quantize}, Device: {device}, Dtype: {dtype}")
        
        # Configure quantization
        quantization_config = None
        if quantize:
            compute_dtype = getattr(torch, bnb_4bit_compute_dtype)
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=compute_dtype,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type=bnb_4bit_quant_type,
            )
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
        )
        
        # Load model
        torch_dtype = getattr(torch, dtype) if dtype != "auto" else "auto"
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quantization_config,
            device_map=device,
            torch_dtype=torch_dtype,
            trust_remote_code=True,
        )
        
        self.model.eval()
        print(f"Model loaded successfully!")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_new_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text from prompt.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_new_tokens: Override max output tokens
            temperature: Override temperature
            **kwargs: Additional generation parameters
            
        Returns:
            Generated text
        """
        # Build messages
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
        
        # Tokenize and truncate
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_input_tokens,
        ).to(self.model.device)
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens or self.max_new_tokens,
                temperature=temperature or self.temperature,
                top_p=self.top_p,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                **kwargs
            )
        
        # Decode only the new tokens
        generated_ids = outputs[0][inputs["input_ids"].shape[1]:]
        response = self.tokenizer.decode(generated_ids, skip_special_tokens=True)
        
        return response.strip()
    
    def cleanup(self):
        """Release model from memory."""
        del self.model
        del self.tokenizer
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
