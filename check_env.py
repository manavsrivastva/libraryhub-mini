"""Checks what this computer allows. Run it first on a locked-down laptop:   python check_env.py"""
import os
import sqlite3
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def check(label, test):
    try:
        detail = test()
        print(f"OK    {label}" + (f" ({detail})" if detail else ""))
        return True
    except Exception as err:
        print(f"FAIL  {label}: {type(err).__name__}: {err}")
        return False


def sqlite_memory():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE t (x)")
    conn.execute("INSERT INTO t VALUES (1)")
    return "SQLite " + sqlite3.sqlite_version


def roundtrip(extension, folder):
    def run():
        path = os.path.join(folder, "envcheck" + extension)
        with open(path, "w", encoding="utf-8") as f:
            f.write("hello")
        with open(path, encoding="utf-8") as f:
            assert f.read() == "hello"
        os.remove(path)
    return run


def sqlite_file(folder):
    def run():
        path = os.path.join(folder, "envcheck.db")
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE t (x)")
        conn.execute("INSERT INTO t VALUES (1)")
        conn.commit()
        conn.close()
        os.remove(path)
    return run


if __name__ == "__main__":
    print("Python", sys.version.split()[0], "-", sys.executable, "\n")
    results = [check("SQLite works in memory", sqlite_memory)]
    for ext in (".py", ".sql", ".txt", ".csv"):
        results.append(check(f"write + read a {ext} file in the project folder", roundtrip(ext, HERE)))
    results.append(check("create + use a .db database file in the project folder", sqlite_file(HERE)))
    results.append(check("create + use a .db database file in the temp folder", sqlite_file(tempfile.gettempdir())))
    print("\nIf the .db line in the project folder FAILS, set another location before running main.py:")
    print('  $env:LIBRARY_DB = "C:\\Users\\<you>\\Documents\\library.db"')
    print("The program never needs to READ a .sql file, so a failing .sql line does not stop the project.")
