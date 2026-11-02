
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

// Common function for making API requests
async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.message || "Something went wrong.");
  }

  return data;
}

// Fetch all books, with optional search and sorting
export function getBooks({ q = "", sort = "title", signal } = {}) {
  const params = new URLSearchParams({ q, sort });

  return request(`/books?${params.toString()}`, { signal });
}

// Fetch one book using its ISBN
export function getBookByISBN(isbn, signal) {
  return request(`/books/${encodeURIComponent(isbn)}`, { signal });
}

// Check whether the backend is running
export function checkAPIHealth() {
  return request("/health");
}


export function getMemberLoans(memberId, signal) {
  return request(
    `/members/${encodeURIComponent(memberId)}/loans`,
    { signal }
  );
}


export function borrowBook(memberId, isbn) {
  return request("/loans", {
    method: "POST",
    body: JSON.stringify({
      member_id: memberId,
      isbn: isbn,
    }),
  });
}


export function addBook(bookData) {
  return request("/books", {
    method: "POST",
    body: JSON.stringify(bookData),
  });
}

export function reserveBook(memberId, isbn) {
  return request("/reservations", {
    method: "POST",
    body: JSON.stringify({
      member_id: memberId,
      isbn: isbn,
    }),
  });
}

// Fetch a member's reservation status for a particular book
export function getReservationStatus(memberId, isbn, signal) {
  return request(
    `/members/${encodeURIComponent(memberId)}/reservations/${encodeURIComponent(isbn)}`,
    { signal }
  );
}