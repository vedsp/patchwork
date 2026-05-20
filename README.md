# Patchwork: Semantic Diff Tool

`patchwork-semantic-diff` is an Abstract Syntax Tree (AST) code comparison utility powered by Tree-sitter that identifies and displays additions, deletions, and modifications at the function and method level.

---

## The Problem Solved

Traditional line-by-line comparison tools (such as `git diff`) flag changes based on physical text line modifications, introducing noise from cosmetic updates like re-indentation, comments, import reordering, or helper function reorganization. Patchwork solves this by converting source files into Abstract Syntax Trees (ASTs), isolating functions, and comparing their signatures and bodies directly. This isolates logical changes from stylistic differences, letting you review functional modifications immediately.

---

## Features

*   **AST-Based Function Identification**: Parses source code via Tree-sitter to extract functions for Python (`function_definition`) and JavaScript/TypeScript (standard `function_declaration`, arrow functions bound to `variable_declarator` nodes, and class `method_definition` routines).
*   **Flexible Diff Targets**: Supports comparing two local files, a local file against a Git commit/branch (`REF`), or comparing a file between two distinct Git commits/branches (`REF1` and `REF2`).
*   **Commit-Level Auditing**: Scans all changed files in a git repository between a target commit (`REF`) and `HEAD`, filtering for files in supported languages and executing automated semantic diffs.
*   **Interactive Side-by-Side TUI**: Provides a terminal application powered by Textual that displays changed functions in a sidebar and highlights unified and inline code differences side-by-side.
*   **Character-Level Inline Diff Highlighting**: Resolves line-level changes down to specific character and word edits, tinting modified text inside the TUI panels.
*   **Real-Time Fuzzy Function Search**: Supports keyboard-driven sidebar filtering inside the TUI via `/` search focusing, instant query matching, and automatic top-match selection.
*   **Dynamic Theme Toggling**: Toggles between Dark Mode (utilizing the Monokai syntax theme and custom dark green/red panel tints) and Light Mode (utilizing the Friendly syntax theme and light green/red tints) instantly using the `d` key.
*   **Built-in Live Session Clock**: Features a real-time status clock in the header bar of the terminal interface to track session durations.

---

## Tech Stack

*   **Runtime Environment**: Python `>=3.10`
*   **Abstract Syntax Tree (AST) Parsing**: `tree-sitter`, `tree-sitter-python`, `tree-sitter-javascript`
*   **CLI Framework**: `click`
*   **Console Rendering & Formatting**: `rich`
*   **Terminal User Interface (TUI)**: `textual`
*   **Version Control Integration**: `gitpython`
*   **Comparison Engine**: `difflib` (standard library unified diffing)

---

## Installation & Setup

To install the tool in your environment, use one of the following methods:

### 1. Install via pip
```bash
pip install patchwork-semantic-diff
```

### 2. Local Development Setup
Clone the repository and install the package in editable mode:
```bash
git clone https://github.com/your-username/patchwork.git
cd patchwork
pip install -e .
```

### 3. Run Test Suite
Run the test suite using `pytest`:
```bash
pip install pytest
pytest
```

---

## Usage with Real Examples

### A. Command Line Interface (CLI)

#### 1. Compare Two Local Files
Run a functional comparison between two files:
```bash
patchwork diff demo/api_client_v1.py demo/api_client_v2.py
```

**Expected CLI Output:**
```text
ADDED FUNCTIONS:
  + query_historical_data

DELETED FUNCTIONS:
  - legacy_authenticate

MODIFIED FUNCTIONS:

Modified: get_user_profile
--- old/get_user_profile
+++ new/get_user_profile
@@ -1,6 +1,19 @@
-def get_user_profile(self, user_id: str) -> Dict[str, Any]:
-        """Fetch user profile information from the API."""
+def get_user_profile(self, user_id: str, retries: int = 3) -> Dict[str, Any]:
+        """
+        Fetch user profile with exponential backoff retry logic.
+        MODIFIED: Added robust retry handling and logging.
+        """
         url = f"{self.base_url}/users/{user_id}"
-        response = self.session.get(url)
-        response.raise_for_status()
-        return response.json()+        
+        for attempt in range(retries):
+            try:
+                response = self.session.get(url, timeout=5)
+                response.raise_for_status()
+                return response.json()
+            except requests.RequestException as e:
+                self.logger.warning(f"Attempt {attempt + 1} failed: {e}")
+                if attempt == retries - 1:
+                    raise
+                time.sleep(2 ** attempt)
+        
+        return {}
```

#### 2. Compare Git Revision against a Local File
Compare a specific Git reference version of a file with a current local file:
```bash
patchwork diff HEAD~1 demo/api_client_v2.py
```

#### 3. Compare a File Between Two Git Revisions
Compare a file between two specific commits, branches, or tags:
```bash
patchwork diff main experimental demo/api_client_v2.py
```

#### 4. Audit an Entire Commit
List and view all semantic changes for files between a given reference (e.g. `main` or a commit hash) and `HEAD`:
```bash
patchwork show main
```

---

### B. Visual TUI Mode
Append `--tui` to any command to launch the side-by-side interactive TUI:
```bash
patchwork diff demo/api_client_v1.py demo/api_client_v2.py --tui
```

#### TUI User Flows & Keybindings:
*   **Sidebar Selection**: Use the mouse or up/down arrow keys to select a changed function from the list. The central panes update instantly.
*   **Search & Filter**: Press `/` to focus the "Search functions..." input field. As you type, the function list filters in real-time. Press **Enter** to submit, which focuses the filtered list and selects the first match. Press **Escape** to clear the query and return focus to the list.
*   **Theme Switcher**: Press `d` to toggle between dark mode (Monokai theme, deep green/red panel tints) and light mode (Friendly theme, light green/red panel tints).
*   **Exit**: Press `q` to quit the visual interface.

---

## Project Structure

```text
.
├── .github/          # Holds GitHub continuous integration (CI) workflows
├── demo/             # Sample source files demonstrating semantic diff scenarios
├── patchwork/        # Primary Python source package for CLI, TUI, and engine
├── tests/            # Automated test suite using pytest
└── pyproject.toml    # Project metadata, requirements, and build configuration
```

*   **`.github`**: Contains GitHub actions workflows configuration files.
*   **`demo`**: Contains demo files representing mock client implementations.
*   **`patchwork`**: Houses package modules, the main CLI script, the parsing engine, and visual stylesheets.
    *   `patchwork/cli.py` - Orchestrates the Click commands (`diff` and `show`), manages Git reference resolving, and formats terminal prints.
    *   `patchwork/engine.py` - Core parsing engine implementing Tree-sitter loaders and language-specific AST walkers (Python, JavaScript/TypeScript).
    *   `patchwork/tui.py` - Implements the double-pane side-by-side terminal UI layout, reactive states, and keybinds using the Textual library.
    *   `patchwork/patchwork.tcss` - Textual stylesheet governing component heights, layout grids, borders, scrolling behavior, and active themes.
*   **`tests`**: Holds testing scripts that assert function analysis correctness, diff outputs, and CLI error handling.

---

## License

This project is licensed under the terms of the MIT License.
