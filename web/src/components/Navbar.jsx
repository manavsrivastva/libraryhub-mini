
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  FormControl,
  Select,
  MenuItem,
} from "@mui/material";

import { Link } from "react-router-dom";
import { useMember } from "../context/MemberContext";

const members = [
  { id: "M001", name: "Asha Raman", type: "Student" },
  { id: "M002", name: "Rahul Mehta", type: "Regular" },
  { id: "M003", name: "Sneha Iyer", type: "Premium" },
  { id: "M004", name: "Karthik N", type: "Student" },
  { id: "M005", name: "Divya Rao", type: "Regular" },
];

function Navbar() {
  const { selectedMemberId, setSelectedMemberId } = useMember();

  function handleMemberChange(event) {
    setSelectedMemberId(event.target.value);
  }

  return (
    <AppBar position="static" color="primary">
      <Toolbar sx={{ flexWrap: "wrap", gap: 1 }}>

        <Typography
          variant="h6"
          component={Link}
          to="/"
          sx={{
            color: "white",
            textDecoration: "none",
            fontWeight: "bold",
            flexGrow: 1,
          }}
        >
          LibraryHub
        </Typography>

        <Button color="inherit" component={Link} to="/">
          Catalogue
        </Button>

        <Button color="inherit" component={Link} to="/me">
          My Loans
        </Button>

        <Button color="inherit" component={Link} to="/basket">
          Basket
        </Button>

        <Button color="inherit" component={Link} to="/admin/add">
          Add Book
        </Button>

        <FormControl
          size="small"
          sx={{
            minWidth: 150,
            bgcolor: "white",
            borderRadius: 1,
          }}
        >
          <Select
            value={selectedMemberId}
            onChange={handleMemberChange}
            aria-label="Select library member"
          >
            {members.map((member) => (
              <MenuItem key={member.id} value={member.id}>
                {member.name} ({member.type})
              </MenuItem>
            ))}
          </Select>
        </FormControl>

      </Toolbar>
    </AppBar>
  );
}

export default Navbar;
