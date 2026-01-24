#!/usr/bin/env python3
"""
Main entry point for interactive documentation assistant.
Optimized for Google Colab T4 GPU.
"""

import os
import argparse

# Reduce HF/Transformers download and warning noise
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from chat import Assistant

# Default model configuration
DEFAULT_MODEL = "Qwen/Qwen2.5-Coder-1.5B-Instruct"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Interactive Documentation Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start interactive chat
  python main.py
  
  # Specify model
  python main.py --model Qwen/Qwen2.5-Coder-3B-Instruct
  
  # Use CPU instead of GPU
  python main.py --device cpu
  
  # Disable quantization (requires more memory)
  python main.py --no-quantize
        """
    )
    
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"HuggingFace model ID (default: {DEFAULT_MODEL})",
    )
    
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda", "mps"],
        help="Device to use (default: auto)",
    )
    
    parser.add_argument(
        "--no-quantize",
        action="store_true",
        help="Disable 4-bit quantization (uses more memory)",
    )
    
    args = parser.parse_args()
    
    # Create and start assistant
    assistant = Assistant(
        model_id=args.model,
        device=args.device,
        quantize=not args.no_quantize,
    )
    
    assistant.start()


if __name__ == "__main__":
    main()
