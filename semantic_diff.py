import difflib
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

def snapshot(file_path: str) -> dict[str, str]:
    PY_LANGUAGE = Language(tspython.language())
    parser = Parser(PY_LANGUAGE)
    
    with open(file_path, "rb") as f:
        source_bytes = f.read()
        
    tree = parser.parse(source_bytes)
    root_node = tree.root_node
    
    functions = {}
    
    for node in root_node.children:
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                func_name = name_node.text.decode("utf-8")
                # Slice raw source using precise byte offsets
                func_source = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
                functions[func_name] = func_source
                
    return functions

def diff_snapshots(old: dict[str, str], new: dict[str, str]) -> dict:
    old_names = set(old.keys())
    new_names = set(new.keys())
    
    added = list(new_names - old_names)
    deleted = list(old_names - new_names)
    modified = []
    
    common = old_names & new_names
    for name in common:
        if old[name] != new[name]:
            modified.append(name)
            
    return {
        "added": added,
        "deleted": deleted,
        "modified": modified
    }

def line_diff(old_source: str, new_source: str, func_name: str) -> str:
    diff = difflib.unified_diff(
        old_source.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=f"old/{func_name}",
        tofile=f"new/{func_name}"
    )
    return "".join(diff)

def main(old_path, new_path):
    old_snap = snapshot(old_path)
    new_snap = snapshot(new_path)
    
    diff = diff_snapshots(old_snap, new_snap)
    
    print(f"--- Semantic Diff: {old_path} vs {new_path} ---\n")
    
    if diff["added"]:
        print("ADDED FUNCTIONS:")
        for name in diff["added"]:
            print(f"  + {name}")
        print()

    if diff["deleted"]:
        print("DELETED FUNCTIONS:")
        for name in diff["deleted"]:
            print(f"  - {name}")
        print()

    if diff["modified"]:
        print("MODIFIED FUNCTIONS:")
        for name in diff["modified"]:
            print(f"--- diff for: {name} ---")
            print(line_diff(old_snap[name], new_snap[name], name))
            print()

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python semantic_diff.py old.py new.py")
