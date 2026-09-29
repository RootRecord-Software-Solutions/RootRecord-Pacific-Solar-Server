"""Minimal stdlib pytest-alike: discovers test_*.py files, runs top-level
functions named test_*, reports pass/fail without needing pytest installed."""
import importlib.util, sys, traceback, pathlib, os, logging

# Scheduler smoke tests intentionally exercise exception paths. Suppress the\n# scheduler logger here so expected simulated failures do not drown out the\n# actual PASS/FAIL result; real test failures still produce tracebacks below.\nlogging.disable(logging.CRITICAL)

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

def discover(base):
    return sorted(pathlib.Path(base).rglob("test_*.py"))

def run_module(path):
    modname = path.stem + "_" + str(abs(hash(str(path))))[:6]
    spec = importlib.util.spec_from_file_location(modname, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        return [("<module import>", "ERROR", traceback.format_exc())]
    results = []
    for name in dir(mod):
        if name.startswith("test_") and callable(getattr(mod, name)):
            fn = getattr(mod, name)
            try:
                fn()
                results.append((name, "PASS", None))
            except Exception:
                results.append((name, "FAIL", traceback.format_exc()))
    return results

def main(target_dirs):
    total = passed = failed = errored = 0
    failures = []
    for d in target_dirs:
        for f in discover(ROOT / d):
            rel = f.relative_to(ROOT)
            results = run_module(f)
            for name, status, tb in results:
                total += 1
                if status == "PASS":
                    passed += 1
                elif status == "ERROR":
                    errored += 1
                    failures.append((rel, name, tb))
                else:
                    failed += 1
                    failures.append((rel, name, tb))
            statuses = ", ".join(f"{n}:{s}" for n, s, _ in results) or "(no test_ functions found)"
            print(f"{rel}: {statuses}")
    print(f"\n=== {passed} passed, {failed} failed, {errored} errored, {total} total ===")
    if failures:
        print("\n--- FAILURE DETAILS ---")
        for rel, name, tb in failures:
            print(f"\n### {rel}::{name}")
            print(tb)
    return 0 if (failed == 0 and errored == 0) else 1

if __name__ == "__main__":
    dirs = sys.argv[1:] or ["tests"]
    sys.exit(main(dirs))
