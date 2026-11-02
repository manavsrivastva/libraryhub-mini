"""The audit trail (one row per successful borrow, return, renew or undo)."""


class AuditRepository:
    def __init__(self, db):
        self.db = db

    def add(self, logged_at, action, member_id, isbn):
        self.db.execute("INSERT INTO audit_log (logged_at, action, member_id, isbn) VALUES (?, ?, ?, ?)",
                        (logged_at, action, member_id, isbn))

    def all(self):
        return [{"time": t, "action": a, "member": m, "item": i} for t, a, m, i in self.db.execute(
            "SELECT logged_at, action, member_id, isbn FROM audit_log ORDER BY audit_id")]

    def count(self):
        return self.db.one("SELECT COUNT(*) FROM audit_log")
