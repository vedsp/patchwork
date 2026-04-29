import tree_sitter_python as tspython
import tree_sitter_javascript as tsjavascript
from tree_sitter import Language, Parser
import difflib
import git

LANGUAGES = {
    "python": tspython.language(),
    "javascript": tsjavascript.language(),
}

def read_file_at_ref(repo_path: str, ref: str, file_path: str) -> str:
    repo = git.Repo(repo_path)
    commit = repo.commit(ref)
    # Ensure forward slashes for Git internal paths
    git_path = file_path.replace("\\", "/")
    blob = commit.tree / git_path
    return blob.data_stream.read().decode("utf-8")

def extract_python_functions(root_node, source_bytes):
    functions = {}
    
    def walk(node):
        if node.type == "function_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                func_name = name_node.text.decode("utf-8")
                func_source = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
                functions[func_name] = func_source
        
        for child in node.children:
            walk(child)

    walk(root_node)
    return functions

def extract_javascript_functions(root_node, source_bytes):
    functions = {}
    
    def walk(node):
        # 1. function_declaration: function foo() {}
        if node.type == "function_declaration":
            name_node = node.child_by_field_name("name")
            if name_node:
                func_name = name_node.text.decode("utf-8")
                functions[func_name] = source_bytes[node.start_byte:node.end_byte].decode("utf-8")
        
        # 2. variable_declarator: const foo = () => {}
        elif node.type == "variable_declarator":
            value_node = node.child_by_field_name("value")
            if value_node and value_node.type == "arrow_function":
                name_node = node.child_by_field_name("name")
                if name_node:
                    func_name = name_node.text.decode("utf-8")
                    functions[func_name] = source_bytes[node.parent.start_byte:node.parent.end_byte].decode("utf-8")
        
        # 3. method_definition: class Foo { bar() {} }
        elif node.type == "method_definition":
            name_node = node.child_by_field_name("name")
            if name_node:
                func_name = name_node.text.decode("utf-8")
                functions[func_name] = source_bytes[node.start_byte:node.end_byte].decode("utf-8")

        for child in node.children:
            walk(child)

    walk(root_node)
    return functions

def snapshot(file_path: str = None, source: str = None, language: str = "python") -> dict[str, str]:
    if language not in LANGUAGES:
        raise ValueError(f"Unsupported language: {language}")

    PY_LANGUAGE = Language(LANGUAGES[language])
    parser = Parser(PY_LANGUAGE)
    
    if source is not None:
        source_bytes = source.encode("utf-8")
    elif file_path is not None:
        with open(file_path, "rb") as f:
            source_bytes = f.read()
    else:
        raise ValueError("Either source or file_path must be provided")
        
    tree = parser.parse(source_bytes)
    
    if tree.root_node.has_error:
        location = file_path if file_path else "provided source"
        raise SyntaxError(f"Syntax error detected in {location}")

    root_node = tree.root_node
    
    if language == "python":
        return extract_python_functions(root_node, source_bytes)
    elif language == "javascript":
        return extract_javascript_functions(root_node, source_bytes)
    
    return {}

def diff_snapshots(old: dict[str, str], new: dict[str, str]) -> dict:
    old_names = set(old.keys())
    new_names = set(new.keys())
    
    added = list(new_names - old_names)
    deleted = list(old_names - new_names)
    modified = [n for n in (old_names & new_names) if old[n] != new[n]]
            
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
