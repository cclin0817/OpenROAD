# Bug Report: Python 3dblox Parser

This document lists bugs found in the Python 3dblox parser implementation.

## Bug #1: None/Null Values Converted to String "None"

**Severity:** High
**Files Affected:**
- `py3dblox/dbx_parser.py` (lines 116, 276, 281)

**Description:**
When YAML fields contain null values (`~` in YAML syntax), the parser incorrectly converts them to the string `"None"` instead of preserving them as Python `None` objects.

**Root Cause:**
The code uses `str()` conversion on values without checking if they are `None`:
```python
connection.top = str(connection_node['top'])  # Line 276
connection.bot = str(connection_node['bot'])  # Line 281
design = DesignDef(name=str(design_node['name']))  # Line 116
```

**Example:**
```yaml
Connection:
  soc_to_virtual:
    top: soc_inst_duplicate.regions.r1
    bot: ~  # YAML null
    thickness: 0.0
```

Current behavior: `connection.bot == "None"` (string)
Expected behavior: `connection.bot is None` (NoneType)

**Impact:**
- Semantic meaning is lost (null vs string "None")
- Downstream code cannot distinguish between intentional null values and the string "None"
- Type confusion in code that checks for None values

**Affected Fields:**
- `DbxData.design.name`
- `Connection.top`
- `Connection.bot`
- Potentially other string fields that use `str()` conversion

---

## Bug #2: Wildcard Paths Only Work in Filename

**Severity:** Medium
**Files Affected:**
- `py3dblox/base_parser.py` (lines 87-114, method `resolve_paths`)

**Description:**
The `resolve_paths` function only supports wildcards (`*`) in the filename portion of a path, not in directory components. Attempting to use wildcards in the middle of a path causes an error.

**Root Cause:**
The implementation assumes wildcards only appear in the last path component:
```python
if '*' in path_pattern:
    directory = resolved.parent  # Gets parent of /path/*/file.txt -> /path/*
    pattern = resolved.name      # Gets filename

    if not directory.exists() or not directory.is_dir():
        self.log_error(f"Directory does not exist: {directory}")
```

**Example:**
```python
# Works:
resolve_paths("/some/path/*.txt")

# Fails with "Directory does not exist: /some/*":
resolve_paths("/some/*/path/file.txt")
```

**Impact:**
- Cannot use wildcards in directory names
- Limits flexibility when specifying paths with variable directory components
- Error message is confusing (claims directory doesn't exist when it's actually a pattern)

**Suggested Fix:**
Use `pathlib.Path.glob()` or `glob.glob()` for proper wildcard support throughout the entire path.

---

## Bug #3: Missing Validation for Required Non-Null Values

**Severity:** Medium
**Files Affected:**
- `py3dblox/dbx_parser.py` (multiple locations)

**Description:**
The parser checks if required keys exist in YAML nodes but doesn't validate that the values are not null. This allows invalid configurations to pass validation.

**Example:**
```python
if 'name' not in design_node:
    self.log_error("DBX Design name is required")
design = DesignDef(name=str(design_node['name']))  # No check if name is None
```

**Test Case:**
```yaml
Design:
  name: ~  # Should fail validation but currently passes
```

**Impact:**
- Invalid configurations are not caught during parsing
- Required fields can be null, leading to unexpected behavior
- Combined with Bug #1, results in string "None" values in required fields

**Affected Fields:**
- `Design.name` (required but can be null)
- `Connection.top` (required but can be null)
- `Connection.bot` (required but can be null)
- `ChipletInst.reference` (required but can be null)
- `ChipletDef.type` (required but can be null)

---

## Limitation #1: Unimplemented Fields

**Severity:** Low (Feature Gap)
**Files Affected:**
- `py3dblox/dbv_parser.py`

**Description:**
The `.3dbv` example file contains a `cad_layer` field that is not parsed by the current implementation. This data is silently ignored.

**Example:**
```yaml
ChipletDef:
  SoC:
    type: die
    cad_layer:
      108;101:
        type: design_area
```

**Impact:**
- Data loss during parsing
- No warning to users that data is being ignored
- Possible feature incompleteness

---

## Testing Recommendations

1. Add test cases for null/None values in all string fields
2. Add validation tests to ensure required fields reject null values
3. Add wildcard path tests covering:
   - Wildcards in filename (currently works)
   - Wildcards in directory paths (currently fails)
   - Multiple wildcards in single path
4. Add tests for the `cad_layer` field once implemented
5. Consider adding a strict mode that warns about unrecognized YAML fields

---

## Summary

**Critical bugs:** 1 (Bug #1)
**Non-critical bugs:** 2 (Bugs #2, #3)
**Limitations:** 1

The most critical issue is Bug #1, which causes data corruption by converting null values to the string "None". This should be fixed as a priority.
