import sys
import os
import click
from rich.console import Console
from rich.syntax import Syntax
import git
from .engine import snapshot, diff_snapshots, line_diff, read_file_at_ref
from .tui import PatchworkApp

console = Console()

EXTENSION_MAP = {
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'javascript'
}

def detect_language(file_path, language_override=None):
    if language_override:
        return language_override
    
    _, ext = os.path.splitext(file_path)
    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]
    
    console.print(f"[bold red]Error:[/bold red] Unsupported file type: {ext}")
    sys.exit(1)

def find_repo():
    try:
        return git.Repo(os.getcwd(), search_parent_directories=True)
    except git.InvalidGitRepositoryError:
        console.print("[bold red]Error:[/bold red] Not a git repository (or any of the parent directories).")
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
    
    if len(args) == 2:
        old_path, new_path = args
        lang = detect_language(new_path, language)
        
        for f in [old_path, new_path]:
            if not os.path.exists(f):
                console.print(f"[bold red]Error:[/bold red] File not found: {f}")
                sys.exit(1)
        
        try:
            old_snap = snapshot(file_path=old_path, language=lang)
            new_snap = snapshot(file_path=new_path, language=lang)
        except SyntaxError as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)

    elif len(args) == 3:
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
        except git.exc.GitCommandError as e:
            console.print(f"[bold red]Error:[/bold red] Git error: {str(e)}")
            sys.exit(1)
        except (KeyError, git.exc.BadName):
            console.print(f"[bold red]Error:[/bold red] File or Ref error for '{rel_path}'")
            sys.exit(1)
        except SyntaxError as e:
            console.print(f"[bold red]Error:[/bold red] {str(e)}")
            sys.exit(1)
    else:
        console.print("[bold red]Error:[/bold red] Usage: patchwork diff [OLD] [NEW] [FILE] or patchwork diff [FILE1] [FILE2]")
        sys.exit(1)

    if tui:
        results = diff_snapshots(old_snap, new_snap)
        app = PatchworkApp(results, old_snap, new_snap)
        app.run()
    else:
        run_diff_output(old_snap, new_snap)

@cli.command()
@click.argument('ref')
@click.option('--language', default=None, help='Override language detection')
def show(ref, language):
    """Show all semantic changes between REF and HEAD."""
    repo = find_repo()
    repo_root = repo.working_tree_dir
    
    try:
        commit_ref = repo.commit(ref)
        head_commit = repo.head.commit
        diffs = commit_ref.diff(head_commit)
        
        for d in diffs:
            file_path = d.b_path if d.b_path else d.a_path
            _, ext = os.path.splitext(file_path)
            
            if ext in EXTENSION_MAP:
                lang = detect_language(file_path, language)
                console.print(f"\n[bold blue]FILE: {file_path}[/bold blue]")
                
                try:
                    old_source = read_file_at_ref(repo_root, ref, d.a_path) if d.a_path else ""
                    new_source = read_file_at_ref(repo_root, 'HEAD', d.b_path) if d.b_path else ""
                    
                    old_snap = snapshot(source=old_source, language=lang) if old_source else {}
                    new_snap = snapshot(source=new_source, language=lang) if new_source else {}
                    
                    run_diff_output(old_snap, new_snap)
                except Exception as e:
                    console.print(f"[yellow]Skipping {file_path}: {str(e)}[/yellow]")
                    
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {str(e)}")
        sys.exit(1)

def run_diff_output(old_snap, new_snap):
    if old_snap == new_snap:
        console.print("No changes detected.")
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
