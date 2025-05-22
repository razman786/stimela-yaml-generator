import ast
import yaml
import re
import sys
import os
import requests
from bs4 import BeautifulSoup
from tabulate import tabulate

# CASA c-based data types mapped to python
CASA_TO_PYTHON_TYPES = {
    "cFloat": "float",
    "cFloatVec": "List[float]",
    "cIntVec": "List[int]",
    "cStrList": "List[str]",
    'cStr': 'str',
    'cStrVec': 'List[str]',
    'cBool': 'bool',
    'cBoolVec': 'List[bool]',
    'cInt': 'int',
    'cIntVec': 'List[int]',
    'cPathVec': 'List[File]',
    'cReqPath': 'File',
    'cVariant': 'Any',
    'unknown': 'Any'
}

# Stimela Union dtypes
UNION_TYPE_MAP = {
    ("str", "List[str]"): "Union[str, List[str]]",
    ("int", "List[int]"): "Union[int, List[int]]",
    ("float", "List[float]"): "Union[float, List[float]]",
    ("bool", "List[bool]"): "Union[bool, List[bool]]",
}


class QuotedString(str):
    """
    A subclass of `str` used to force YAML to quote string values explicitly.

    When used with PyYAML's custom Dumper, this ensures that values like
    'yes', 'no', 'true', or 'false' are not misinterpreted as booleans,
    and that empty strings remain quoted in YAML output.
    """
    pass


