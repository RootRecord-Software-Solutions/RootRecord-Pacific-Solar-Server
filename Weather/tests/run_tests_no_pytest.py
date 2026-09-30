# ==============================================================================
# FILE: Weather/tests/run_tests_no_pytest.py
# What this file is: first-party Pacific source. Read the SECTION banner above
# the function or list you need. Every code line ends with an # info: note.
# How to edit: change the code, then change the # info: note on that same line
# so it still says what the line does. Add a new function with the SECTION
# banner from 5 - RootRecord-Library/prompts/How-To-Read-And-Edit-Code.md.
# Kind: python
# ==============================================================================
"""Minimal stdlib pytest-alike: discovers test_*.py files, runs top-level
functions named test_*, reports pass/fail without needing pytest installed."""
import importlib.util, sys, traceback, pathlib, os, logging  # info: import importlib . util , sys , traceback

# Scheduler smoke tests intentionally exercise exception paths. Suppress the\n# scheduler logger here so expected simulated failures do not drown out the\n# actual PASS/FAIL result; real test failures still produce tracebacks below.\nlogging.disable(logging.CRITICAL)

ROOT = pathlib.Path(__file__).resolve().parent.parent  # info: set ROOT
sys.path.insert(0, str(ROOT))  # info: sys . path . insert ( 0 ,

# ====================================================
# SECTION: function discover
# What it does: discover.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def discover(base):  # info: def discover
    return sorted(pathlib.Path(base).rglob("test_*.py"))  # info: return sorted ( pathlib . Path ( base

# ====================================================
# SECTION: function run_module
# What it does: run module.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def run_module(path):  # info: def run_module
    modname = path.stem + "_" + str(abs(hash(str(path))))[:6]  # info: set modname
    spec = importlib.util.spec_from_file_location(modname, path)  # info: set spec
    mod = importlib.util.module_from_spec(spec)  # info: set mod
    try:  # info: try :
        spec.loader.exec_module(mod)  # info: spec . loader . exec_module ( mod )
    except Exception as e:  # info: except Exception as e :
        return [("<module import>", "ERROR", traceback.format_exc())]  # info: return [ ( "<module import>" , "ERROR" , traceback
    results = []  # info: set results
    for name in dir(mod):  # info: for name in dir ( mod ) :
        if name.startswith("test_") and callable(getattr(mod, name)):  # info: if name . startswith ( "test_" ) and
            fn = getattr(mod, name)  # info: set fn
            try:  # info: try :
                fn()  # info: call fn
                results.append((name, "PASS", None))  # info: results . append ( ( name , "PASS"
            except Exception:  # info: except Exception :
                results.append((name, "FAIL", traceback.format_exc()))  # info: results . append ( ( name , "FAIL"
    return results  # info: return results

# ====================================================
# SECTION: function main
# What it does: main.
# Edit this block only. Leave this banner in place and update the What-it-does line if the behavior changes.
# ====================================================
def main(target_dirs):  # info: def main
    total = passed = failed = errored = 0  # info: set total
    failures = []  # info: set failures
    for d in target_dirs:  # info: for d in target_dirs :
        for f in discover(ROOT / d):  # info: for f in discover ( ROOT / d
            rel = f.relative_to(ROOT)  # info: set rel
            results = run_module(f)  # info: set results
            for name, status, tb in results:  # info: for name , status , tb in results
                total += 1  # info: set total
                if status == "PASS":  # info: if status == "PASS" :
                    passed += 1  # info: set passed
                elif status == "ERROR":  # info: elif status == "ERROR" :
                    errored += 1  # info: set errored
                    failures.append((rel, name, tb))  # info: failures . append ( ( rel , name
                else:  # info: else :
                    failed += 1  # info: set failed
                    failures.append((rel, name, tb))  # info: failures . append ( ( rel , name
            statuses = ", ".join(f"{n}:{s}" for n, s, _ in results) or "(no test_ functions found)"  # info: set statuses
            print(f"{rel}: {statuses}")  # info: call print
    print(f"\n=== {passed} passed, {failed} failed, {errored} errored, {total} total ===")  # info: call print
    if failures:  # info: if failures :
        print("\n--- FAILURE DETAILS ---")  # info: call print
        for rel, name, tb in failures:  # info: for rel , name , tb in failures
            print(f"\n### {rel}::{name}")
            print(tb)  # info: call print
    return 0 if (failed == 0 and errored == 0) else 1  # info: return 0 if ( failed == 0 and

if __name__ == "__main__":  # info: if __name__ == "__main__" :
    dirs = sys.argv[1:] or ["tests"]  # info: set dirs
    sys.exit(main(dirs))  # info: sys . exit ( main ( dirs )
