import subprocess
import getpass
import os

def run_git_commands():
    try:
        # 1. git add .
        print("Staging all changes...")
        add_result = subprocess.run(['git', 'add', '.'], capture_output=True, text=True, check=False)
        if add_result.returncode != 0:
            print(f"Error staging files: {add_result.stderr}")
            return
        print("Changes staged successfully.")

        # 2. git commit
        commit_message = input("Enter your commit message: ")
        print("Committing changes...")
        commit_result = subprocess.run(['git', 'commit', '-m', commit_message], capture_output=True, text=True, check=False)
        if commit_result.returncode != 0:
            print(f"Error committing changes: {commit_result.stderr}")
            return
        print("Changes committed successfully.")

        # 3. git push
        username = input("Enter your GitHub username: ")
        pat = getpass.getpass("Enter your GitHub Personal Access Token (PAT): ")

        # Get current remote URL
        remote_url_result = subprocess.run(['git', 'config', '--get', 'remote.origin.url'], capture_output=True, text=True, check=True)
        original_remote_url = remote_url_result.stdout.strip()

        # Extract owner and repo from the original URL
        # Handles both HTTPS (https://github.com/owner/repo.git) and SSH (git@github.com:owner/repo.git)
        if original_remote_url.startswith('https://'):
            parts = original_remote_url.split('/')
            owner = parts[-2]
            repo = parts[-1].replace('.git', '')
        elif original_remote_url.startswith('git@'):
            parts = original_remote_url.split(':', 1)
            if len(parts) > 1:
                repo_path = parts[1]
                repo_parts = repo_path.split('/')
                owner = repo_parts[0]
                repo = repo_parts[1].replace('.git', '')
            else:
                print("Could not parse SSH remote URL.")
                return
        else:
            print("Unsupported Git remote URL format. Please use HTTPS or SSH.")
            return

        # Construct the PAT-embedded URL for push
        pat_remote_url = f"https://{username}:{pat}@github.com/{owner}/{repo}.git"

        print("Pushing changes to remote repository...")
        push_result = subprocess.run(['git', 'push', pat_remote_url], capture_output=True, text=True, check=False)
        if push_result.returncode != 0:
            print(f"Error pushing changes: {push_result.stderr}")
            print("Please ensure your PAT has the necessary 'repo' scope and is correct.")
            return
        print("Changes pushed successfully.")

    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e.cmd}\nStdout: {e.stdout}\nStderr: {e.stderr}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    run_git_commands()
