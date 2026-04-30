from textual.app import App, ComposeResult
from textual.widgets import ListItem, Static, Label, Input, ListView
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.reactive import reactive
from textual.binding import Binding
from rich.syntax import Syntax
from rich.text import Text
from rich.table import Table
from rich.console import Console
from rich.segment import Segment
import difflib
from datetime import datetime

class HeaderIcon(Label):
    """A dedicated icon button that opens the command palette when clicked."""
    def on_click(self) -> None:
        self.app.action_command_palette()

class FunctionItem(ListItem):
    """A list item representing a changed function with a colored badge."""
    def __init__(self, name: str, change_type: str):
        super().__init__()
        self.func_name = name
        self.change_type = change_type

    def compose(self) -> ComposeResult:
        badge_map = {
            "added": "[bold green]+[/]",
            "deleted": "[bold red]-[/]",
            "modified": "[bold yellow]~[/]"
        }
        yield Label(f"{badge_map.get(self.change_type, '')} {self.func_name}")

class DiffPane(Static):
    """A widget to display code with high-contrast diff highlighting and syntax colors."""
    code = reactive("")
    language = reactive("python")
    highlight_lines = reactive({}) # Changed from set to dict for char ranges
    theme = reactive("monokai")
    title = reactive("")
    bg_style = reactive("")
    inline_bg_style = reactive("") # New: Style for exact changed words

    def render(self):
        if not self.code:
            return Text(self.title, style="italic")
        
        # Bug 1 Fix: Implement Syntax Highlighting while preserving background tints
        console = Console()
        syntax = Syntax(
            self.code, 
            self.language, 
            theme=self.theme, 
            background_color="default",
            word_wrap=False
        )
        
        # Render the syntax to segments so we can put them into our custom Table rows
        highlighted_lines = list(console.render_lines(syntax, pad=False))
        
        table = Table.grid(padding=(0, 1))
        table.add_column("num", style="#aaaaaa", justify="right", width=4)
        table.add_column("code")
        
        for i, line_segments in enumerate(highlighted_lines, 1):
            num_text = Text(str(i))
            
            # Reassemble the highlighted segments for this line
            line_text = Text.assemble(*[(s.text, s.style) for s in line_segments])
            
            row_style = None
            if i in self.highlight_lines:
                row_style = self.bg_style
                char_ranges = self.highlight_lines[i]
                for (start, end) in char_ranges:
                    line_text.stylize(self.inline_bg_style, start, end)
            
            table.add_row(num_text, line_text, style=row_style)
            
        return table

