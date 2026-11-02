"""Run the test-suite WITHOUT installing anything.

    python run_tests.py

If the real pytest is installed, this simply calls it. If not, a tiny built-in
stand-in (standard library only) runs the same tests, supporting what they use:
fixtures, @pytest.mark.parametrize, pytest.raises(match=...), monkeypatch, capsys.
"""
import contextlib
import importlib
import inspect
import io
import os
import re
import sys
import traceback
import types

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path[:0] = [ROOT, os.path.join(ROOT, "tests")]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")   # so the rupee sign prints on Windows


def real_pytest_available():
    try:
        import pytest  # noqa: F401
        return hasattr(sys.modules["pytest"], "main")
    except ImportError:
        return False


if real_pytest_available():
    import pytest
    sys.exit(pytest.main(["-v"]))

# ---------------------------------------------------------------- stand-in for pytest
stub = types.ModuleType("pytest")


class _Mark:
    def parametrize(self, names, values):
        names = [n.strip() for n in names.split(",")]

        def deco(func):
            # stacked decorators add one more parameter set each (like real pytest)
            func._param_sets = getattr(func, "_param_sets", []) + [(names, list(values))]
            return func
        return deco


class _Raises:
    def __init__(self, exc, match=None):
        self.exc, self.match, self.value = exc, match, None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            raise AssertionError(f"DID NOT RAISE {self.exc.__name__}")
        if not issubclass(exc_type, self.exc):
            return False
        if self.match and not re.search(self.match, str(exc)):
            raise AssertionError(f"message {str(exc)!r} does not match {self.match!r}")
        self.value = exc
        return True


def _fixture(func=None, **kwargs):
    def mark(f):
        f._is_fixture = True
        return f
    return mark(func) if func else mark


stub.mark, stub.raises, stub.fixture = _Mark(), _Raises, _fixture
sys.modules["pytest"] = stub


class MonkeyPatch:
    def __init__(self):
        self._undo = []

    def setattr(self, obj, name, value):
        self._undo.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def undo(self):
        for obj, name, old in reversed(self._undo):
            setattr(obj, name, old)


class CapSys:
    def __init__(self):
        self.buffer = io.StringIO()
        self._cm = contextlib.redirect_stdout(self.buffer)
        self._cm.__enter__()

    def readouterr(self):
        return types.SimpleNamespace(out=self.buffer.getvalue(), err="")

    def close(self):
        self._cm.__exit__(None, None, None)


def run_all():
    conftest = importlib.import_module("conftest")
    fixtures = {n: f for n, f in inspect.getmembers(conftest, inspect.isfunction)
                if getattr(f, "_is_fixture", False)}
    test_dir = os.path.join(ROOT, "tests")
    modules = sorted(f[:-3] for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py"))
    passed, failed = 0, []
    for modname in modules:
        module = importlib.import_module(modname)
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_"):
                continue
            cases = [{}]
            for names, rows in getattr(func, "_param_sets", []):
                cases = [dict(done, **dict(zip(names, row if len(names) > 1 else (row,))))
                         for done in cases for row in rows]
            for case in cases:
                shown = [getattr(v, "__name__", v) for v in case.values()]
                label = name + (f"[{', '.join(map(str, shown))}]" if case else "")
                monkeypatch, capsys = MonkeyPatch(), CapSys()
                try:
                    kwargs = {}
                    for param in inspect.signature(func).parameters:
                        if param in case:
                            kwargs[param] = case[param]
                        elif param == "monkeypatch":
                            kwargs[param] = monkeypatch
                        elif param == "capsys":
                            kwargs[param] = capsys
                        else:
                            kwargs[param] = fixtures[param]()
                    func(**kwargs)
                    capsys.close()
                    passed += 1
                    print(f"PASSED  {modname}::{label}")
                except BaseException:
                    capsys.close()
                    failed.append(label)
                    print(f"FAILED  {modname}::{label}")
                    traceback.print_exc()
                finally:
                    monkeypatch.undo()
    print(f"\n{passed} passed, {len(failed)} failed")
    return 1 if failed else 0


sys.exit(run_all())
