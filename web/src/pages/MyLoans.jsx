
import { useEffect, useState } from "react";

import {
  Box,
  Typography,
  Paper,
  Stack,
  CircularProgress,
  Alert,
  Chip,
} from "@mui/material";

import { getMemberLoans } from "../services/api";
import { useMember } from "../context/MemberContext";

function MyLoans() {
  // Get the currently selected member from Navbar
  const { selectedMemberId } = useMember();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function fetchLoans() {
      try {
        setLoading(true);
        setError("");
        setData(null);

        const result = await getMemberLoans(
          selectedMemberId,
          controller.signal
        );

        setData(result);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Unable to load your loans.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    fetchLoans();

    return () => controller.abort();
  }, [selectedMemberId]);

  if (loading) {
    return (
      <Box sx={{ textAlign: "center", py: 6 }}>
        <CircularProgress />
        <Typography sx={{ mt: 2 }}>
          Loading your loans...
        </Typography>
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  if (!data) {
    return <Alert severity="warning">No loan information found.</Alert>;
  }

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        My Loans
      </Typography>

      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Your borrowed books and membership information.
      </Typography>

      <Paper elevation={2} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" fontWeight="bold">
          {data.member}
        </Typography>

        <Stack
          direction="row"
          spacing={2}
          flexWrap="wrap"
          sx={{ mt: 2, gap: 1 }}
        >
          <Chip label={`Membership: ${data.membership_type}`} />
          <Chip label={`Maximum items: ${data.max_items}`} />
          <Chip
            label={`Unpaid fines: ₹${data.unpaid_fines}`}
            color={data.unpaid_fines > 0 ? "error" : "success"}
          />
        </Stack>
      </Paper>

      <Typography variant="h6" fontWeight="bold" sx={{ mb: 2 }}>
        Active Borrowings
      </Typography>

      {data.active.length === 0 ? (
        <Alert severity="info">
          You currently have no active loans.
        </Alert>
      ) : (
        <Stack spacing={2}>
          {data.active.map((loan) => (
            <Paper
              key={loan.loan_id}
              elevation={1}
              sx={{ p: 3, borderRadius: 2 }}
            >
              <Typography variant="h6">
                {loan.title}
              </Typography>

              <Typography color="text.secondary" sx={{ mt: 1 }}>
                Loan ID: {loan.loan_id}
              </Typography>

              <Typography color="text.secondary">
                Due date: {loan.due_date}
              </Typography>

              <Box sx={{ mt: 2 }}>
                {loan.days_overdue > 0 ? (
                  <Chip
                    label={`${loan.days_overdue} days overdue`}
                    color="error"
                  />
                ) : (
                  <Chip label="Not overdue" color="success" />
                )}
              </Box>
            </Paper>
          ))}
        </Stack>
      )}
    </Box>
  );
}

export default MyLoans;
