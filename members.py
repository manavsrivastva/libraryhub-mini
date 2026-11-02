"""Members. Each membership type answers its own limit, loan period and fine rate,
so no other file ever needs `if member_type == ...`."""
from abc import ABC, abstractmethod


class Member(ABC):
    membership_type = "Member"

    def __init__(self, member_id, name, email):
        self.member_id = member_id
        self.name = name
        self.email = email

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not str(value).strip():
            raise ValueError("Name cannot be blank.")
        self._name = str(value).strip()

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, value):
        if "@" not in str(value):
            raise ValueError("Email must contain @.")
        self._email = str(value).strip()

    @abstractmethod
    def max_items(self): ...      # R3

    @abstractmethod
    def loan_days(self): ...      # also what a renewal adds (R6)

    @abstractmethod
    def fine_per_day(self): ...   # R5

    def describe(self):
        return f"{self.membership_type}: {self.max_items()} items, {self.loan_days()} days, ₹{self.fine_per_day()}/day"

    def __str__(self):
        return f"{self.name} ({self.member_id}, {self.membership_type})"

    def __repr__(self):
        return f"{type(self).__name__}(member_id={self.member_id!r}, name={self.name!r})"


class StudentMember(Member):
    membership_type = "Student"
    def max_items(self): return 3
    def loan_days(self): return 14
    def fine_per_day(self): return 2


class RegularMember(Member):
    membership_type = "Regular"
    def max_items(self): return 5
    def loan_days(self): return 21
    def fine_per_day(self): return 5


class PremiumMember(Member):
    membership_type = "Premium"
    def max_items(self): return 10
    def loan_days(self): return 30
    def fine_per_day(self): return 3


# Lookup table used when loading the CSV: replaces an if/elif chain on the type name.
MEMBER_TYPES = {cls.membership_type: cls for cls in (StudentMember, RegularMember, PremiumMember)}
