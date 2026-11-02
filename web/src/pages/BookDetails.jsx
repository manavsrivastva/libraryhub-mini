
import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useMember } from "../context/MemberContext";

import {
  Box,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Paper,
  Stack,
} from "@mui/material";

import {
  getBookByISBN,
  getReservationStatus,
  reserveBook,
  borrowBook,
} from "../services/api";

import AvailabilityBadge from "../components/AvailabilityBadge";

function BookDetails() {
  const { isbn } = useParams();
  const navigate = useNavigate();
  const { selectedMemberId } = useMember();

  const [book, setBook] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [reservation, setReservation] = useState(null);
  const [reservationLoading, setReservationLoading] = useState(true);

  const [actionLoading, setActionLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [actionError, setActionError] = useState("");

  // Fetch book details and selected member's reservation status
  useEffect(() => {
    const controller = new AbortController();

    async function fetchDetails() {
      try {
        setLoading(true);
        setReservationLoading(true);
        setError("");
        setActionError("");
        setSuccessMessage("");
        setBook(null);
        setReservation(null);

        const [bookData, reservationData] = await Promise.all([
          getBookByISBN(isbn, controller.signal),
          getReservationStatus(
            selectedMemberId,
            isbn,
            controller.signal
          ),
        ]);

        setBook(bookData);
        setReservation(reservationData);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Unable to load book details.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setReservationLoading(false);
        }
      }
    }

    fetchDetails();

    return () => controller.abort();
  }, [isbn, selectedMemberId]);

  // Refresh book and reservation information after an action
  async function refreshDetails() {
    const [bookData, reservationData] = await Promise.all([
      getBookByISBN(isbn),
      getReservationStatus(selectedMemberId, isbn),
    ]);

    setBook(bookData);
    setReservation(reservationData);
  }

  // Join waiting list
  async function handleReserve() {
    try {
      setActionLoading(true);
      setActionError("");
      setSuccessMessage("");

      const result = await reserveBook(selectedMemberId, isbn);

      await refreshDetails();

      setSuccessMessage(
        `${result.message} Your queue position is ${result.position}.`
      );
    } catch (err) {
      setActionError(err.message || "Unable to join the waiting list.");
    } finally {
      setActionLoading(false);
    }
  }

  // Borrow a copy held for this member
  async function handleBorrow() {
    try {
      setActionLoading(true);
      setActionError("");
      setSuccessMessage("");

      await borrowBook(selectedMemberId, isbn);

      await refreshDetails();

      setSuccessMessage("Book borrowed successfully.");
    } catch (err) {
      setActionError(err.message || "Unable to borrow this book.");
    } finally {
      setActionLoading(false);
    }
  }

  if (loading) {
    return (
      <Box sx={{ textAlign: "center", py: 6 }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>
          Loading book details...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Alert severity="error">{error}</Alert>
        <Button sx={{ mt: 2 }} onClick={() => navigate("/")}>
          Back to Catalogue
        </Button>
      </Box>
    );
  }

  if (!book) {
    return <Alert severity="warning">Book not found.</Alert>;
  }

  return (
    <Box>
      <Button onClick={() => navigate("/")}>
        ← Back to Catalogue
      </Button>

      <Paper elevation={2} sx={{ p: 4, mt: 3, borderRadius: 2 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          {book.title}
        </Typography>

        <Typography color="text.secondary" sx={{ mb: 3 }}>
          By {book.author || book.authors?.join(", ") || "Unknown"}
        </Typography>

        <Stack spacing={2}>
          <Typography>
            <strong>ISBN:</strong> {book.isbn}
          </Typography>

          <Typography>
            <strong>Category:</strong> {book.category}
          </Typography>

          <Typography>
            <strong>Type:</strong> {book.item_type}
          </Typography>

          <Typography>
            <strong>Total copies:</strong> {book.total}
          </Typography>

          <Typography>
            <strong>Pages:</strong> {book.pages || "Not available"}
          </Typography>

          <Box>
            <strong>Availability: </strong>
            <AvailabilityBadge available={book.available} />
          </Box>

          {reservationLoading ? (
            <Typography color="text.secondary">
              Checking reservation status...
            </Typography>
          ) : (
            <>
              {/* A copy is held specifically for this member */}
              {reservation?.status === "held" && (
                <Box>
                  <Alert severity="success" sx={{ mb: 2 }}>
                    A copy is being held for you. You have priority to borrow it.
                  </Alert>

                  <Button
                    variant="contained"
                    onClick={handleBorrow}
                    disabled={actionLoading}
                  >
                    {actionLoading ? "Processing..." : "Borrow Book"}
                  </Button>
                </Box>
              )}

              {/* Member is still waiting in the queue */}
              {reservation?.status === "waiting" && (
                <Alert severity="info">
                  You are on the waiting list. Your current queue position is{" "}
                  {reservation.position}.
                </Alert>
              )}

              {/* No reservation and no copies available */}
              {reservation?.status === "none" && book.available === 0 && (
                <Button
                  variant="contained"
                  onClick={handleReserve}
                  disabled={actionLoading}
                >
                  {actionLoading ? "Joining..." : "Join Waiting List"}
                </Button>
              )}

              {/* No reservation, but a copy is available */}
              {reservation?.status === "none" && book.available > 0 && (
                <Alert severity="success">
                  This book is available. You can add it to your borrow basket.
                </Alert>
              )}
            </>
          )}

          {successMessage && (
            <Alert severity="success">{successMessage}</Alert>
          )}

          {actionError && (
            <Alert severity="error">{actionError}</Alert>
          )}
        </Stack>
      </Paper>
    </Box>
  );
}

export default BookDetails;
