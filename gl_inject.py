import re

HEADER_PATH = "gl.h"
OUTPUT_PATH = "gl_passthrough.cpp"

# For each function, generate a signature that returns either nothing or an empty initializer list
header = open(HEADER_PATH, 'r')
output = open(OUTPUT_PATH, 'w')

output.write("#include <khrplatform.h>\n")
output.write("\n")

# If our codegen had C++ semantics then manual type conversions like this would be less necessary
while True:
    line = header.readline()
    if not line:
        break

    # Matches typedefs for plain types while excluding function pointer typedefs
    typedef_match = re.search(r"typedef (.*) ([*\w]*);", line)
    if typedef_match:
        original_type = typedef_match.group(1)
        new_type = typedef_match.group(2)
        output.write(" ".join(["typedef", original_type, new_type, ";\n"]))

    function_match = re.search(r"GLAPI (.*) APIENTRY (.*?) (.*);", line)
    if function_match:
        type = function_match.group(1)
        func_name = function_match.group(2)
        arg_list = function_match.group(3)

        # We exclude a few debugging function intercepts here making our mock implementation incomplete.
        if "PROC" in arg_list:
            pass

        if type == "void":
            ret_val = "";

        else:
            # This works as a defualt initializer for POD or non-POD types
            ret_val = "{}";

        output.write(" ".join([type, func_name, arg_list, '''{
   return''', ret_val, ''';
}

''']))
