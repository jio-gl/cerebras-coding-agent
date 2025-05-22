import os
import pytest
from cerebras_agent.agent import CerebrasAgent
from unittest.mock import patch, MagicMock

@pytest.fixture
def agent():
    """Create a basic agent instance for testing."""
    api_key = os.environ.get("CEREBRAS_API_KEY")
    if not api_key:
        pytest.skip("CEREBRAS_API_KEY environment variable not set")
    return CerebrasAgent(api_key=api_key)

def test_parse_nodejs_errors(agent):
    """Test parsing various Node.js/JavaScript errors."""
    
    # ES6 Module error
    error = """
    import fs from 'fs';
    ^^^^^^

    SyntaxError: Cannot use import statement outside a module
        at Object.compileFunction (node:vm:360:18)
        at wrapSafe (node:internal/modules/cjs/loader:1088:15)
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "ES6 Module"
    assert "Cannot use import statement outside a module" in parsed["message"]
    assert "Add \"type\": \"module\" to package.json" in parsed["suggested_fix"]
    
    # Module not found error
    error = """
    Error: Cannot find module 'express'
        at Function.Module._resolveFilename (node:internal/modules/cjs/loader:995:15)
        at Function.Module._load (node:internal/modules/cjs/loader:841:27)
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "Import/Module" or parsed["error_type"] == "Reference"
    assert "Cannot find module" in parsed["message"]
    assert "Install the missing module" in parsed["suggested_fix"]
    
    # Syntax error
    error = """
    const obj = { name: 'test', value: 42, };  // Trailing comma
                                          ^

    SyntaxError: Unexpected token '}'
        at Object.compileFunction (node:vm:360:18)
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "SyntaxError" or parsed["error_type"] == "Syntax"
    assert "Unexpected token" in parsed["message"]
    assert "Fix syntax error" in parsed["suggested_fix"] or "missing" in parsed["suggested_fix"]
    
    # Reference error
    error = """
    ReferenceError: undefinedVariable is not defined
        at Object.<anonymous> (/app/index.js:2:13)
        at Module._compile (node:internal/modules/cjs/loader:1105:14)
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "ReferenceError" or parsed["error_type"] == "Reference"
    assert "not defined" in parsed["message"]
    assert "Define the variable" in parsed["suggested_fix"] or "check for typos" in parsed["suggested_fix"]
    assert parsed["file"] == "/app/index.js" or parsed["file"].endswith("index.js")
    assert parsed["line_number"] == "2"

