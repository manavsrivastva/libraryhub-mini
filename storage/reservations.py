"""The waiting list (R7). Lower `seq` = earlier in the queue. status: 'waiting' or 'held'."""


class ReservationRepository:
    def __init__(self, db):
        self.db = db

    def join(self, isbn, member_id):
        """Add to the END of the queue. Returns the 1-based position."""
        seq = self.db.one("SELECT COALESCE(MAX(seq), 0) + 1 FROM reservations")
        self.db.execute("INSERT INTO reservations (isbn, member_id, status, seq) VALUES (?, ?, 'waiting', ?)",
                        (isbn, member_id, seq))
        return self.waiting_count(isbn)

    def waiting_ids(self, isbn):
        return [r[0] for r in self.db.execute(
            "SELECT member_id FROM reservations WHERE isbn = ? AND status = 'waiting' ORDER BY seq", (isbn,))]

    def waiting_count(self, isbn):
        return self.db.one("SELECT COUNT(*) FROM reservations WHERE isbn = ? AND status = 'waiting'", (isbn,))

    def held_count(self, isbn):
        return self.db.one("SELECT COUNT(*) FROM reservations WHERE isbn = ? AND status = 'held'", (isbn,))

    def held_seq(self, isbn, member_id):
        """The queue position number of a copy being held for this member, or None."""
        return self.db.one("SELECT seq FROM reservations WHERE isbn = ? AND member_id = ? AND status = 'held'",
                           (isbn, member_id))

    def is_queued(self, isbn, member_id):
        return self.db.one("SELECT 1 FROM reservations WHERE isbn = ? AND member_id = ?",
                           (isbn, member_id)) is not None

    def hold_first(self, isbn):
        """First in the queue gets the returned copy held for them. Returns their member_id or None."""
        row = self.db.execute("SELECT member_id FROM reservations WHERE isbn = ? AND status = 'waiting' "
                              "ORDER BY seq LIMIT 1", (isbn,)).fetchone()
        if row is None:
            return None
        self.db.execute("UPDATE reservations SET status = 'held' WHERE isbn = ? AND member_id = ?", (isbn, row[0]))
        return row[0]

    def unhold(self, isbn, member_id):
        """Undo of hold_first: same seq, so the member is back in EXACTLY their old place."""
        self.db.execute("UPDATE reservations SET status = 'waiting' WHERE isbn = ? AND member_id = ?",
                        (isbn, member_id))

    def remove(self, isbn, member_id):
        self.db.execute("DELETE FROM reservations WHERE isbn = ? AND member_id = ?", (isbn, member_id))

    def restore_held(self, isbn, member_id, seq):
        self.db.execute("INSERT INTO reservations (isbn, member_id, status, seq) VALUES (?, ?, 'held', ?)",
                        (isbn, member_id, seq))
