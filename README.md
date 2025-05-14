# Stimela YAML Generator → CASA 

This project extracts Stimela-compatible YAML schemas from CASA task Python wrappers (e.g. `applycal.py`, `deconvolve.py`), using Python AST parsing, docstring introspection, and optional online validation against CASA XML documentation.

---

## 🚀 Features

- 🔍 **AST-based parsing** of CASA task wrappers
- 📋 **Structured YAML generation** in Stimela `cabs` format
- ✅ **Online validation** against CASA XML
- 🧠 **Fuzzy matching** for defaults like `float(0.1)` vs `0.1`
- 🛠 **Fix missing descriptions** with `--fix-description`
- 🧪 **Test suite** for multiple tasks using `pytest`

---

## ⚙️ Usage

### Generate YAML for a CASA Python task:

```bash
python generate_stimela_yaml.py applycal.py
```

### Validate YAML against online CASA XML documentation:

```bash
python generate_stimela_yaml.py applycal.py --validate-online
```

### Fix missing descriptions using CASA XML documentation

```bash
python generate_stimela_yaml.py applycal.py --fix-description
```

## 🧪 Running Tests

```bash
./run_tests.sh
```

Supports:

✅ YAML generation

✅ XML validation

✅ --fix-description functionality

✅ Comparison against expected YAML outputs

## 📦 Installation
Clone the repository and install requirements:

```bash
git clone https://github.com/razman786/stimela-yaml-generator.git
cd stimela-yaml-generator
pip install -r requirements.txt
```

## 📝 Directory Structure
.
├── generate_stimela_casa_cab.py     # Main CLI script
├── requirements.txt
├── tests/
│   ├── test_tasks.py            # Test suite
│   ├── fixtures/                # CASA task .py files
│   └── expected/                # Reference YAML files (optional)

## 📖 References

- [CASA Task Documentation](https://casadocs.readthedocs.io/en/v4.7-v6.1/)
- [CASA XML Index (v6.1.1)](https://casadocs.readthedocs.io/en/v4.7-v6.1/notebooks/XML611.html)
- [Stimela Parameter Schema](https://stimela.readthedocs.io/en/latest/fundamentals/params.html)

