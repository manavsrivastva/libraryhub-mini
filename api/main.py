from fastapi.responses import JSONResponse

import os
from datetime import date
from typing import Literal

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from errors import (
    LibraryError,
    InvalidISBNError,
    ItemNotFoundError,
    MemberNotFoundError,
    LoanNotFoundError,
    ItemNotBorrowableError,
    BorrowLimitExceededError,
    UnpaidFinesError,
    DuplicateLoanError,
    DuplicateISBNError,
    ItemNotAvailableError,
    RenewalNotAllowedError,
)
from items import ITEM_TYPES
from library import Library
from storage import Database


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.environ.get(
    "LIBRARY_DB",
    os.path.join(BASE_DIR, "library.db")
)

FRONTEND_ORIGIN = os.environ.get(
    "FRONTEND_ORIGIN",
    "http://localhost:5173"
)


app = FastAPI(title="LibraryHub Mini API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# Database connection
# --------------------------------------------------

async def get_library():
    db = Database(DB_PATH)
    library = Library(db)

    try:
        yield library
    finally:
        db.close()


# --------------------------------------------------
# Date configuration
# --------------------------------------------------

def get_today():
    raw = os.environ.get("TODAY")

    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            raise ValueError(
                "TODAY must use the format YYYY-MM-DD."
            )

    return date.today()


# --------------------------------------------------
# Error handling
# --------------------------------------------------

ERROR_STATUS = {
    InvalidISBNError: 422,
    ItemNotFoundError: 404,
    MemberNotFoundError: 404,
    LoanNotFoundError: 404,
    ItemNotBorrowableError: 409,
    BorrowLimitExceededError: 409,
    UnpaidFinesError: 409,
    DuplicateLoanError: 409,
    DuplicateISBNError: 409,
    ItemNotAvailableError: 409,
    RenewalNotAllowedError: 409,
}


@app.exception_handler(LibraryError)
async def library_error_handler(request, exc):
    status_code = ERROR_STATUS.get(type(exc), 400)

    return JSONResponse(
        status_code=status_code,
        content={
            "error": exc.label,
            "message": str(exc),
        },
    )

# --------------------------------------------------
# Request models
# --------------------------------------------------

class BorrowRequest(BaseModel):
    member_id: str
    isbn: str

class ReservationRequest(BaseModel):
    member_id: str
    isbn: str


class AddBookRequest(BaseModel):
    isbn: str
    title: str = Field(min_length=1)
    authors: list[str]
    category: str
    parent_category: str | None = None
    item_type: Literal["Book", "Magazine", "Reference"] = "Book"
    pages: int = Field(ge=0)
    price: int = Field(ge=0)
    total_copies: int = Field(ge=1)


# --------------------------------------------------
# Response helper
# --------------------------------------------------

def book_response(item, library):
    return {
        "isbn": item.isbn,
        "title": item.title,
        "authors": item.authors,
        "category": item.category,
        "item_type": item.type_name,
        "available": library.free_copies(item.isbn),
        "total": item.total_copies,
        "pages": item.pages,
    }


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


# --------------------------------------------------
# Catalogue endpoints
# --------------------------------------------------

@app.get("/books")
async def get_books(
    q: str = "",
    sort: str = "title",
    library: Library = Depends(get_library),
):
    items = library.item_repo.all()

    if q.strip():
        items = library.search(q)

    sort_functions = {
        "title": lambda item: item.title.casefold(),
        "author": lambda item: ", ".join(item.authors).casefold(),
        "category": lambda item: item.category.casefold(),
    }

    if sort not in sort_functions:
        sort = "title"

    items.sort(key=sort_functions[sort])

    return [
        book_response(item, library)
        for item in items
    ]


@app.get("/books/{isbn}")
async def get_book(
    isbn: str,
    library: Library = Depends(get_library),
):
    item = library.get_item(isbn)
    return book_response(item, library)


@app.post("/books", status_code=201)
async def add_book(
    request: AddBookRequest,
    library: Library = Depends(get_library),
):
    item_class = ITEM_TYPES[request.item_type]

    item = item_class(
        request.isbn,
        request.title,
        request.authors,
        request.category,
        request.parent_category,
        request.pages,
        request.price,
        request.total_copies,
    )

    library.add_item(item)

    return book_response(item, library)


# --------------------------------------------------
# Borrow and return endpoints
# --------------------------------------------------

@app.post("/reservations", status_code=201)
async def reserve_book(
    request: ReservationRequest,
    library: Library = Depends(get_library),
):
    position = library.reserve(
        request.member_id,
        request.isbn,
    )

    return {
        "message": "Successfully joined the waiting list.",
        "position": position,
    }

@app.post("/loans", status_code=201)
async def borrow_book(
    request: BorrowRequest,
    library: Library = Depends(get_library),
):
    loan = library.borrow(
        request.member_id,
        request.isbn,
        get_today(),
    )

    return {
        "loan_id": loan.loan_id,
        "due_date": loan.due_date.isoformat(),
    }


@app.post("/loans/{loan_id}/return")
async def return_book(
    loan_id: str,
    library: Library = Depends(get_library),
):
    result = library.return_item(
        loan_id,
        get_today(),
    )

    return {
        "loan_id": result.loan.loan_id,
        "days_late": result.days_late,
        "fine": result.fine,
        "next_in_waiting_list": (
            result.next_member.name
            if result.next_member else None
        ),
    }


# --------------------------------------------------
# Member loans endpoint
# --------------------------------------------------

@app.get("/members/{member_id}/loans")
async def get_member_loans(
    member_id: str,
    library: Library = Depends(get_library),
):
    view = library.member_loans(member_id, get_today())

    member = view["member"]

    active_loans = []

    for loan, item, days_late in view["active"]:
        active_loans.append({
            "loan_id": loan.loan_id,
            "title": item.title,
            "due_date": loan.due_date.isoformat(),
            "days_overdue": days_late,
        })

    return {
        "member": member.name,
        "membership_type": member.membership_type,
        "max_items": member.max_items(),
        "unpaid_fines": view["unpaid"],
        "active": active_loans,
    }


@app.get("/members/{member_id}/reservations/{isbn}")
async def get_reservation_status(
    member_id: str,
    isbn: str,
    library: Library = Depends(get_library),
):
    library.get_member(member_id)
    library.get_item(isbn)

    held_seq = library.reservation_repo.held_seq(isbn, member_id)

    if held_seq is not None:
        return {
            "status": "held",
            "position": held_seq,
        }

    if library.reservation_repo.is_queued(isbn, member_id):
        waiting_ids = library.reservation_repo.waiting_ids(isbn)
        position = waiting_ids.index(member_id) + 1

        return {
            "status": "waiting",
            "position": position,
        }

    return {
        "status": "none",
        "position": None,
    }