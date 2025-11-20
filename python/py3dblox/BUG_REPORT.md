# Bug Report: Python 3dblox Parser

## Summary

After comparing the Python implementation with the C++ reference implementation, **one confirmed bug was found and fixed**.

## Bug #1: None/Null Values Converted to String "None" [FIXED]

**Status:** ✅ FIXED

**Severity:** High

**Files Affected:**
- `py3dblox/base_parser.py` (extract_value method)
- `py3dblox/dbx_parser.py` (multiple methods)
- `py3dblox/dbv_parser.py` (multiple methods)
- `py3dblox/objects.py` (Connection class)

**Description:**
When YAML fields contained null values (`~` in YAML syntax), the parser incorrectly converted them to the string `"None"` instead of preserving them as Python `None` objects.

**Root Cause:**
The code used `str()` conversion on values without checking if they were `None`:
```python
connection.bot = str(connection_node['bot'])  # Before fix
```

When the YAML value was `~` (null), `connection_node['bot']` would be `None`, and `str(None)` produces the string `"None"`.

**Example:**
```yaml
Connection:
  soc_to_virtual:
    top: soc_inst_duplicate.regions.r1
    bot: ~  # YAML null
    thickness: 0.0
```

**Before fix:**
- `connection.bot == "None"` (string)

**After fix:**
- `connection.bot is None` (NoneType)

**Fix Applied:**
1. Updated `extract_value()` method in `base_parser.py` to check for None values before type conversion
2. Replaced all `str(node[key])` calls with `extract_value(node, key, str)` throughout the codebase
3. Updated type annotations to allow `str | None` where appropriate (e.g., `Connection.top`, `Connection.bot`)
4. Added proper None handling when assigning extracted values

**Verification:**
The C++ test suite (`Test3DBloxParser.cpp:111`) confirms that `connection->getBottomRegion()` should be `nullptr` when `bot: ~` is in the YAML, validating this fix.

---

## Issue #2: Wildcard Paths Only Work in Filename [NOT A BUG]

**Status:** ℹ️ NOT A BUG (Consistent with C++ implementation)

**Description:**
The `resolve_paths` function only supports wildcards (`*`) in the filename portion of a path, not in directory components.

**C++ Reference:**
The C++ implementation in `baseParser.cpp:155` has the same limitation:
```cpp
const std::string filename_pattern = path_fs.filename().string();
```

**Conclusion:**
This is a design limitation shared by both implementations, not a bug in the Python version.

---

## Issue #3: Missing Validation for Required Non-Null Values [NOT A BUG]

**Status:** ℹ️ NOT A BUG (Null values are intentionally allowed)

**Description:**
Initially identified as missing validation for null values in required fields, but upon reviewing the C++ implementation, this is intentional behavior.

**C++ Reference:**
The C++ code in `dbxParser.cpp:224` explicitly documents this:
```cpp
// Parse bot region (required, can be "~")
```

The C++ test (`Test3DBloxParser.cpp:111`) expects `nullptr` for connections with `bot: ~`:
```cpp
EXPECT_EQ(connection->getBottomRegion(), nullptr);
```

**Conclusion:**
Required fields CAN have null values in the 3dblox format. The key exists in the YAML (so it's present), but its value can be null to indicate no connection. This is intentional design, not a bug.

---

## Limitation: Unimplemented Fields

**Status:** ℹ️ KNOWN LIMITATION (Not critical)

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
- Data loss during parsing (minor, as this field is not used in tests)
- No warning to users that data is being ignored
- Feature may need implementation if `cad_layer` becomes important

---

## Test Results

All parsers tested successfully after fix:
- ✅ `.3dbv` parser: Parses correctly, preserves header values
- ✅ `.3dbx` parser: Parses correctly, preserves None values in connections
- ✅ `.bmap` parser: Parses correctly

**Verification command:**
```python
from py3dblox import parser

dbx_data = parser.parse_dbx('example.3dbx')
# Before fix: dbx_data.connections['soc_to_virtual'].bot == "None" (str)
# After fix:  dbx_data.connections['soc_to_virtual'].bot is None (NoneType)
```

---

## Conclusion

**Critical bugs fixed:** 1
- ✅ Bug #1: None/null values converted to string "None"

**Non-bugs clarified:** 2
- Issue #2: Wildcard limitation is consistent with C++ implementation
- Issue #3: Null values are intentionally allowed per specification

The Python 3dblox parser is now consistent with the C++ reference implementation.