class PatchworkApp(App):
    CSS_PATH = "patchwork.tcss"
    
    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("d", "toggle_dark", "Mode", show=True),
        Binding("slash", "focus_filter", "Search", show=True),
        Binding("escape", "clear_filter", "Clear", show=False),
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
        
        self.all_changes = {}
        for name in diff_results["added"]: self.all_changes[name] = "added"
        for name in diff_results["deleted"]: self.all_changes[name] = "deleted"
        for name in diff_results["modified"]: self.all_changes[name] = "modified"
        self.func_names = sorted(self.all_changes.keys())

    def on_mount(self):
        if self.func_names:
            self.selected_func = self.func_names[0]
        self.set_interval(1.0, self.update_clock)

    def update_clock(self):
        # Bug 3 Fix: Robust query to prevent flicker/freeze
        try:
            clocks = self.query("#header-clock")
            if clocks:
                clocks.first().update(datetime.now().strftime("%H:%M:%S"))
        except Exception:
            pass

    def compose(self) -> ComposeResult:
        with Horizontal(id="header-bar"):
            yield HeaderIcon(" ◈ ", id="header-icon")
            yield Label("[bold #ffaf00]PATCHWORK[/]", id="branding")
            yield Label(self.filename, id="header-filename")
            yield Label("--:--:--", id="header-clock")

        with Horizontal():
            with Vertical(id="sidebar"):
                yield Label("FUNCTIONS", id="sidebar-label")
                yield Input(placeholder="Search functions...", id="filter-input")
                yield ListView(id="function-list")
            
            with Vertical(id="main-view"):
                with Horizontal(id="summary-bar"):
                    yield Label(self.get_summary_text(), id="summary-label")
                
                with Horizontal(id="diff-panes"):
                    with Vertical(classes="pane-container"):
                        yield Label("OLD", classes="pane-label")
                        with ScrollableContainer(classes="code-scroll"):
                            yield DiffPane(id="old-pane", classes="pane")
                    with Vertical(classes="pane-container"):
                        yield Label("NEW", classes="pane-label")
                        with ScrollableContainer(classes="code-scroll"):
                            yield DiffPane(id="new-pane", classes="pane")
        
        with Horizontal(id="footer-bar"):
            yield Label("Q [dim]Quit[/]   D [dim]Mode[/]   / [dim]Search[/]", id="footer-hints")
            yield Label("built by Vedant Prabhu", id="footer-credit")

    def get_summary_text(self):
        r = self.diff_results
        return f" {len(r['modified'])} modified · {len(r['added'])} added · {len(r['deleted'])} deleted"

    def watch_filter_query(self, query: str):
        self.update_function_list()

    def watch_selected_func(self, func_name: str):
        if not func_name: return
        
        old_source = self.old_snap.get(func_name, "")
        new_source = self.new_snap.get(func_name, "")
        
        old_pane = self.query_one("#old-pane", DiffPane)
        new_pane = self.query_one("#new-pane", DiffPane)
        
        old_pane.language = self.language
        new_pane.language = self.language
        
        # Maintain theme sync
        syntax_theme = "friendly" if self.theme == "textual-light" else "monokai"
        old_pane.theme = syntax_theme
        new_pane.theme = syntax_theme

        if self.all_changes[func_name] == "added":
            old_pane.code = ""
            old_pane.title = "Function did not exist."
            new_pane.code = new_source
            new_pane.bg_style = "on #062a06" if self.theme == "textual-dark" else "on #d4f7d4"
            new_pane.highlight_lines = {i: [] for i in range(1, len(new_source.splitlines()) + 1)}
        elif self.all_changes[func_name] == "deleted":
            old_pane.code = old_source
            old_pane.bg_style = "on #3b0b0b" if self.theme == "textual-dark" else "on #ffd7d7"
            old_pane.highlight_lines = {i: [] for i in range(1, len(old_source.splitlines()) + 1)}
            new_pane.code = ""
            new_pane.title = "Function was removed."
        else:
            d = difflib.Differ()
            diff = list(d.compare(old_source.splitlines(), new_source.splitlines()))
            
            import re
            old_lines, new_lines = [], []
            old_highlights, new_highlights = {}, {}
            o_idx, n_idx = 1, 1
            for i, line in enumerate(diff):
                if line.startswith(' '):
                    old_lines.append(line[2:])
                    new_lines.append(line[2:])
                    o_idx += 1
                    n_idx += 1
                elif line.startswith('-'):
                    old_lines.append(line[2:])
                    old_highlights[o_idx] = []
                    if i + 1 < len(diff) and diff[i+1].startswith('?'):
                        q_line = diff[i+1][2:]
                        for m in re.finditer(r'[-^]+', q_line):
                            old_highlights[o_idx].append((m.start(), m.end()))
                    else:
                        old_highlights[o_idx].append((0, len(line[2:])))
                    o_idx += 1
                elif line.startswith('+'):
                    new_lines.append(line[2:])
                    new_highlights[n_idx] = []
                    if i + 1 < len(diff) and diff[i+1].startswith('?'):
                        q_line = diff[i+1][2:]
                        for m in re.finditer(r'[+^]+', q_line):
                            new_highlights[n_idx].append((m.start(), m.end()))
                    else:
                        new_highlights[n_idx].append((0, len(line[2:])))
                    n_idx += 1
            
            old_pane.code = "\n".join(old_lines)
            old_pane.bg_style = "on #3b0b0b" if self.theme == "textual-dark" else "on #ffd7d7"
            old_pane.inline_bg_style = "on #8f1f1f" if self.theme == "textual-dark" else "on #ffaaaa"
            old_pane.highlight_lines = old_highlights
            
            new_pane.code = "\n".join(new_lines)
            new_pane.bg_style = "on #062a06" if self.theme == "textual-dark" else "on #d4f7d4"
            new_pane.inline_bg_style = "on #176b17" if self.theme == "textual-dark" else "on #88f088"
            new_pane.highlight_lines = new_highlights

    def update_function_list(self):
        # Bug 2 Fix: Auto-select first result during filtering
        try:
            list_view = self.query_one("#function-list", ListView)
            list_view.clear()
            matches = []
            for name in self.func_names:
                if self.filter_query.lower() in name.lower():
                    item = FunctionItem(name, self.all_changes[name])
                    list_view.append(item)
                    matches.append(name)
            
            if matches:
                list_view.index = 0
                self.selected_func = matches[0]
            else:
                self.selected_func = ""
        except Exception:
            pass

    def on_input_changed(self, event: Input.Changed):
        if event.input.id == "filter-input":
            self.filter_query = event.value

    def on_input_submitted(self, event: Input.Submitted):
        if event.input.id == "filter-input":
            self.query_one("#function-list").focus()

    def on_list_view_selected(self, event: ListView.Selected):
        if event.item:
            self.selected_func = event.item.func_name

    def action_focus_filter(self):
        self.query_one("#filter-input").focus()

    def action_clear_filter(self):
        """Action to clear the search filter (Escape key)."""
        search_input = self.query_one("#filter-input", Input)
        search_input.value = ""
        self.query_one("#function-list").focus()

    def action_toggle_dark(self):
        self.theme = "textual-light" if self.theme == "textual-dark" else "textual-dark"
        # Force re-render of current diff to update syntax theme
        self.watch_selected_func(self.selected_func)

if __name__ == "__main__":
    # This remains for local testing
    pass
