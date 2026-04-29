from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Static, Label, Input
from textual.containers import Horizontal, Vertical, Container
from textual.reactive import reactive
from textual.binding import Binding
from rich.syntax import Syntax
from rich.text import Text
import difflib

class FunctionItem(ListItem):
    """A list item representing a changed function with a badge."""
    def __init__(self, name: str, change_type: str):
        super().__init__()
        self.func_name = name
        self.change_type = change_type

    def compose(self) -> ComposeResult:
        badge_map = {
            "added": "[bold green][added][/]",
            "deleted": "[bold red][deleted][/]",
            "modified": "[bold yellow][modified][/]"
        }
        yield Label(f"{badge_map.get(self.change_type, '')} {self.func_name}")

class DiffPane(Static):
    """A widget to display code with line-level highlighting."""
    code = reactive("")
    language = reactive("python")
    highlight_lines = reactive(set())
    theme = reactive("monokai")
    title = reactive("")

    def render(self):
        if not self.code:
            return Text(self.title, style="italic")
        
        return Syntax(
            self.code,
            self.language,
            theme=self.theme,
            line_numbers=True,
            highlight_lines=self.highlight_lines,
            background_color="default"
        )

class PatchworkApp(App):
    CSS_PATH = "patchwork.tcss"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "toggle_dark", "Toggle Dark Mode", show=True),
        Binding("slash", "focus_filter", "Filter", show=True),
    ]

    selected_func = reactive("")
    filter_query = reactive("")

    def __init__(self, diff_results, old_snap, new_snap, filename, language):
        super().__init__()
        self.diff_results = diff_results
        self.old_snap = old_snap
        self.new_snap = new_snap
        self.filename = filename
        self.language = language
        
        # Flatten all changes into a name -> type mapping
        self.all_changes = {}
        for name in diff_results["added"]: self.all_changes[name] = "added"
        for name in diff_results["deleted"]: self.all_changes[name] = "deleted"
        for name in diff_results["modified"]: self.all_changes[name] = "modified"
        
        self.func_names = sorted(self.all_changes.keys())

    def on_mount(self):
        self.title = f"Patchwork: {self.filename}"
        if self.func_names:
            self.selected_func = self.func_names[0]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label(" FUNCTIONS", id="sidebar-title")
                yield Input(placeholder="Filter ( / )...", id="filter-input")
                yield ListView(id="function-list")
            with Vertical(id="main-view"):
                with Horizontal(id="summary-bar"):
                    yield Label(f" {self.filename}", id="filename-label")
                    yield Label(self.get_summary_text(), id="summary-label")
                with Horizontal(id="diff-panes"):
                    with Vertical(classes="pane-container"):
                        yield Label("OLD", classes="pane-header")
                        yield DiffPane(id="old-pane", classes="pane")
                    with Vertical(classes="pane-container"):
                        yield Label("NEW", classes="pane-header")
                        yield DiffPane(id="new-pane", classes="pane")
        yield Footer()

    def get_summary_text(self):
        r = self.diff_results
        return f"{len(r['modified'])} modified · {len(r['added'])} added · {len(r['deleted'])} deleted "

    def watch_filter_query(self, query: str):
        self.update_function_list()

    def watch_selected_func(self, func_name: str):
        if not func_name: return
        
        old_source = self.old_snap.get(func_name, "")
        new_source = self.new_snap.get(func_name, "")
        
        old_pane = self.query_one("#old-pane")
        new_pane = self.query_one("#new-pane")
        
        old_pane.language = self.language
        new_pane.language = self.language

        if self.all_changes[func_name] == "added":
            old_pane.code = ""
            old_pane.title = "This function did not exist in the old version."
            new_pane.code = new_source
            new_pane.highlight_lines = set(range(1, len(new_source.splitlines()) + 1))
        elif self.all_changes[func_name] == "deleted":
            old_pane.code = old_source
            old_pane.highlight_lines = set(range(1, len(old_source.splitlines()) + 1))
            new_pane.code = ""
            new_pane.title = "This function was removed in the new version."
        else:
            # Modified: Calculate line diff
            d = difflib.Differ()
            diff = list(d.compare(old_source.splitlines(), new_source.splitlines()))
            
            old_lines = []
            new_lines = []
            old_highlights = set()
            new_highlights = set()
            
            o_idx, n_idx = 1, 1
            for line in diff:
                if line.startswith(' '):
                    old_lines.append(line[2:])
                    new_lines.append(line[2:])
                    o_idx += 1
                    n_idx += 1
                elif line.startswith('-'):
                    old_lines.append(line[2:])
                    old_highlights.add(o_idx)
                    o_idx += 1
                elif line.startswith('+'):
                    new_lines.append(line[2:])
                    new_highlights.add(n_idx)
                    n_idx += 1
            
            old_pane.code = "\n".join(old_lines)
            old_pane.highlight_lines = old_highlights
            new_pane.code = "\n".join(new_lines)
            new_pane.highlight_lines = new_highlights

    def update_function_list(self):
        try:
            list_view = self.query_one("#function-list", ListView)
            list_view.clear()
            for name in self.func_names:
                if self.filter_query.lower() in name.lower():
                    list_view.append(FunctionItem(name, self.all_changes[name]))
        except:
            pass

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "filter-input":
            self.filter_query = event.value

    def on_list_view_selected(self, event: ListView.Selected):
        if event.item:
            self.selected_func = event.item.func_name

    def action_focus_filter(self):
        self.query_one("#filter-input").focus()

    def action_toggle_dark(self):
        self.dark = not self.dark
