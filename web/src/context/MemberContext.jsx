
import { createContext, useContext, useState } from "react";

const MemberContext = createContext(null);

export function MemberProvider({ children }) {
  const [selectedMemberId, setSelectedMemberId] = useState("M001");

  const value = {
    selectedMemberId,
    setSelectedMemberId,
  };

  return (
    <MemberContext.Provider value={value}>
      {children}
    </MemberContext.Provider>
  );
}

export function useMember() {
  const context = useContext(MemberContext);

  if (!context) {
    throw new Error("useMember must be used inside MemberProvider");
  }

  return context;
}
