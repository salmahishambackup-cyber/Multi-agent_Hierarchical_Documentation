from agents.structural_agent import StructuralAgent


def run_pipeline(repo_url: str):
    agent = StructuralAgent()
    return agent.run(repo_url)
