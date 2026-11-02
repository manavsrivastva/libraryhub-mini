"""Singly linked list of a member's loans, newest first."""


class Node:
    def __init__(self, loan):
        self.loan = loan
        self.next = None


class BorrowHistory:
    def __init__(self):
        self.head = None
        self._size = 0

    def insert_head(self, loan):
        """O(1): the new node points at the old head, then becomes the head."""
        node = Node(loan)
        node.next = self.head
        self.head = node
        self._size += 1

    def __iter__(self):
        current = self.head
        while current is not None:
            yield current.loan
            current = current.next

    def __len__(self):
        return self._size

    def __str__(self):
        return " -> ".join([loan.loan_id for loan in self] + ["None"])

    # ---- stretch tasks ---------------------------------------------------------
    def delete(self, loan_id):
        previous, current = None, self.head
        while current is not None:
            if current.loan.loan_id == loan_id:
                if previous is None:
                    self.head = current.next
                else:
                    previous.next = current.next
                self._size -= 1
                return True
            previous, current = current, current.next
        return False

    def reverse(self):
        previous, current = None, self.head
        while current is not None:
            current.next, previous, current = previous, current, current.next
        self.head = previous

    def kth_from_end(self, k):
        """Two pointers: `lead` starts k steps ahead, so when it falls off the end
        `trail` is k from the end. One pass, no length needed."""
        lead = self.head
        for _ in range(k):
            if lead is None:
                return None
            lead = lead.next
        trail = self.head
        while lead is not None:
            lead, trail = lead.next, trail.next
        return trail.loan if trail else None

    def second_from_end(self):
        return self.kth_from_end(2)
