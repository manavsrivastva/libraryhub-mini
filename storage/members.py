"""Members."""
from members import MEMBER_TYPES


class MemberRepository:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _build(row):
        member_id, name, email, membership_type = row
        return MEMBER_TYPES[membership_type](member_id, name, email)   # lookup dict, no if-chain

    def get(self, member_id):
        row = self.db.execute("SELECT member_id, name, email, membership_type FROM members "
                              "WHERE member_id = ?", (member_id,)).fetchone()
        return self._build(row) if row else None

    def all(self):
        return [self._build(r) for r in self.db.execute(
            "SELECT member_id, name, email, membership_type FROM members ORDER BY rowid")]

    def count(self):
        return self.db.one("SELECT COUNT(*) FROM members")

    def add(self, member):
        self.db.execute("INSERT INTO members VALUES (?, ?, ?, ?)",
                        (member.member_id, member.name, member.email, member.membership_type))
