
import { Box, Container } from "@mui/material";
import Navbar from "./Navbar";

function Layout({ children }) {
  return (
    <Box>
      <Navbar />

      <Container maxWidth="lg" sx={{ py: 4 }}>
        {children}
      </Container>
    </Box>
  );
}

export default Layout;