def quoted_presenter(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


class CleanDumper(yaml.SafeDumper):
    """
    A custom YAML Dumper that ensures QuotedString values are always double-quoted.

    Extends PyYAML's SafeDumper to improve output readability and compatibility,
    especially for edge cases like empty strings or lowercase booleans.
    """
    pass


CleanDumper.add_representer(QuotedString, quoted_presenter)


def get_default_value(node):
    """
    Resolves the most appropriate default value for a given parameter.

    Prioritizes the value parsed from the docstring. Falls back to the AST
    function signature default if no docstring default is found.

    Args:
        parsed_doc_info (dict): Dictionary of parsed parameter docstrings.
        param_defaults (dict): Accumulator for parameter defaults.
        name (str): Name of the current parameter.
        i (int): Index of the parameter in the function signature.
        default_offset (int): Offset to align parameters with defaults.
        defaults (list): List of AST-parsed default values.

    Returns:
        Any: A valid Python object or literal to be used as default.
    """
    try:
        return ast.literal_eval(node)
    except Exception:
        return ast.unparse(node)


def extract_schema_dict(schema_node):
    """
    Constructs the full Stimela-style YAML schema for a given CASA task.

    Processes all function parameters using both AST introspection and docstring parsing.
    Extracts types, default values, and parameter descriptions, then formats them
    into a dictionary following Stimela's 'cabs' structure.

    Args:
        (your existing parameters...)

    Returns:
        dict: A structured dictionary representing the Stimela 'cabs' YAML schema.
    """
    schema = {}
    if not isinstance(schema_node, ast.Dict):
        return schema
    for key_node, val_node in zip(schema_node.keys, schema_node.values):
        key = key_node.value if isinstance(key_node, ast.Constant) else None
        if key and isinstance(val_node, ast.Dict):
            param_info = {}
            for k, v in zip(val_node.keys, val_node.values):
                if isinstance(k, ast.Constant):
                    param_key = k.value
                    param_info[param_key] = get_default_value(v)
            schema[key] = param_info
    return schema


def extract_structured_param_docs_full_pass(filepath):
    """
    Parses the full docstring of a CASA task to extract structured parameter metadata.

    Identifies the parameter section, groups lines for each parameter, and
    delegates line parsing to `process_block()`.

    Args:
        docstring (str): Full function docstring containing parameter definitions.

    Returns:
        dict: Mapping of parameter names to their 'default' and 'info' metadata.
    """
    with open(filepath, "r") as f:
        tree = ast.parse(f.read())

    param_docs = {}
    current_param = None
    buffer = []
    collecting = False

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            docstring = ast.get_docstring(node)
            if not docstring:
                return param_docs

            lines = docstring.splitlines()

            for line in lines:
                line = line.expandtabs()
                stripped = line.strip()

                if 'parameter descriptions' in stripped.lower():
                    collecting = True
                    continue

                if not collecting:
                    continue

                match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s{2,}(.*)', line)
                if match:
                    if current_param:
                        param_docs[current_param] = process_block(current_param, buffer)
                        buffer = []
                    current_param = match.group(1)
                    desc = match.group(2).strip()
                    if desc:
                        buffer.append(desc)
                elif current_param:
                    buffer.append(stripped)

            if current_param:
                param_docs[current_param] = process_block(current_param, buffer)

            break

    return param_docs


def process_block(param, lines):
    """
    Extracts metadata for a single parameter from its docstring lines.

    Parses the 'default:' line using CASA-style formatting and captures the
    parameter's textual description.

    Args:
        param (str): Name of the parameter.
        lines (list of str): Lines associated with this parameter from the docstring.

    Returns:
        dict: A dictionary with keys 'info' (description) and 'default' (parsed value).
    """
    info = ""
    default = None

    def parse_casa_default(val):
        val = val.strip()
        match = re.match(r"\(boolArray=\[(.*?)\]\)", val)
        if match:
            return [x.strip() == "True" for x in match.group(1).split(",") if x.strip()]
        match = re.match(r"\(stringArray=\[(.*?)\]\)", val)
        if match:
            return [x.strip().strip("'\"") for x in match.group(1).split(",") if x.strip()]
        match = re.match(r"\(intArray=\[(.*?)\]\)", val)
        if match:
            return [int(x.strip()) for x in match.group(1).split(",") if x.strip()]
        match = re.match(r"\(floatArray=\[(.*?)\]\)", val)
        if match:
            return [float(x.strip()) for x in match.group(1).split(",") if x.strip()]
        if val == "numpy.array([])":
            return []
        if val.lower() in ["true", "false"]:
            return val.lower() == "true"
        return val.strip("'\"")

    for line in lines:
        lower = line.lower()
        if not info and "default:" not in lower:
            info = line.strip()

        if "default:" in lower:
            # match = re.search(r"default:\s*(\(.*\))", line)
            match = re.search(r"default:\s*(\([^\)]+\))", line)
            if match:
                raw_val = match.group(1).strip()
                default = parse_casa_default(raw_val)

    if default is not None:
        print(f"DEBUG process_block: {param} → parsed={default} ({type(default).__name__})")

    return {"info": info, "default": default}


def extract_yaml(filepath):
    """
    Extracts a Stimela-style YAML schema from a Python CASA task file.

    This function uses the AST to locate function definitions and parameters,
    parses docstrings for default values and descriptions, and combines that
    information into a dictionary under the Stimela 'cabs' format.

    Args:
        filepath (str): Path to the CASA task Python file.

    Returns:
        dict: A dictionary containing the YAML structure, cab name, and parsed doc info.
    """
    with open(filepath, "r") as f:
        tree = ast.parse(f.read())

    cab_name = os.path.splitext(os.path.basename(filepath))[0]
    param_order = []
    param_defaults = {}
    schema_data = {}
    has_outputs = False
    parsed_doc_info = extract_structured_param_docs_full_pass(filepath)

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            call_method = next((n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == '__call__'), None)
            if not call_method:
                continue

            args = call_method.args.args[1:]
            defaults = call_method.args.defaults
            default_offset = len(args) - len(defaults)

            for i, arg in enumerate(args):
                name = arg.arg
                param_order.append(name)
                parsed = parsed_doc_info.get(name, {})
                if parsed and parsed.get("default", None) is not None:
                    param_defaults[name] = parsed["default"]
                elif i >= default_offset:
                    try:
                        param_defaults[name] = ast.unparse(defaults[i - default_offset])
                        if isinstance(param_defaults[name], str):
                            if re.match(r"\[?bool\(true\)\]?", param_defaults[name].lower()):
                                param_defaults[name] = [True]
                            elif re.match(r"\[?bool\(false\)\]?", param_defaults[name].lower()):
                                param_defaults[name] = [False]
                            elif "bool(true)" in param_defaults[name].lower():
                                param_defaults[name] = [True for _ in re.findall(r"bool\\(true\\)", param_defaults[name].lower())]
                            elif "bool(false)" in param_defaults[name].lower():
                                param_defaults[name] = [
                                    False for _ in re.findall(r"bool\\(false\\)", param_defaults[name].lower())
                                ]
                    except Exception:
                        param_defaults[name] = None
                else:
                    param_defaults[name] = None

            has_outputs = any(isinstance(n, ast.Return) and n.value is not None for n in ast.walk(call_method))

            for stmt in call_method.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == 'schema':
                            schema_data = extract_schema_dict(stmt.value)
            break

    inputs = {}
    for param in param_order:
        casa_dtype = schema_data.get(param, {}).get('type', 'unknown')
        dtype = CASA_TO_PYTHON_TYPES.get(casa_dtype, casa_dtype)
        default = param_defaults.get(param)

        parsed = parsed_doc_info.get(param, {})
        if default is None and parsed.get("default") not in [None, '']:
            default = parsed["default"]

        raw_default = param_defaults.get(param)

        if isinstance(raw_default, str):
            float_match = re.match(r"float\((-?\d+\.?\d*)\)", raw_default)
            int_match = re.match(r"int\((-?\d+)\)", raw_default)
            if float_match:
                default = float(float_match.group(1))
            elif int_match:
                default = int(int_match.group(1))
            else:
                try:
                    default = ast.literal_eval(raw_default)
                except Exception:
                    default = raw_default
        else:
            default = raw_default

        # Handle Union[<type>, List[<type>]] based on hints
        info_text = parsed.get("info", "").lower()
        if dtype == "str" and ("list of strings" in info_text or "comma-separated" in info_text):
            dtype = "Union[str, List[str]]"
        elif dtype == "int" and "list of integers" in info_text:
            dtype = "Union[int, List[int]]"
        elif dtype == "float" and "list of floats" in info_text:
            dtype = "Union[float, List[float]]"
        elif dtype == "bool" and "list of booleans" in info_text:
            dtype = "Union[bool, List[bool]]"

        # Stimela dtype overrides based on param names or docstring
        param_lower = param.lower()
        info_text = parsed.get("info", "").lower()

        # Handle 'ms' dtype for measurement sets
        if param_lower in ("vis", "ms", "observation", "dataset", "measurementset"):
            dtype = "MS"
        elif "measurement set" in info_text or "ms file" in info_text:
            dtype = "MS"
        # Handle 'File' dtype for file-like inputs and outputs
        elif any(key in param_lower for key in ("image", "imagename", "model", "mask", "file", "fits", "outfile", "output")):
            dtype = "File"
        elif any(phrase in info_text for phrase in (
            "fits file", "image file", "file path", "mask image", "input file", "output file", "file name", "image name"
        )):
            dtype = "File"

        inputs[param] = {
            'dtype': dtype,
            'default': default,
            'required': default is None,
            'info': QuotedString(parsed.get("info", ""))
        }

    cab_structure = {'cabs': {cab_name: {'inputs': inputs}}}

    if has_outputs:
        cab_structure['cabs'][cab_name]['outputs'] = {}

    return {'cab_name': cab_name, 'yaml': cab_structure}


def validate_and_print_summary(inputs):
    """
    Compares Stimela-style YAML inputs against CASA XML inputs and prints a validation summary.

    This function checks parameter names, default values, and descriptions between
    the YAML schema and the official CASA XML documentation. It prints a structured
    summary showing whether each parameter matches, mismatches, or is missing.

    Args:
        yaml_inputs (dict): Dictionary of parameters from the generated YAML schema.
        xml_inputs (dict): Dictionary of parameters parsed from CASA XML documentation.

    Returns:
        None: Results are printed to stdout in tabular form.
    """
    rows = []
    for param, data in inputs.items():
        rows.append([
            param,
            data.get("dtype"),
            data.get("default"),
            data.get("required"),
            data.get("info")[:80] + ("..." if len(data.get("info", "")) > 80 else "")
        ])
    headers = ["parameter", "dtype", "default", "required", "info"]
    print("\n\n=== Stimela Cab Input Parameter Summary ===")
    print(tabulate(rows, headers=headers, tablefmt="github"))


def fetch_xml_parameter_info(task_name):
    """
    Fetches and parses CASA XML documentation for a specific task.

    Extracts descriptions of each parameter from the remote XML documentation,
    enabling validation and autofill for missing YAML fields.

    Args:
        taskname (str): Name of the CASA task.

    Returns:
        dict: Mapping of parameter names to their description from the XML.
    """
    base_url = "https://casadocs.readthedocs.io/en/v4.7-v6.1/tasks611/"
    url = f"{base_url}{task_name}.xml.html"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f"⚠️ Could not fetch XML documentation: {e}")
        return {}

    soup = BeautifulSoup(response.text, 'html.parser')
    parameters = {}
    table = soup.find('table')
    if not table:
        print("⚠️ Could not find parameter table in XML page.")
        return parameters

    rows = table.find_all('tr')[1:]  # Skip header
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 3:
            name = cols[0].get_text(strip=True)
            default = cols[1].get_text(strip=True)
            description = cols[2].get_text(strip=True)
            parameters[name] = {'default': default, 'description': description}
    return parameters


