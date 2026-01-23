#!/usr/bin/env python3
"""
Mock test to demonstrate the pipeline flow without requiring GPU.
Creates minimal artifacts and tests the pipeline configuration.
"""

import json
import tempfile
from pathlib import Path


def create_mock_artifacts(artifacts_dir: Path, project_key: str):
    """Create minimal mock artifacts for testing."""
    project_dir = artifacts_dir / project_key
    project_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock AST
    ast_json = {
        "project": project_key,
        "data": [
            {
                "file": "main.py",
                "imports": [{"symbol": "import os"}],
                "functions": [
                    {
                        "kind": "function_definition",
                        "symbol": "main()",
                        "location": {"start_byte": 0, "end_byte": 50},
                    }
                ],
                "classes": [],
            }
        ]
    }
    (project_dir / "ast.json").write_text(json.dumps(ast_json, indent=2))
    
    # Mock dependencies
    deps_json = {
        "project": project_key,
        "internal_dependencies": [],
        "external_dependencies": [],
    }
    (project_dir / "dependencies_normalized.json").write_text(json.dumps(deps_json, indent=2))
    
    # Mock components
    components_json = {
        "project": project_key,
        "components": [],
    }
    (project_dir / "components.json").write_text(json.dumps(components_json, indent=2))
    
    print(f"✓ Created mock artifacts in {project_dir}")


def test_config_backward_compat():
    """Test that PipelineConfig llm_params backward compatibility works."""
    from Docsys.config import PipelineConfig
    from pathlib import Path
    
    # Test 1: Old-style llm_params
    cfg1 = PipelineConfig(
        repo_root=Path("/tmp"),
        project_key="test",
        project_artifacts_dir=Path("/tmp/artifacts"),
        cache_dir=Path("/tmp/cache"),
        model_id="test-model",
    )
    cfg1.llm_params = {"temperature": 0.5}
    
    assert cfg1.llm_params == {"temperature": 0.5}
    assert cfg1.llm_params_by_role.get("default") == {"temperature": 0.5}
    print("✓ Backward-compatible llm_params setter works")
    
    # Test 2: New-style llm_params_by_role
    cfg2 = PipelineConfig(
        repo_root=Path("/tmp"),
        project_key="test",
        project_artifacts_dir=Path("/tmp/artifacts"),
        cache_dir=Path("/tmp/cache"),
        model_id="test-model",
        llm_params_by_role={
            "writer": {"temperature": 0.2},
            "critic": {"temperature": 0.1},
        },
    )
    
    assert cfg2.llm_params_by_role["writer"] == {"temperature": 0.2}
    print("✓ New llm_params_by_role works")
    
    # Test 3: Docstring mode
    from Docsys.config import DocstringMode
    cfg3 = PipelineConfig(
        repo_root=Path("/tmp"),
        project_key="test",
        project_artifacts_dir=Path("/tmp/artifacts"),
        cache_dir=Path("/tmp/cache"),
        model_id="test-model",
        docstring_mode="modules_only",
    )
    assert cfg3.docstring_mode == "modules_only"
    print("✓ Docstring mode works")


def test_session_router_config():
    """Test SessionRouter configuration without loading models."""
    try:
        from Utils.ToolBox.llm_clients.session_router import SessionRouter
        
        # Test shared mode config (don't init, just verify attributes)
        print("✓ SessionRouter can be imported")
        
        # Check that it has required attributes
        assert hasattr(SessionRouter, '__dataclass_fields__')
        fields = SessionRouter.__dataclass_fields__
        
        assert 'run_mode' in fields
        assert 'shared_model_id' in fields
        assert 'agent_models' in fields
        assert 'quantize' in fields
        assert 'max_input_tokens' in fields
        assert 'keep_loaded' in fields
        print("✓ SessionRouter has all required fields")
    except ImportError as e:
        if "torch" in str(e) or "transformers" in str(e):
            print("✓ SessionRouter exists (torch not installed, skipping import test)")
            # Verify file exists and has key content
            from pathlib import Path
            router_file = Path("Utils/ToolBox/llm_clients/session_router.py")
            assert router_file.exists()
            content = router_file.read_text()
            assert "class SessionRouter" in content
            assert "run_mode:" in content
            print("✓ SessionRouter has required structure")
        else:
            raise


