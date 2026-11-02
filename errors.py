"""Exception hierarchy. LibraryError is the parent of everything the engine raises on purpose.

`code` is what the console prints inside ERROR [...]: a rule number (R1..R9)
for rule violations, otherwise the class name.
"""


class LibraryError(Exception):
    code = None  # rule number such as "R3"; None means "use the class name"

    def __init__(self, message, code=None):
        super().__init__(message)
        if code is not None:
            self.code = code  # per-instance override (RenewalNotAllowedError uses R2 or R6)

    @property
    def label(self):
        return self.code or type(self).__name__


class InvalidISBNError(LibraryError): pass
class ItemNotFoundError(LibraryError): pass
class MemberNotFoundError(LibraryError): pass
class LoanNotFoundError(ItemNotFoundError): pass          # unknown or already-returned loan ID
class ItemNotBorrowableError(LibraryError): code = "R1"
class BorrowLimitExceededError(LibraryError): code = "R3"
class UnpaidFinesError(LibraryError): code = "R4"
class DuplicateLoanError(LibraryError): code = "R8"
class DuplicateISBNError(LibraryError): code = "R9"
class ItemNotAvailableError(LibraryError): pass           # R7: caller may offer the waiting list
class RenewalNotAllowedError(LibraryError): code = "R6"   # R2 passed explicitly for magazines