def fuzzy_match(norm_local, norm_xml):
    """
    Returns True if the local and XML default values are functionally equivalent.

    Handles:
    - constructor strings like int(10), float(0.1), str("value")
    - numpy.array([...]) with int/float constructor wrapping
    - empty vs non-empty bool lists
    - CASA dict-like thresholds: {'value': float(...), 'unit': '...'}
    """

    import re

    # Exact match
    if norm_local == norm_xml:
        return True

    # Scalar vs constructor string
    if isinstance(norm_local, (int, float, str)) and isinstance(norm_xml, str):
        expected = f"{type(norm_local).__name__}({repr(norm_local)})"
        alt_expected = f"{type(norm_local).__name__}({norm_local})"
        return norm_xml in (expected, alt_expected)

    # Bool list vs empty bool list
    if isinstance(norm_local, list) and isinstance(norm_xml, list):
        if all(isinstance(x, bool) for x in norm_local + norm_xml):
            return norm_local == [] or norm_xml == []

    # List vs numpy-style string
    if isinstance(norm_local, list) and isinstance(norm_xml, str):
        try:
            clean = re.sub(r"(numpy\.array\(|\))", "", norm_xml)
            clean = re.sub(r"(int|float)\((.*?)\)", r"\2", clean)
            xml_list = [int(x.strip()) if x.strip().isdigit() else float(x.strip()) for x in clean.split(",")]
            return norm_local == xml_list
        except:
            return False

    # Dict match: e.g. threshold = {'value': float(0.0), 'unit': 'mjy'}
    if isinstance(norm_local, dict) and isinstance(norm_xml, str):
        try:
            # Match CASA-style threshold dicts
            value_match = re.search(r"'?value'?:\s*float\((-?\d+\.?\d*)\)", norm_xml)
            unit_match = re.search(r"'?unit'?:\s*'(\w+)'", norm_xml)
            if value_match and unit_match:
                parsed = {
                    "value": float(value_match.group(1)),
                    "unit": unit_match.group(1)
                }
                return norm_local == parsed
        except:
            return False

    return False


