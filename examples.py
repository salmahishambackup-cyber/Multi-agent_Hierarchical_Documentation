#!/usr/bin/env python3
"""
Example usage of the Multi-Agent Hierarchical Documentation pipeline.
Demonstrates different configuration modes for Colab T4 GPU.
"""

from pathlib import Path

# Example 1: Basic usage with shared model (recommended for most cases)
def example_basic():
    """
    Most common usage: single quantized model for all agents.
    Memory-efficient for Colab T4.
    """
    from main import run_pipeline
    
    result = run_pipeline(
        repo_root="/content/MyProject",
        artifacts_dir="/content/Artifacts",
        model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
        
        # Memory optimization (default settings)
        quantize=True,              # 4-bit quantization
        max_input_tokens=2048,      # Truncate long prompts
        
        # Docstring mode
        docstring_mode="modules_only",  # Only module-level docs
        
        # Output
        generate_readme=True,       # Generate README.md
        cleanup_cache=True,
        debug=True,
    )
    print(result)


# Example 2: Per-agent models with different sizes
def example_per_agent():
    """
    Use different models for different roles.
    Useful when you want lighter models for simpler tasks.
    """
    from main import run_pipeline
    
    result = run_pipeline(
        repo_root="/content/MyProject",
        artifacts_dir="/content/Artifacts",
        
        # Per-agent configuration
        run_mode="per_agent",
        agent_models={
            "writer": "Qwen/Qwen2.5-Coder-3B-Instruct",
            "critic": "Qwen/Qwen2.5-Coder-1.5B-Instruct",  # Lighter
            "readme": "Qwen/Qwen2.5-Coder-3B-Instruct",
        },
        
        # Unload models after each role to save memory
        keep_loaded=False,
        quantize=True,
        max_input_tokens=2048,
        
        # Full documentation
        docstring_mode="symbols_and_modules",
        
        debug=True,
    )
    print(result)


# Example 3: Reuse router across multiple projects
def example_reuse_router():
    """
    Create router once and reuse for multiple projects.
    Avoids reloading the model multiple times.
    """
    from main import run_pipeline
    from Utils.ToolBox.llm_clients.session_router import SessionRouter
    
    # Create router once
    router = SessionRouter(
        run_mode="shared",
        shared_model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
        quantize=True,
        max_input_tokens=2048,
        device="auto",
        dtype="auto",
    )
    
    # Process multiple projects with same router
    projects = ["/content/Project1", "/content/Project2"]
    
    for project_path in projects:
        result = run_pipeline(
            repo_root=project_path,
            artifacts_dir="/content/Artifacts",
            router=router,  # Reuse pre-loaded model
            docstring_mode="modules_only",
            generate_readme=True,
            debug=True,
        )
        print(f"Processed {project_path}: {result['outputs']}")
    
    # Cleanup when done
    router.cleanup()


# Example 4: Per-role LLM parameters
def example_custom_params():
    """
    Customize generation parameters for each role.
    """
    from main import run_pipeline
    
    result = run_pipeline(
        repo_root="/content/MyProject",
        artifacts_dir="/content/Artifacts",
        model_id="Qwen/Qwen2.5-Coder-3B-Instruct",
        
        # Custom parameters per role
        llm_params_by_role={
            "writer": {
                "temperature": 0.2,
                "top_p": 0.95,
                "max_new_tokens": 220,
            },
            "critic": {
                "temperature": 0.1,
                "top_p": 0.9,
                "max_new_tokens": 150,
            },
            "readme": {
                "temperature": 0.3,
                "top_p": 0.95,
                "max_new_tokens": 300,
            },
        },
        
        docstring_mode="modules_only",
        quantize=True,
        max_input_tokens=2048,
        
        # Generate README with LLM
        generate_readme=True,
        readme_use_llm=True,
        
        debug=True,
    )
    print(result)


# Example 5: Minimal mode (no LLM, artifacts only)
def example_no_llm():
    """
    Skip LLM calls entirely, just organize artifacts.
    Fastest option, but no docstrings generated.
    """
    from main import run_pipeline
    
    result = run_pipeline(
        repo_root="/content/MyProject",
        artifacts_dir="/content/Artifacts",
        
        # No LLM mode
        docstring_mode="none",
        
        # README without LLM
        generate_readme=True,
        readme_use_llm=False,
        
        debug=True,
    )
    print(result)


# Example 6: Non-quantized for larger GPUs (A100, etc.)
def example_non_quantized():
    """
    Use full precision on larger GPUs where memory isn't a constraint.
    """
    from main import run_pipeline
    
    result = run_pipeline(
        repo_root="/content/MyProject",
        artifacts_dir="/content/Artifacts",
        model_id="Qwen/Qwen2.5-Coder-7B-Instruct",  # Larger model
        
        # Disable quantization
        quantize=False,
        dtype="float16",
        max_input_tokens=4096,  # Longer context
        
        # Full documentation
        docstring_mode="symbols_and_modules",
        
        generate_readme=True,
        readme_use_llm=True,
        debug=True,
    )
    print(result)


if __name__ == "__main__":
    print("Multi-Agent Hierarchical Documentation - Usage Examples")
    print("=" * 60)
    print("\nRun individual examples by calling:")
    print("  example_basic()           # Recommended for Colab T4")
    print("  example_per_agent()       # Different models per role")
    print("  example_reuse_router()    # Process multiple projects")
    print("  example_custom_params()   # Custom LLM parameters")
    print("  example_no_llm()          # Artifacts only, no LLM")
    print("  example_non_quantized()   # For larger GPUs")
    print("\nNote: Requires input artifacts (ast.json, deps.json, etc.)")
    print("      in Artifacts/<project_key>/ directory")
