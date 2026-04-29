import pytest
from click.testing import CliRunner
from patchwork.engine import snapshot, diff_snapshots, line_diff
from patchwork.cli import cli

# 1. Snapshot of a file with 3 functions returns correct dict keys
def test_snapshot_extraction():
    source = """
def func1(): pass
def func2(): pass
def func3(): pass
"""
    snap = snapshot(source=source, language="python")
    assert set(snap.keys()) == {"func1", "func2", "func3"}

# 2. Snapshot of an empty file returns empty dict
def test_snapshot_empty():
    snap = snapshot(source="", language="python")
    assert snap == {}

# 3. diff_snapshots detects an added function correctly
def test_diff_added():
    old = {"f1": "src"}
    new = {"f1": "src", "f2": "src"}
    results = diff_snapshots(old, new)
    assert results["added"] == ["f2"]

# 4. diff_snapshots detects a deleted function correctly
def test_diff_deleted():
    old = {"f1": "src", "f2": "src"}
    new = {"f1": "src"}
    results = diff_snapshots(old, new)
    assert results["deleted"] == ["f2"]

# 5. diff_snapshots detects a modified function correctly
def test_diff_modified():
    old = {"f1": "src_v1"}
    new = {"f1": "src_v2"}
    results = diff_snapshots(old, new)
    assert results["modified"] == ["f1"]

# 6. diff_snapshots returns no changes for identical snapshots
def test_diff_no_changes():
    old = {"f1": "src"}
    new = {"f1": "src"}
    results = diff_snapshots(old, new)
    assert not results["added"]
    assert not results["deleted"]
    assert not results["modified"]

# 7. line_diff returns a non-empty string for changed functions
def test_line_diff_output():
    diff = line_diff("line1\n", "line1\nline2\n", "f1")
    assert isinstance(diff, str)
    assert len(diff) > 0

# 8. line_diff output contains + and - markers
def test_line_diff_markers():
    diff = line_diff("old\n", "new\n", "f1")
    assert "-" in diff
    assert "+" in diff

# 9. read_file_at_ref raises a clean error for an invalid ref
# (Note: Requires a repo context, mocked or integrated)
def test_invalid_ref():
    import git
    with pytest.raises(Exception):
        from patchwork.engine import read_file_at_ref
        read_file_at_ref(".", "non-existent-ref", "any.py")

# 10. CLI exits with code 1 for a missing file
def test_cli_missing_file():
    runner = CliRunner()
    result = runner.invoke(cli, ["diff", "missing1.py", "missing2.py"])
    assert result.exit_code == 1
    assert "File not found" in result.output