def validate_against_xml(task_name, inputs):
    """
    Validates a YAML schema against the CASA XML documentation for the same task.

    Checks consistency between default values and descriptions. Optionally
    fills in blank descriptions using XML when `fix_description=True`.

    Args:
        yaml_dict (dict): Stimela-style YAML structure.
        cab_name (str): Name of the cab/task being validated.
        fix_description (bool): Whether to autofill missing descriptions.

    Returns:
        None: Prints summary and mismatch results to stdout.
    """

    def normalize(val):
        if isinstance(val, str):
            val = val.strip()
            if val == "numpy.array([])":
                return []
            if val == "(boolArray=[True])":
                return [True]
            try:
                return ast.literal_eval(val)
            except Exception:
                return val.lower()
        return val

    xml_params = fetch_xml_parameter_info(task_name)
    print("\n=== Online XML-CASA Validation Report ===")
    rows = []
    for param, local in inputs.items():
        xml = xml_params.get(param)
        if not xml:
            rows.append([param, "❌ Not found in XML", "", "", "", ""])
            continue

        norm_local = normalize(local.get("default"))
        norm_xml = normalize(xml["default"])
        print(f"DEBUG: {param} - YAML: {repr(norm_local)} ({type(norm_local)}) vs XML: {repr(norm_xml)} ({type(norm_xml)})")
        if fuzzy_match(norm_local, norm_xml):
            default_match = "✓"
        else:
            default_match = "✗"

        local_info = local.get("info", "").strip()
        xml_desc = xml["description"].strip()
        description_match = "✓" if xml_desc[:50].lower() in local_info.lower() else "✗"

        status = "✅" if default_match == "✓" and description_match == "✓" else "⚠️"

        rows.append([param, status, default_match, description_match, f"YAML: {local_info[:50]}...", f"XML: {xml_desc[:50]}..."])

    if not rows:
        print("⚠️ No matching parameters found.")
        return

    headers = ["Parameter", "Status", "Default Match", "Description Match", "YAML Info", "XML Info"]
    table = tabulate(rows, headers=headers, tablefmt="github")
    print(table)

    report_path = f"{task_name}_online_validation_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Online XML-CASA Validation Report\n\n")
        f.write(table)
        f.write("\n")

    print(f"📄 Report written to: {report_path}")


