
import { useState, useEffect } from "react";

import {
  Box,
  Typography,
  TextField,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  CircularProgress,
  Alert,
  Button,
} from "@mui/material";

import BookList from "../components/BookList";
import { getBooks } from "../services/api";

function Catalogue() {
  const [books, setBooks] = useState([]);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("title");
  const [category, setCategory] = useState("All");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retryCount, setRetryCount] = useState(0);

  // Fetch books whenever search, sort or retry changes
  useEffect(() => {
    const controller = new AbortController();

    const timer = setTimeout(async () => {
      try {
        setLoading(true);
        setError("");

        const data = await getBooks({
          q: search,
          sort: sort,
          signal: controller.signal,
        });

        setBooks(data);
      } catch (err) {
        if (err.name !== "AbortError") {
          setError(err.message || "Unable to load books.");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }, 300);

    // Cleanup: cancel timer and outdated request
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [search, sort, retryCount]);

  // Get unique categories from the fetched books
  const categories = [
    "All",
    ...new Set(books.map((book) => book.category)),
  ];

  // Apply category filter
  const filteredBooks =
    category === "All"
      ? books
      : books.filter((book) => book.category === category);

  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Book Catalogue
      </Typography>

      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Explore books and other resources available in LibraryHub.
      </Typography>

      {/* Search and filters */}
      <Box
        sx={{
          display: "flex",
          gap: 2,
          mb: 4,
          flexWrap: "wrap",
        }}
      >
        <TextField
          label="Search books"
          placeholder="Enter title, author or keyword..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          sx={{ flex: 2, minWidth: 220 }}
        />

        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Category</InputLabel>
          <Select
            value={category}
            label="Category"
            onChange={(e) => setCategory(e.target.value)}
          >
            {categories.map((item) => (
              <MenuItem key={item} value={item}>
                {item}
              </MenuItem>
            ))}
          </Select>
        </FormControl>

        <FormControl sx={{ minWidth: 150 }}>
          <InputLabel>Sort By</InputLabel>
          <Select
  value={sort}
  label="Sort By"
  onChange={(e) => setSort(e.target.value)}
>
  <MenuItem value="title">Title</MenuItem>
  <MenuItem value="author">Author</MenuItem>
  <MenuItem value="category">Category</MenuItem>
</Select>
        </FormControl>
      </Box>

      {/* Loading state */}
      {loading && (
        <Box sx={{ textAlign: "center", py: 5 }}>
          <CircularProgress />
          <Typography sx={{ mt: 2 }}>
            Loading books...
          </Typography>
        </Box>
      )}

      {/* Error state */}
      {!loading && error && (
        <Alert
          severity="error"
          action={
            <Button
              color="inherit"
              size="small"
              onClick={() => setRetryCount((count) => count + 1)}
            >
              Retry
            </Button>
          }
        >
          {error}
        </Alert>
      )}

      {/* Results */}
      {!loading && !error && (
        <>
          <Typography sx={{ mb: 2 }} color="text.secondary">
            Showing {filteredBooks.length} books
          </Typography>

          <BookList books={filteredBooks} />
        </>
      )}
    </Box>
  );
}

export default Catalogue;
