"""3.8 THE INJECTION EXPERIMENT. A throwaway file: the ONLY place in the project that builds SQL
with an f-string, on purpose, to show the attack.   python injection_unsafe_demo.py"""
import sys

from build_db import build_db


def search_unsafe(conn, term):
    sql = f"SELECT isbn, title FROM items WHERE title LIKE '%{term}%'"      # DANGEROUS: user text becomes SQL
    return conn.execute(sql).fetchall()


def search_safe(conn, term):
    return conn.execute("SELECT isbn, title FROM items WHERE title LIKE ?",   # ? is data, never SQL
                        (f"%{term}%",)).fetchall()


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    conn = build_db()
    attack = "' OR '1'='1"
    print(f'search_unsafe("Python")  -> {len(search_unsafe(conn, "Python"))} row')
    print(f'search_unsafe("{attack}") -> {len(search_unsafe(conn, attack))} rows   (every item leaked)')
    print(f"   the database actually ran: SELECT isbn, title FROM items WHERE title LIKE '%{attack}%'")
    print(f'search_safe("{attack}")   -> {len(search_safe(conn, attack))} rows')
    print(f'search_safe("Python")    -> {len(search_safe(conn, "Python"))} row')
