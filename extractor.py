import tree_sitter_python as tspython
from tree_sitter import Language, Parser

def extract_functions(file_path: str) -> list[dict]:
    try:
        # Initialize parser
        PY_LANGUAGE = Language(tspython.language())
        parser = Parser(PY_LANGUAGE)

        with open(file_path, "rb") as f:
            code = f.read()

        tree = parser.parse(code)
        root_node = tree.root_node
        functions = []

        # Iterate over the top-level nodes in the file
        for node in root_node.children:
            if node.type == "function_definition":
                # The name is usually a child node of type 'identifier'
                # In tree-sitter-python, the function name is a specific child
                name_node = node.child_by_field_name("name")
                
                if name_node:
                    # node.text gives us the raw bytes, so we decode it to string
                    # node.start_point.row is 0-indexed, so we add 1 for humans
                    functions.append({
                        "name": name_node.text.decode("utf-8"),
                        "start_line": node.start_point[0] + 1,
                        "end_line": node.end_point[0] + 1
                    })
        
        return functions

    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

if __name__ == "__main__":
    # Test it on our dummy file!
    results = extract_functions("dummy.py")
    print("Functions found:")
    for func in results:
        print(f"- {func['name']} (Lines {func['start_line']}-{func['end_line']})")
