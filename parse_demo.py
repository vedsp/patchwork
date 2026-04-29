import sys
import tree_sitter_python as tspython
from tree_sitter import Language, Parser

def main():
    # Make sure the user provided a file path
    if len(sys.argv) < 2:
        print("Usage: python parse_demo.py <path_to_file.py>")
        return

    file_path = sys.argv[1]

    # 1. Initialize the Language using the Python grammar
    PY_LANGUAGE = Language(tspython.language())
    
    # 2. Create a Parser instance and hand it our language
    parser = Parser(PY_LANGUAGE)

    # 3. Read the target file in binary mode ("rb"). 
    # Tree-sitter works with raw bytes to perfectly track character offsets.
    with open(file_path, "rb") as f:
        code = f.read()

    # 4. Parse the code! This returns a Tree object.
    tree = parser.parse(code)

    # 5. Extract the root node from the Tree
    root_node = tree.root_node

    # 6. Print the tree as an S-expression
    print(root_node)

if __name__ == "__main__":
    main()
