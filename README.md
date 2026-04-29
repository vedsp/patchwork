# Patchwork

A semantic code diff tool that understands functions, not just lines.

![Build Status](https://github.com/your-username/patchwork/actions/workflows/ci.yml/badge.svg)

### [Demo placeholder]
> **Recording your own demo:**
> 1. Install `asciinema` and `agg`
> 2. Run `asciinema rec demo.cast`
> 3. Perform a few diffs (e.g., `patchwork diff old.py new.py`)
> 4. Convert to GIF: `agg demo.cast demo.gif`

---

## Installation

```bash
pip install patchwork-diff
```

## Usage

### 1. Compare local files
```bash
patchwork diff old.py new.py
```

### 2. Compare Git commits
```bash
patchwork diff HEAD~1 HEAD path/to/file.js
```

### 3. Audit an entire commit
```bash
patchwork show HEAD~1
```

### 4. Visual TUI mode
```bash
patchwork diff old.py new.py --tui
```

---

## How it Works

Patchwork uses **Tree-sitter** to parse your source code into an Abstract Syntax Tree (AST). Instead of looking at raw text changes, it traverses the tree to identify specific function declarations, arrow functions, and class methods. 

By mapping code changes to these semantic blocks, Patchwork can tell you precisely which functions were added, deleted, or modified. This eliminates the "noise" of line-level diffs—like changes to comments, whitespace, or reordering—and lets you focus on the logic that actually changed.

## Supported Languages

| Language | Extensions |
| :--- | :--- |
| **Python** | `.py` |
| **JavaScript** | `.js` |
| **TypeScript** | `.ts` |

---

## Contributing

We welcome contributions! Please open an issue or submit a pull request on GitHub.
