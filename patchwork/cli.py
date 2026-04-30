import sys
import os
import click
from rich.console import Console
from rich.syntax import Syntax
import git
from .engine import snapshot, diff_snapshots, line_diff, read_file_at_ref
from .tui import PatchworkApp

console = Console()
# Patchwork: A professional semantic code diff tool.

EXTENSION_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.ts': 'javascript',
    '.tsx': 'javascript'
}

def detect_language(file_path, language_override=None):
    if language_override:
        return language_override
    
    _, ext = os.path.splitext(file_path)
    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]
    
    # Silently skip if it's not a supported language during bulk operations
    return None

def find_repo():
    try:
        return git.Repo(os.getcwd(), search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        console.print("[bold red]Error:[/bold red] Not a git repository.")
        sys.exit(1)

@click.group()
def cli():
    """Patchwork: A semantic code diff tool."""
    pass

@cli.command()
@click.argument('args', nargs=-1)
@click.option('--language', default=None, help='Override language detection')
@click.option('--tui', is_flag=True, help='Launch side-by-side TUI')
def diff(args, language, tui):
    """Compare two source files or Git refs at the function level."""
    
    old_snap, new_snap = {}, {}
    lang = None
    target_file = ""

    if len(args) == 2:
        arg1, arg2 = args
        
        # Case A: Two local files
        if os.path.exists(arg1) and os.path.exists(arg2):
            lang = detect_language(arg2, language)
            old_snap = snapshot(file_path=arg1, language=lang)
            new_snap = snapshot(file_path=arg2, language=lang)
            target_file = arg2
        
        # Case B: One Ref and One local file (Smart Diff)
        else:
            repo = find_repo()
            ref, file_path = arg1, arg2
            if not os.path.exists(file_path):
                console.print(f"[bold red]Error:[/bold red] File not found: {file_path}")
                sys.exit(1)
            
            lang = detect_language(file_path, language)
            repo_root = repo.working_tree_dir
            rel_path = os.path.relpath(os.path.abspath(file_path), repo_root)
            
            try:
                old_source = read_file_at_ref(repo_root, ref, rel_path)
                with open(file_path, "r", encoding="utf-8") as f:
                    new_source = f.read()
                
                old_snap = snapshot(source=old_source, language=lang)
                new_snap = snapshot(source=new_source, language=lang)
                target_file = file_path
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")
                sys.exit(1)

    elif len(args) == 3:
        # Case C: Two Refs and one file
        ref1, ref2, file_path = args
        repo = find_repo()
        repo_root = repo.working_tree_dir
        lang = detect_language(file_path, language)
        rel_path = os.path.relpath(os.path.abspath(file_path), repo_root)

        try:
            old_source = read_file_at_ref(repo_root, ref1, rel_path)
            new_source = read_file_at_ref(repo_root, ref2, rel_path)
            old_snap = snapshot(source=old_source, language=lang)
            new_snap = snapshot(source=new_source, language=lang)
            target_file = file_path
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)
    else:
        console.print("[bold red]Error:[/bold red] Usage: patchwork diff [REF1] [REF2] [FILE] or patchwork diff [FILE1] [FILE2]")
        sys.exit(1)

    if tui:
        results = diff_snapshots(old_snap, new_snap)
        app = PatchworkApp(results, old_snap, new_snap, target_file, lang)
        app.run()
    else:
        run_diff_output(old_snap, new_snap)

@cli.command()
@click.argument('ref')
@click.option('--language', default=None, help='Override language detection')
@click.option('--tui', is_flag=True, help='Launch TUI for the first changed file')
def show(ref, language, tui):
    """Show all semantic changes between REF and HEAD."""
    repo = find_repo()
    repo_root = repo.working_tree_dir
    
    try:
        commit_ref = repo.commit(ref)
        head_commit = repo.head.commit
        diffs = commit_ref.diff(head_commit)
        
        found_first_tui = False
        
        for d in diffs:
            file_path = d.b_path if d.b_path else d.a_path
            lang = detect_language(file_path, language)
            
            if lang:
                try:
                    old_source = read_file_at_ref(repo_root, ref, d.a_path) if d.a_path else ""
                    new_source = read_file_at_ref(repo_root, 'HEAD', d.b_path) if d.b_path else ""
                    
                    old_snap = snapshot(source=old_source, language=lang) if old_source else {}
                    new_snap = snapshot(source=new_source, language=lang) if new_source else {}
                    
                    if tui and not found_first_tui:
                        results = diff_snapshots(old_snap, new_snap)
                        if results["added"] or results["deleted"] or results["modified"]:
                            app = PatchworkApp(results, old_snap, new_snap, file_path, lang)
                            app.run()
                            found_first_tui = True
                            continue

                    if not tui:
                        console.print(f"\n[bold blue]FILE: {file_path}[/bold blue]")
                        run_diff_output(old_snap, new_snap)
                except Exception as e:
                    if not tui:
                        console.print(f"[yellow]Skipping {file_path}: {str(e)}[/yellow]")
                    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

def run_diff_output(old_snap, new_snap):
    if old_snap == new_snap:
        console.print("No semantic changes detected.")
        return

    results = diff_snapshots(old_snap, new_snap)

    if results["added"]:
        console.print("[bold green]ADDED FUNCTIONS:[/bold green]")
        for name in results["added"]:
            console.print(f"  [green]+ {name}[/green]")
        console.print()

    if results["deleted"]:
        console.print("[bold red]DELETED FUNCTIONS:[/bold red]")
        for name in results["deleted"]:
            console.print(f"  [red]- {name}[/red]")
        console.print()

    if results["modified"]:
        console.print("[bold yellow]MODIFIED FUNCTIONS:[/bold yellow]")
        for name in results["modified"]:
            console.print(f"\n[yellow]Modified: {name}[/yellow]")
            diff_text = line_diff(old_snap[name], new_snap[name], name)
            syntax = Syntax(diff_text, "diff", theme="monokai", background_color="default")
            console.print(syntax)

if __name__ == "__main__":
    cli()
