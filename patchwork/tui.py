from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Static, Label
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive
import difflib

class DiffView(Static):
    """A widget to display a colored diff."""
    def update_diff(self, old_source, new_source):
        lines = difflib.ndiff(old_source.splitlines(), new_source.splitlines())
        
        old_display = []
        new_display = []
        
        for line in lines:
            if line.startswith(' '):
                old_display.append(line[2:])
                new_display.append(line[2:])
            elif line.startswith('-'):
                old_display.append(f"[red]{line[2:]}[/red]")
                new_display.append("") # Placeholder to keep lines aligned
            elif line.startswith('+'):
                old_display.append("") # Placeholder
                new_display.append(f"[green]{line[2:]}[/green]")
        
        self.old_text = "\n".join(old_display)
        self.new_text = "\n".join(new_display)
        self.refresh()

class PatchworkApp(App):
    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 30;
        background: $panel;
        border-right: tall $primary;
    }
    #diff-container {
        width: 1fr;
    }
    .pane {
        width: 1fr;
        height: 1fr;
        border: solid $accent;
        padding: 1;
        overflow-y: scroll;
    }
    """
    
    def __init__(self, diff_results, old_snap, new_snap):
        super().__init__()
        self.diff_results = diff_results
        self.old_snap = old_snap
        self.new_snap = new_snap
        self.all_changed = sorted(list(set(diff_results['added'] + diff_results['deleted'] + diff_results['modified'])))

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="sidebar"):
            yield Label("Functions")
            yield ListView(*[ListItem(Static(name), id=name) for name in self.all_changed], id="function-list")
        with Horizontal(id="diff-container"):
            yield Static("", id="old-pane", classes="pane")
            yield Static("", id="new-pane", classes="pane")
        yield Footer()

    def on_list_view_selected(self, event: ListView.Selected):
        func_name = event.item.id
        old_source = self.old_snap.get(func_name, "")
        new_source = self.new_snap.get(func_name, "")
        
        # Simple diff rendering for Phase 5 TUI
        diff = difflib.ndiff(old_source.splitlines(), new_source.splitlines())
        
        old_lines = []
        new_lines = []
        
        for line in diff:
            if line.startswith(' '):
                old_lines.append(line[2:])
                new_lines.append(line[2:])
            elif line.startswith('-'):
                old_lines.append(f"[@click=none][red]{line[2:]}[/][/]")
                new_lines.append("")
            elif line.startswith('+'):
                old_lines.append("")
                new_lines.append(f"[@click=none][green]{line[2:]}[/][/]")
        
        self.query_one("#old-pane").update("\n".join(old_lines))
        self.query_one("#new-pane").update("\n".join(new_lines))
