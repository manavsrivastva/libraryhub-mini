
import { Chip } from "@mui/material";

function AvailabilityBadge({ available }) {
  const isAvailable = available > 0;

  return (
    <Chip
      label={isAvailable ? `${available} Available` : "Unavailable"}
      color={isAvailable ? "success" : "error"}
      size="small"
      variant="outlined"
    />
  );
}

export default AvailabilityBadge;