def test_parse_python_errors(agent):
    """Test parsing various Python errors."""
    
    # Import error
    error = """
    Traceback (most recent call last):
      File "/app/script.py", line 1, in <module>
        import nonexistent_module
    ModuleNotFoundError: No module named 'nonexistent_module'
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "ModuleNotFoundError" or parsed["error_type"] == "Import/Module"
    assert "No module named" in parsed["message"]
    assert "pip install" in parsed["suggested_fix"]
    assert parsed["file"] == "/app/script.py" or parsed["file"].endswith("script.py")
    assert parsed["line_number"] == "1"
    
    # Syntax error
    error = """
    File "/app/script.py", line 2
        if True
              ^
    SyntaxError: invalid syntax
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "SyntaxError" or parsed["error_type"] == "Syntax"
    assert "invalid syntax" in parsed["message"]
    assert isinstance(parsed["suggested_fix"], str)
    assert len(parsed["suggested_fix"]) > 0
    assert parsed["file"] == "/app/script.py" or parsed["file"].endswith("script.py")
    assert parsed["line_number"] == "2"
    
    # Indentation error
    error = """
    File "/app/script.py", line 3
        print("indented incorrectly")
    ^
    IndentationError: unexpected indent
    """
    parsed = agent._parse_error_output(error)
    assert "IndentationError" in parsed["error_type"] or parsed["error_type"] == "Syntax"
    assert "indent" in parsed["message"]
    assert "indentation" in parsed["suggested_fix"].lower()
    assert parsed["file"] == "/app/script.py" or parsed["file"].endswith("script.py")
    assert parsed["line_number"] == "3"
    
    # Type error
    error = """
    Traceback (most recent call last):
      File "/app/script.py", line 5, in <module>
        result = "string" + 42
    TypeError: can only concatenate str (not "int") to str
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "TypeError" or parsed["error_type"] == "Type"
    assert "concatenate" in parsed["message"]
    assert parsed["file"] == "/app/script.py" or parsed["file"].endswith("script.py")
    assert parsed["line_number"] == "5"

def test_parse_java_errors(agent):
    """Test parsing Java errors."""
    
    # NullPointerException
    error = """
    Exception in thread "main" java.lang.NullPointerException
        at com.example.Main.processData(Main.java:25)
        at com.example.Main.main(Main.java:10)
    """
    parsed = agent._parse_error_output(error)
    assert "NullPointerException" in parsed["error_type"] or parsed["error_type"] == "Java Exception"
    assert "java.lang.NullPointerException" in parsed["message"]
    assert parsed["file"] == "Main.java" or parsed["file"].endswith("Main.java")
    assert parsed["line_number"] == "25" or parsed["line_number"] == "10"
    
    # ClassNotFoundException
    error = """
    Exception in thread "main" java.lang.ClassNotFoundException: com.example.MissingClass
        at java.base/jdk.internal.loader.BuiltinClassLoader.loadClass(BuiltinClassLoader.java:581)
        at java.base/jdk.internal.loader.ClassLoaders$AppClassLoader.loadClass(ClassLoaders.java:178)
    """
    parsed = agent._parse_error_output(error)
    assert "ClassNotFoundException" in parsed["error_type"] or parsed["error_type"] == "Java Exception"
    assert "MissingClass" in parsed["message"]
    
    # Compilation error
    error = """
    Main.java:15: error: incompatible types: String cannot be converted to int
        int value = "not an integer";
                    ^
    1 error
    """
    parsed = agent._parse_error_output(error)
    assert "incompatible types" in parsed["message"]
    assert parsed["file"] == "Main.java" or parsed["file"].endswith("Main.java")
    assert parsed["line_number"] == "15"

def test_parse_rust_errors(agent):
    """Test parsing Rust errors."""
    
    # Compiler error
    error = """
    error[E0308]: mismatched types
     --> src/main.rs:2:18
      |
    2 |     let x: i32 = "not a number";
      |             ---   ^^^^^^^^^^^^^ expected `i32`, found `&str`
      |             |
      |             expected due to this
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "Rust Compiler"
    assert "mismatched types" in parsed["message"]
    assert parsed["file"] == "src/main.rs" or parsed["file"].endswith("main.rs")
    assert parsed["line_number"] == "2"
    
    # Variable not found error
    error = """
    error[E0425]: cannot find value `nonexistent_variable` in this scope
     --> src/main.rs:4:13
      |
    4 |     println!("{}", nonexistent_variable);
      |                    ^^^^^^^^^^^^^^^^^^^^ not found in this scope
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "Rust Compiler"
    assert "cannot find value" in parsed["message"]
    assert parsed["file"] == "src/main.rs" or parsed["file"].endswith("main.rs")
    assert parsed["line_number"] == "4"

def test_parse_go_errors(agent):
    """Test parsing Go errors."""
    
    # Undefined variable
    error = """
    ./main.go:6:12: undefined: nonexistentVariable
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "Go Compiler"
    assert "undefined" in parsed["message"]
    assert parsed["file"] == "./main.go" or parsed["file"].endswith("main.go")
    assert parsed["line_number"] == "6"
    
    # Import error
    error = """
    main.go:3:8: package nonexistentPackage is not in GOROOT (/usr/local/go/src/nonexistentPackage)
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "Go Compiler"
    assert "package" in parsed["message"] and "not in GOROOT" in parsed["message"]
    assert parsed["file"] == "main.go" or parsed["file"].endswith("main.go")
    assert parsed["line_number"] == "3"

def test_parse_c_cpp_errors(agent):
    """Test parsing C/C++ errors."""
    
    # Syntax error
    error = """
    test.c:5:10: error: expected ';' after expression
        printf("Hello World")
                            ^
                            ;
    1 error generated.
    """
    parsed = agent._parse_error_output(error)
    assert parsed["error_type"] == "C/C++ Compiler"
    assert "expected ';'" in parsed["message"]
    assert parsed["file"] == "test.c" or parsed["file"].endswith("test.c")
    assert parsed["line_number"] == "5"
    
    # Undefined reference
    error = """
    /tmp/ccXrHuXL.o: In function `main':
    main.cpp:(.text+0x13): undefined reference to `nonexistentFunction()'
    collect2: error: ld returned 1 exit status
    """
    parsed = agent._parse_error_output(error)
    assert parsed["file"] == "main.cpp" or "main.cpp" in parsed["file"]
    assert isinstance(parsed["suggested_fix"], str)
    assert len(parsed["suggested_fix"]) > 0

def test_parse_generic_errors(agent):
    """Test parsing generic command-line errors."""
    
    # Command not found
    error = """
    bash: nonexistentCommand: command not found
    """
    parsed = agent._parse_error_output(error)
    assert "command not found" in parsed["message"]
    assert "Install the missing command" in parsed["suggested_fix"]
    
    # Permission denied
    error = """
    bash: ./script.sh: Permission denied
    """
    parsed = agent._parse_error_output(error)
    assert "Permission denied" in parsed["message"]
    assert "permissions" in parsed["suggested_fix"].lower() or "chmod" in parsed["suggested_fix"].lower()
    
    # No such file or directory
    error = """
    cat: nonexistentFile.txt: No such file or directory
    """
    parsed = agent._parse_error_output(error)
    assert "No such file or directory" in parsed["message"] 