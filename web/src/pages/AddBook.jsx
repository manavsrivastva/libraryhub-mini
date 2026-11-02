
import { useState } from "react";
import { addBook } from "../services/api";

import {
  Box,
  Typography,
  TextField,
  Button,
  MenuItem,
  Paper,
  Stack,
  Alert,
} from "@mui/material";

function AddBook() {
  const initialFormData = {
    isbn: "",
    title: "",
    author: "",
    category: "",
    parent_category: "",
    item_type: "Book",
    pages: "",
    price: "",
    total_copies: "1",
  };

  const [formData, setFormData] = useState(initialFormData);
  const [errors, setErrors] = useState({});

  const [successMessage, setSuccessMessage] = useState("");
  const [apiError, setApiError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  function handleChange(event) {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));

    setErrors((previous) => ({
      ...previous,
      [name]: "",
    }));

    setSuccessMessage("");
    setApiError("");
  }

  function validateForm() {
    const newErrors = {};

    if (!/^\d{13}$/.test(formData.isbn)) {
      newErrors.isbn = "ISBN must contain exactly 13 digits.";
    }

    if (!formData.title.trim()) {
      newErrors.title = "Title is required.";
    }

    if (!formData.author.trim()) {
      newErrors.author = "Author is required.";
    }

    if (!formData.category.trim()) {
      newErrors.category = "Category is required.";
    }

    if (
      formData.total_copies === "" ||
      !Number.isInteger(Number(formData.total_copies)) ||
      Number(formData.total_copies) < 1
    ) {
      newErrors.total_copies = "Enter at least 1 copy.";
    }

    if (
      formData.pages === "" ||
      !Number.isInteger(Number(formData.pages)) ||
      Number(formData.pages) < 0
    ) {
      newErrors.pages = "Pages must be zero or greater.";
    }

    if (
      formData.price === "" ||
      !Number.isFinite(Number(formData.price)) ||
      Number(formData.price) < 0
    ) {
      newErrors.price = "Price must be zero or greater.";
    }

    setErrors(newErrors);

    return Object.keys(newErrors).length === 0;
  }

  const isFormValid =
    /^\d{13}$/.test(formData.isbn) &&
    formData.title.trim() !== "" &&
    formData.author.trim() !== "" &&
    formData.category.trim() !== "" &&
    Number.isInteger(Number(formData.total_copies)) &&
    Number(formData.total_copies) >= 1 &&
    formData.pages !== "" &&
    Number.isInteger(Number(formData.pages)) &&
    Number(formData.pages) >= 0 &&
    formData.price !== "" &&
    Number.isFinite(Number(formData.price)) &&
    Number(formData.price) >= 0;

  async function handleSubmit(event) {
    event.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setSuccessMessage("");
    setApiError("");

    const bookData = {
      isbn: formData.isbn,
      title: formData.title.trim(),
      authors: [formData.author.trim()],
      category: formData.category.trim(),
      parent_category: formData.parent_category.trim() || null,
      item_type: formData.item_type,
      pages: Number(formData.pages),
      price: Number(formData.price),
      total_copies: Number(formData.total_copies),
    };

    try {
      await addBook(bookData);

      setSuccessMessage("Book added successfully!");

      setFormData(initialFormData);
      setErrors({});
    } catch (error) {
      setApiError(error.message || "Unable to add the book.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Paper
      elevation={2}
      sx={{
        p: { xs: 2, sm: 4 },
        maxWidth: 700,
        mx: "auto",
      }}
    >
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        Add a New Book
      </Typography>

      <Typography color="text.secondary" sx={{ mb: 3 }}>
        Enter the book details to add it to the library catalogue.
      </Typography>

      <Box component="form" onSubmit={handleSubmit}>
        <Stack spacing={2.5}>

          {successMessage && (
            <Alert severity="success">
              {successMessage}
            </Alert>
          )}

          {apiError && (
            <Alert severity="error">
              {apiError}
            </Alert>
          )}

          <TextField
            label="ISBN"
            name="isbn"
            value={formData.isbn}
            onChange={handleChange}
            error={Boolean(errors.isbn)}
            helperText={errors.isbn || "Enter exactly 13 digits."}
            required
            fullWidth
          />

          <TextField
            label="Book Title"
            name="title"
            value={formData.title}
            onChange={handleChange}
            error={Boolean(errors.title)}
            helperText={errors.title}
            required
            fullWidth
          />

          <TextField
            label="Author"
            name="author"
            value={formData.author}
            onChange={handleChange}
            error={Boolean(errors.author)}
            helperText={errors.author}
            required
            fullWidth
          />

          <TextField
            label="Category"
            name="category"
            value={formData.category}
            onChange={handleChange}
            error={Boolean(errors.category)}
            helperText={errors.category}
            required
            fullWidth
          />

          <TextField
            label="Parent Category (Optional)"
            name="parent_category"
            value={formData.parent_category}
            onChange={handleChange}
            fullWidth
          />

          <TextField
            select
            label="Item Type"
            name="item_type"
            value={formData.item_type}
            onChange={handleChange}
            fullWidth
          >
            <MenuItem value="Book">Book</MenuItem>
            <MenuItem value="Magazine">Magazine</MenuItem>
            <MenuItem value="Reference">Reference</MenuItem>
          </TextField>

          <TextField
            label="Number of Pages"
            name="pages"
            type="number"
            value={formData.pages}
            onChange={handleChange}
            error={Boolean(errors.pages)}
            helperText={errors.pages}
            required
            fullWidth
          />

          <TextField
            label="Price (₹)"
            name="price"
            type="number"
            value={formData.price}
            onChange={handleChange}
            error={Boolean(errors.price)}
            helperText={errors.price}
            required
            fullWidth
          />

          <TextField
            label="Total Copies"
            name="total_copies"
            type="number"
            value={formData.total_copies}
            onChange={handleChange}
            error={Boolean(errors.total_copies)}
            helperText={errors.total_copies}
            required
            fullWidth
          />

          <Button
            type="submit"
            variant="contained"
            size="large"
            disabled={!isFormValid || submitting}
          >
            {submitting ? "Adding Book..." : "Add Book"}
          </Button>

        </Stack>
      </Box>
    </Paper>
  );
}

export default AddBook;
