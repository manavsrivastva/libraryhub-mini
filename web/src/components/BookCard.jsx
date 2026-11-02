
import {
  Card,
  CardContent,
  Typography,
  Button,
  Stack,
} from "@mui/material";

import { useNavigate } from "react-router-dom";

import AvailabilityBadge from "./AvailabilityBadge";
import { useBasket } from "../context/BasketContext";

function BookCard({ book }) {
  const navigate = useNavigate();
  const { basket, dispatch } = useBasket();

  const alreadyAdded = basket.items.some(
    (item) => item.isbn === book.isbn
  );

  function handleAddToBasket() {
    dispatch({
      type: "ADD",
      payload: book,
    });
  }

  return (
    <Card
      elevation={2}
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        borderRadius: 2,
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Typography variant="h6" gutterBottom>
          {book.title}
        </Typography>

        <Typography color="text.secondary" variant="body2">
          By {book.authors.join(", ")}
        </Typography>

        <Typography variant="body2" sx={{ mt: 1 }}>
          Category: {book.category}
        </Typography>

        <Typography variant="body2">
          Type: {book.item_type}
        </Typography>

        <Typography variant="body2">
          ISBN: {book.isbn}
        </Typography>

        <Typography variant="body2" sx={{ mt: 1 }}>
          Total copies: {book.total}
        </Typography>

        <Stack direction="row" sx={{ mt: 2 }}>
          <AvailabilityBadge available={book.available} />
        </Stack>
      </CardContent>

      <Stack spacing={1} sx={{ p: 2, pt: 0 }}>
        <Button
          variant="contained"
          disabled={alreadyAdded}
          onClick={handleAddToBasket}
        >
          {alreadyAdded ? "Added to Basket" : "Add to Basket"}
        </Button>

        <Button
          variant="outlined"
          onClick={() => navigate(`/books/${book.isbn}`)}
        >
          View Details
        </Button>
      </Stack>
    </Card>
  );
}

export default BookCard;
