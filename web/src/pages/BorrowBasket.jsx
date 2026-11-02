
import { useState } from "react";
import {
  Box,
  Typography,
  Paper,
  Button,
  Stack,
  Alert,
  CircularProgress,
} from "@mui/material";

import { useNavigate } from "react-router-dom";
import { useBasket } from "../context/BasketContext";
import { useMember } from "../context/MemberContext";
import { borrowBook } from "../services/api";

function BorrowBasket() {
  const { basket, dispatch } = useBasket();
  const { selectedMemberId } = useMember();

  const navigate = useNavigate();
  const books = basket.items;

  const [checkingOut, setCheckingOut] = useState(false);
  const [checkoutMessage, setCheckoutMessage] = useState("");
  const [checkoutErrors, setCheckoutErrors] = useState([]);

  function removeBook(isbn) {
    dispatch({
      type: "REMOVE",
      payload: isbn,
    });
  }

  function clearBasket() {
    dispatch({ type: "CLEAR" });
    setCheckoutMessage("");
    setCheckoutErrors([]);
  }

  async function handleCheckout() {
    setCheckingOut(true);
    setCheckoutMessage("");
    setCheckoutErrors([]);

    const successfulBooks = [];
    const failedBooks = [];

    // Borrow each book for the currently selected member.
    for (const book of books) {
      try {
        const result = await borrowBook(
          selectedMemberId,
          book.isbn
        );

        successfulBooks.push({
          title: book.title,
          loanId: result.loan_id,
          dueDate: result.due_date,
        });

        // Remove successfully borrowed books.
        dispatch({
          type: "REMOVE",
          payload: book.isbn,
        });
      } catch (err) {
        failedBooks.push({
          title: book.title,
          message: err.message,
        });
      }
    }

    if (successfulBooks.length > 0) {
      setCheckoutMessage(
        `Successfully borrowed ${successfulBooks.length} book(s): ` +
        successfulBooks.map((book) => book.title).join(", ")
      );
    }

    setCheckoutErrors(failedBooks);
    setCheckingOut(false);
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Borrow Basket
      </Typography>

      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Review the books you want to borrow.
      </Typography>

      <Alert severity="info" sx={{ mb: 2 }}>
        Borrowing as member: {selectedMemberId}
      </Alert>

      {checkoutMessage && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {checkoutMessage}
          {checkoutErrors.length === 0 && (
            <Button
              size="small"
              onClick={() => navigate("/me")}
              sx={{ ml: 1 }}
            >
              View My Loans
            </Button>
          )}
        </Alert>
      )}

      {checkoutErrors.map((error, index) => (
        <Alert
          severity="error"
          key={`${error.title}-${index}`}
          sx={{ mb: 2 }}
        >
          <strong>{error.title}:</strong> {error.message}
        </Alert>
      ))}

      {books.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: "center" }}>
          <Alert severity="info">
            Your basket is currently empty.
          </Alert>

          <Button
            variant="contained"
            sx={{ mt: 3 }}
            onClick={() => navigate("/")}
          >
            Explore Catalogue
          </Button>
        </Paper>
      ) : (
        <>
          <Stack spacing={2}>
            {books.map((book) => (
              <Paper
                key={book.isbn}
                elevation={2}
                sx={{ p: 3, borderRadius: 2 }}
              >
                <Typography variant="h6" fontWeight="bold">
                  {book.title}
                </Typography>

                <Typography color="text.secondary">
                  By {book.authors.join(", ")}
                </Typography>

                <Typography variant="body2" sx={{ mt: 1 }}>
                  ISBN: {book.isbn}
                </Typography>

                <Typography variant="body2">
                  Category: {book.category}
                </Typography>

                <Button
                  color="error"
                  variant="outlined"
                  size="small"
                  sx={{ mt: 2 }}
                  disabled={checkingOut}
                  onClick={() => removeBook(book.isbn)}
                >
                  Remove
                </Button>
              </Paper>
            ))}
          </Stack>

          <Box sx={{ mt: 3 }}>
            <Typography fontWeight="bold" sx={{ mb: 2 }}>
              Total selected books: {books.length}
            </Typography>

            <Stack direction="row" spacing={2} flexWrap="wrap">
              <Button
                variant="contained"
                onClick={() => navigate("/")}
                disabled={checkingOut}
              >
                Continue Browsing
              </Button>

              <Button
                variant="outlined"
                color="error"
                onClick={clearBasket}
                disabled={checkingOut}
              >
                Clear Basket
              </Button>

              <Button
                variant="contained"
                color="success"
                onClick={handleCheckout}
                disabled={checkingOut || books.length === 0}
              >
                {checkingOut ? (
                  <>
                    <CircularProgress
                      size={18}
                      color="inherit"
                      sx={{ mr: 1 }}
                    />
                    Processing...
                  </>
                ) : (
                  "Checkout"
                )}
              </Button>
            </Stack>
          </Box>
        </>
      )}
    </Box>
  );
}

export default BorrowBasket;
