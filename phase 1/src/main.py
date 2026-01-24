from pipeline.orchestrator import run_pipeline

if __name__ == "__main__":
    print("Choose how you want to run the pipeline:")
    print("1. Run the pipeline on a GitHub repository")
    print("2. Run the pipeline on a local repository")
    choice = input("Enter 1 for GitHub repo or 2 for local repo: ").strip()

    if choice == "1":
        repo_url = input("Enter the GitHub repository URL: ").strip()
    elif choice == "2":
        repo_url = input("Enter the local repository path: ").strip()
    else:
        print("Invalid choice. Exiting.")
        exit(1)

    result = run_pipeline(repo_url)

    print("Pipeline finished successfully.")
    print("Repository:", result["repo"])
    print("Generated artifacts:")

    for name, path in result["artifacts"].items():
        print(f" - {name}: {path}")