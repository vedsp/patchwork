### Resume Bullet Points

*   Engineered a semantic diff engine using **tree-sitter** to perform **AST-based** analysis on Python and JavaScript files.
*   Developed a high-performance CLI using **Click**, **Rich**, and **Textual**, achieving sub-second diffing for 1k+ line files.
*   Integrated **GitPython** to enable direct object-store analysis of Git refs, eliminating the need for working-tree checkouts.

### Project Description

**Patchwork** is a professional-grade semantic code diff tool designed to help developers audit logic changes across commits with high precision. By leveraging tree-sitter grammars to parse code into Abstract Syntax Trees, it identifies functional modifications (added, deleted, or changed functions) rather than raw line-level edits. The tool features a Git-integrated CLI and a side-by-side TUI, providing a modern, language-agnostic interface for deep code analysis.
