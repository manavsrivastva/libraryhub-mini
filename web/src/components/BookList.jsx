
import { Grid, Typography } from "@mui/material";
import BookCard from "./BookCard";

function BookList({ books }) {
  if (!books || books.length === 0) {
    return (
      <Typography align="center" sx={{ mt: 5 }}>
        No books found.
      </Typography>
    );
  }

  return (
    <Grid container spacing={3}>
      {books.map((book) => (
        <Grid key={book.isbn} size={{ xs: 12, sm: 6, md: 4 }}>
          <BookCard book={book} />
        </Grid>
      ))}
    </Grid>
  );
}

export default BookList;

