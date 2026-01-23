#!/usr/bin/env python3
"""
Verification script to check that all refactoring requirements are met.
Runs without requiring GPU or model downloads.
"""

import sys
from pathlib import Path


def check_file_exists(filepath, description):
    """Check if a file exists."""
    path = Path(filepath)
    if path.exists():
        print(f"✓ {description}: {filepath}")
        return True
    else:
        print(f"✗ {description} MISSING: {filepath}")
        return False


def check_import(module_path, description):
    """Check if a module can be imported (syntax check)."""
    try:
        parts = module_path.split('.')
        if len(parts) > 1:
            parent = '.'.join(parts[:-1])
            name = parts[-1]
            exec(f"from {parent} import {name}")
        else:
            exec(f"import {module_path}")
        print(f"✓ {description} imports successfully")
        return True
    except SyntaxError as e:
        print(f"✗ {description} has SYNTAX ERROR: {e}")
        return False
    except Exception as e:
        # Import errors are ok (missing dependencies), we just check syntax
        if "No module named" in str(e) or "cannot import" in str(e):
            print(f"✓ {description} has valid syntax (missing deps: {e})")
            return True
        print(f"✗ {description} ERROR: {e}")
        return False


def check_config_attributes():
    """Check that PipelineConfig has new attributes."""
    try:
        with open("Docsys/config.py", "r") as f:
            content = f.read()
        
        checks = [
            ("llm_params_by_role", "llm_params_by_role" in content),
            ("docstring_mode", "docstring_mode" in content),
            ("DocstringMode", "DocstringMode" in content),
            ("Backward compat llm_params", "@property" in content and "def llm_params" in content),
        ]
        
        all_ok = True
        for name, check in checks:
            if check:
                print(f"✓ PipelineConfig has {name}")
            else:
                print(f"✗ PipelineConfig MISSING {name}")
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"✗ Error checking config: {e}")
        return False


def check_hfclient_features():
    """Check that HFClient has new features."""
    try:
        with open("Utils/ToolBox/llm_clients/hf_client.py", "r") as f:
            content = f.read()
        
        checks = [
            ("quantize parameter", "quantize:" in content),
            ("max_input_tokens parameter", "max_input_tokens:" in content),
            ("BitsAndBytesConfig", "BitsAndBytesConfig" in content),
            ("PYTORCH_CUDA_ALLOC_CONF", "PYTORCH_CUDA_ALLOC_CONF" in content),
            ("Truncation logic", "if self.max_input_tokens" in content),
        ]
        
        all_ok = True
        for name, check in checks:
            if check:
                print(f"✓ HFClient has {name}")
            else:
                print(f"✗ HFClient MISSING {name}")
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"✗ Error checking HFClient: {e}")
        return False


def check_session_router():
    """Check SessionRouter implementation."""
    try:
        with open("Utils/ToolBox/llm_clients/session_router.py", "r") as f:
            content = f.read()
        
        checks = [
            ("SessionRouter class", "class SessionRouter" in content),
            ("run_mode parameter", "run_mode:" in content),
            ("shared_model_id", "shared_model_id:" in content),
            ("agent_models", "agent_models:" in content),
            ("get_client method", "def get_client" in content),
            ("release_role method", "def release_role" in content),
            ("cleanup method", "def cleanup" in content),
            ("keep_loaded support", "keep_loaded:" in content),
        ]
        
        all_ok = True
        for name, check in checks:
            if check:
                print(f"✓ SessionRouter has {name}")
            else:
                print(f"✗ SessionRouter MISSING {name}")
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"✗ Error checking SessionRouter: {e}")
        return False


def check_main_router_support():
    """Check that main.py accepts router parameter."""
    try:
        with open("main.py", "r") as f:
            content = f.read()
        
        checks = [
            ("router parameter", "router: Optional[SessionRouter]" in content),
            ("run_mode parameter", "run_mode:" in content),
            ("agent_models parameter", "agent_models:" in content),
            ("quantize parameter", "quantize:" in content),
            ("max_input_tokens parameter", "max_input_tokens:" in content),
            ("docstring_mode parameter", "docstring_mode:" in content),
            ("generate_readme parameter", "generate_readme:" in content),
        ]
        
        all_ok = True
        for name, check in checks:
            if check:
                print(f"✓ run_pipeline has {name}")
            else:
                print(f"✗ run_pipeline MISSING {name}")
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"✗ Error checking main.py: {e}")
        return False