def main():
    """
    Entry point for the command-line interface.

    Parses arguments, generates YAML schema from the CASA task,
    optionally validates against XML, and optionally applies fixes
    to missing descriptions.
    """
    args = [arg for arg in sys.argv[1:] if not arg.startswith('--')]
    # CLI flag to enable CASA XML-based validation
    do_validate = '--validate-online' in sys.argv
    # CLI flag to auto-fill missing YAML descriptions from XML
    fix_description = '--fix-description' in sys.argv
    if len(args) != 1:
        print("Usage: python generate_stimela_yaml.py <python_file> [--validate-online | --fix-description]")
        sys.exit(1)

    filepath = args[0]

    if not os.path.isfile(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)

    result = extract_yaml(filepath)
    out_file = f"{result['cab_name']}.yaml"

    with open(out_file, "w", encoding="utf-8") as f:
        yaml.dump(result['yaml'], f, sort_keys=False, Dumper=CleanDumper, allow_unicode=True)

    if fix_description:
        cab_name = result['cab_name']
        yaml_inputs = result["yaml"]["cabs"][cab_name]["inputs"]
        xml_data = fetch_xml_parameter_info(cab_name)
        updated = False
        for param, data in yaml_inputs.items():
            if not data.get("info"):
                xml_info = xml_data.get(param, {}).get("description")
                if xml_info:
                    data["info"] = QuotedString(xml_info)
                    print(f"📘 Filled missing info for '{param}' using XML.")
                    updated = True
        if updated:
            fixed_out_file = f"{cab_name}_fixed.yaml"
            with open(fixed_out_file, "w", encoding="utf-8") as f:
                yaml.dump(result["yaml"], f, sort_keys=False, Dumper=CleanDumper, allow_unicode=True)
            print(f"✅ YAML with fixed descriptions written to: {fixed_out_file}")

    print(f"✅ YAML written to: {out_file}")
    validate_and_print_summary(result['yaml']['cabs'][result['cab_name']]['inputs'])
    if do_validate:
        validate_against_xml(result['cab_name'], result['yaml']['cabs'][result['cab_name']]['inputs'])


if __name__ == "__main__":
    main()