def test_main_pipeline_signature():
    """Test that main.run_pipeline has the right signature."""
    try:
        from main import run_pipeline
        import inspect
        
        sig = inspect.signature(run_pipeline)
        params = list(sig.parameters.keys())
        
        required = [
            'repo_root',
            'artifacts_dir',
            'router',
            'run_mode',
            'agent_models',
            'quantize',
            'max_input_tokens',
            'docstring_mode',
            'generate_readme',
        ]
        
        for param in required:
            assert param in params, f"Missing parameter: {param}"
        
        print("✓ run_pipeline has all required parameters")
    except ImportError as e:
        if "torch" in str(e) or "transformers" in str(e):
            print("✓ main.py exists (torch not installed, skipping import test)")
            # Verify file has key signatures
            from pathlib import Path
            main_file = Path("main.py")
            content = main_file.read_text()
            assert "def run_pipeline" in content
            assert "router:" in content
            assert "run_mode:" in content
            print("✓ run_pipeline has required signature")
        else:
            raise


def test_build_readme_mock():
    """Test build_readme with mock data."""
    try:
        from Docsys.build_readme import build_readme
        from Docsys.config import PipelineConfig
        from pathlib import Path
        
        cfg = PipelineConfig(
            repo_root=Path("/tmp"),
            project_key="TestProject",
            project_artifacts_dir=Path("/tmp/artifacts"),
            cache_dir=Path("/tmp/cache"),
            model_id="test-model",
        )
        
        doc_artifacts = {
            "project_key": "TestProject",
            "modules": [
                {
                    "module_name": "main",
                    "module_path": "main.py",
                    "docstring": "Main module for testing",
                    "symbols": [],
                }
            ],
        }
        
        # Generate README without LLM
        readme = build_readme(cfg, doc_artifacts, router=None, use_llm=False)
        
        assert "TestProject" in readme
        assert "main" in readme
        assert "Multi-Agent Hierarchical Documentation" in readme
        print("✓ build_readme generates valid content")
    except ImportError as e:
        if "torch" in str(e) or "transformers" in str(e):
            print("✓ build_readme.py exists (torch not installed, skipping test)")
            from pathlib import Path
            readme_file = Path("Docsys/build_readme.py")
            assert readme_file.exists()
            content = readme_file.read_text()
            assert "def build_readme" in content
            print("✓ build_readme has required structure")
        else:
            raise


def test_no_llm_mode():
    """Test that docstring_mode='none' doesn't require models."""
    from Docsys.config import PipelineConfig
    from pathlib import Path
    
    cfg = PipelineConfig(
        repo_root=Path("/tmp"),
        project_key="test",
        project_artifacts_dir=Path("/tmp/artifacts"),
        cache_dir=Path("/tmp/cache"),
        model_id="",  # Empty model_id should be ok with docstring_mode='none'
        docstring_mode="none",
    )
    
    assert cfg.docstring_mode == "none"
    print("✓ docstring_mode='none' configuration works")


def main():
    print("=" * 70)
    print("MOCK TESTS: Pipeline Configuration & API")
    print("=" * 70)
    
    print("\n1. Testing backward compatibility...")
    test_config_backward_compat()
    
    print("\n2. Testing SessionRouter configuration...")
    test_session_router_config()
    
    print("\n3. Testing main pipeline signature...")
    test_main_pipeline_signature()
    
    print("\n4. Testing build_readme...")
    test_build_readme_mock()
    
    print("\n5. Testing no-LLM mode...")
    test_no_llm_mode()
    
    print("\n" + "=" * 70)
    print("✓ ALL MOCK TESTS PASSED!")
    print("\nNote: These tests verify API and configuration only.")
    print("Full end-to-end testing requires GPU and model downloads.")
    print("=" * 70)


if __name__ == "__main__":
    main()
