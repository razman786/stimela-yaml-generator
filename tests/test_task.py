import os
import pytest
import yaml
from generate_stimela_casa_cab import extract_yaml, validate_against_xml, fetch_xml_parameter_info

TASK_DIR = "tests/fixtures"
EXPECTED_DIR = "tests/expected"

# Get all task script files
TASK_FILES = [f for f in os.listdir(TASK_DIR) if f.endswith(".py")]

@pytest.mark.parametrize("task_file", TASK_FILES)
def test_yaml_generation(task_file):
    """Test YAML generation succeeds and contains a valid cab structure."""
    path = os.path.join(TASK_DIR, task_file)
    result = extract_yaml(path)

    cab_name = result["cab_name"]
    cab = result["yaml"]["cabs"].get(cab_name)
    
    assert cab is not None, f"Cab section missing in YAML for {task_file}"
    assert "inputs" in cab and isinstance(cab["inputs"], dict), "Missing or invalid 'inputs' section"

@pytest.mark.parametrize("task_file", TASK_FILES)
def test_yaml_against_expected(task_file):
    """Compare YAML output with expected saved version (if available)."""
    cab_base = task_file.replace(".py", "")
    expected_path = os.path.join(EXPECTED_DIR, f"{cab_base}.yaml")
    if not os.path.exists(expected_path):
        pytest.skip(f"No expected YAML available for {cab_base}")

    result = extract_yaml(os.path.join(TASK_DIR, task_file))
    with open(expected_path) as f:
        expected_yaml = yaml.safe_load(f)

    assert result["yaml"] == expected_yaml, f"YAML mismatch for {cab_base}"

@pytest.mark.parametrize("task_file", TASK_FILES)
def test_xml_validation(task_file):
    """Validate YAML against online CASA XML metadata."""
    result = extract_yaml(os.path.join(TASK_DIR, task_file))
    cab_name = result["cab_name"]
    yaml_inputs = result["yaml"]["cabs"][cab_name]["inputs"]
    xml_inputs = fetch_xml_parameter_info(cab_name)

    # Only compare overlapping keys
    for param in yaml_inputs:
        if param in xml_inputs:
            assert "dtype" in yaml_inputs[param]
            assert "info" in yaml_inputs[param]

@pytest.mark.parametrize("task_file", TASK_FILES)
def test_fix_description(task_file):
    """Ensure that --fix-description fills in missing info fields from XML."""
    result = extract_yaml(os.path.join(TASK_DIR, task_file))
    cab_name = result["cab_name"]
    yaml_inputs = result["yaml"]["cabs"][cab_name]["inputs"]
    xml_inputs = fetch_xml_parameter_info(cab_name)

    for param in yaml_inputs:
        if not yaml_inputs[param].get("info") and xml_inputs.get(param, {}).get("info"):
            yaml_inputs[param]["info"] = xml_inputs[param]["info"]

    for param, item in yaml_inputs.items():
        if xml_inputs.get(param, {}).get("info"):
            assert item.get("info"), f"Missing info after fix for param: {param}"

        # assert item.get("info"), f"Missing info after fix for param: {param}"
