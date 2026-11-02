
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { CssBaseline, Typography, Box } from "@mui/material";

import AddBook from "./pages/AddBook";
import BorrowBasket from "./pages/BorrowBasket";
import MyLoans from "./pages/MyLoans";
import Layout from "./components/Layout";
import Catalogue from "./pages/Catalogue";
import BookDetails from "./pages/BookDetails";
import { BasketProvider } from "./context/BasketContext";
import { MemberProvider } from "./context/MemberContext";

// Temporary page for screens we will build next
function PlaceholderPage({ title, description }) {
  return (
    <Box>
      <Typography variant="h4" fontWeight="bold" gutterBottom>
        {title}
      </Typography>
      <Typography color="text.secondary">
        {description}
      </Typography>
    </Box>
  );
}



function NotFound() {
  return (
    <PlaceholderPage
      title="404 - Page Not Found"
      description="The page you are looking for does not exist."
    />
  );
}

function App() {
  return (
    <BrowserRouter>
    <MemberProvider>
      <BasketProvider>
      <CssBaseline />

      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <Catalogue />
            </Layout>
          }
        />

        <Route
          path="/books/:isbn"
          element={
            <Layout>
              <BookDetails />
            </Layout>
          }
        />

        <Route
  path="/me"
  element={
    <Layout>
      <MyLoans />
    </Layout>
  }
/>

        <Route
  path="/basket"
  element={
    <Layout>
      <BorrowBasket />
    </Layout>
  }
/>

        <Route
  path="/admin/add"
  element={
    <Layout>
      <AddBook />
    </Layout>
  }
/>

        <Route
          path="*"
          element={
            <Layout>
              <NotFound />
            </Layout>
          }
        />
      </Routes>
      </BasketProvider>
      </MemberProvider>
    </BrowserRouter>
  );
}

export default App;
