'''
Git workflow helper for ns_lingo_nlp.

Usage:
  python workflow.py start    # before working (pull + ensure master)
  python workflow.py finish   # after working (commit, pull, push, optional merge)
'''

import subprocess
import sys


def run(cmd, capture=False):
    result = subprocess.run(cmd, shell=True, capture_output=capture, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        return None
    return result.stdout.strip() if capture else result.returncode


def is_clean():
    status = run("git status --porcelain", capture=True)
    return status is not None and status == ""


def cmd_start():
    print("=== Workflow: Start ===\n")

    branch = run("git branch --show-current", capture=True)
    print(f"Current branch: {branch}")

    if branch != "master":
        ans = input(f"On branch '{branch}'. Switch to master? (y/n): ").strip().lower()
        if ans == "y":
            if not is_clean():
                print("Uncommitted changes. Stash them first or commit before switching.")
                return
            run("git checkout master")
            branch = "master"

    print("Pulling latest changes...")
    run("git pull")

    run("git status")
    print("\nReady to work.")


def cmd_finish():
    print("=== Workflow: Finish ===\n")

    run("git status")

    if is_clean():
        nothing = input("\nNothing to commit. Push anyways? (y/n): ").strip().lower()
        if nothing != "y":
            print("Aborting.")
            return
    else:
        run('git add -A')
        msg = input("\nCommit message: ").strip()
        if not msg:
            print("No commit message provided. Aborting.")
            return
        result = run(f'git commit -m "{msg}"')
        if result is None:
            print("Commit failed. Aborting.")
            return

    print("\nPulling latest changes...")
    run("git pull --rebase")

    run("git push")

    branch = run("git branch --show-current", capture=True)
    if branch != "master":
        ans = input(f"\nOn branch '{branch}'. Merge into master? (y/n): ").strip().lower()
        if ans == "y":
            run("git checkout master")
            run("git pull")
            run(f"git merge {branch}")
            run("git push")
            run(f"git branch -d {branch}")
            print(f"Merged and deleted branch '{branch}'.")

    print("\nDone.")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("start", "finish"):
        print(__doc__.strip())
        return

    if sys.argv[1] == "start":
        cmd_start()
    else:
        cmd_finish()


if __name__ == "__main__":
    main()