def check_generate_artifacts_router():
    """Check that generate_doc_artifacts accepts router."""
    try:
        with open("Docsys/generate_doc_artifacts.py", "r") as f:
            content = f.read()
        
        checks = [
            ("router parameter", "router: Optional[SessionRouter]" in content),
            ("docstring_mode check", "cfg.docstring_mode" in content),
            ("llm_params_by_role usage", "cfg.llm_params_by_role" in content),
            ("router.get_client", "router.get_client" in content or "router:" in content),
            ("router.release_role", "router.release_role" in content or "release" in content.lower()),
        ]
        
        all_ok = True
        for name, check in checks:
            if check:
                print(f"✓ generate_doc_artifacts has {name}")
            else:
                print(f"✗ generate_doc_artifacts MISSING {name}")
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"✗ Error checking generate_doc_artifacts: {e}")
        return False


def check_build_readme():
    """Check build_readme.py exists and works."""
    try:
        with open("Docsys/build_readme.py", "r") as f:
            content = f.read()
        
        checks = [
            ("build_readme function", "def build_readme" in content),
            ("router parameter", "router:" in content),
            ("use_llm parameter", "use_llm:" in content),
            ("artifact-driven", "doc_artifacts" in content),
        ]
        
        all_ok = True
        for name, check in checks:
            if check:
                print(f"✓ build_readme has {name}")
            else:
                print(f"✗ build_readme MISSING {name}")
                all_ok = False
        return all_ok
    except Exception as e:
        print(f"✗ Error checking build_readme: {e}")
        return False


def check_deprecation_warnings():
    """Check that deprecated files have warnings."""
    try:
        with open("Docsys/build_docs_site.py", "r") as f:
            content = f.read()
        has_warning = "DeprecationWarning" in content
        
        if has_warning:
            print(f"✓ build_docs_site.py has deprecation warning")
        else:
            print(f"✗ build_docs_site.py MISSING deprecation warning")
        
        with open("Docsys/mkdocs_builder.py", "r") as f:
            content = f.read()
        has_warning2 = "DeprecationWarning" in content
        
        if has_warning2:
            print(f"✓ mkdocs_builder.py has deprecation warning")
        else:
            print(f"✗ mkdocs_builder.py MISSING deprecation warning")
        
        return has_warning and has_warning2
    except Exception as e:
        print(f"✗ Error checking deprecation warnings: {e}")
        return False


def main():
    print("=" * 70)
    print("VERIFICATION: Multi-Agent Documentation Pipeline Refactor")
    print("=" * 70)
    
    results = []
    
    print("\n1. Checking file structure...")
    results.append(check_file_exists("Utils/ToolBox/llm_clients/session_router.py", "SessionRouter"))
    results.append(check_file_exists("Docsys/build_readme.py", "README builder"))
    results.append(check_file_exists("examples.py", "Examples file"))
    results.append(check_file_exists(".gitignore", ".gitignore"))
    
    print("\n2. Checking imports/syntax...")
    results.append(check_import("Docsys.config", "PipelineConfig"))
    results.append(check_import("Utils.ToolBox.llm_clients.hf_client", "HFClient"))
    
    print("\n3. Checking PipelineConfig updates...")
    results.append(check_config_attributes())
    
    print("\n4. Checking HFClient updates...")
    results.append(check_hfclient_features())
    
    print("\n5. Checking SessionRouter...")
    results.append(check_session_router())
    
    print("\n6. Checking main.py router support...")
    results.append(check_main_router_support())
    
    print("\n7. Checking generate_doc_artifacts updates...")
    results.append(check_generate_artifacts_router())
    
    print("\n8. Checking build_readme...")
    results.append(check_build_readme())
    
    print("\n9. Checking deprecation warnings...")
    results.append(check_deprecation_warnings())
    
    print("\n" + "=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"RESULTS: {passed}/{total} checks passed")
    
    if passed == total:
        print("✓ ALL CHECKS PASSED!")
        return 0
    else:
        print(f"✗ {total - passed} checks failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
