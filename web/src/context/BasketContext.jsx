
import { createContext, useContext, useReducer } from "react";

import {
  basketReducer,
  initialBasketState,
} from "../reducers/basketReducer";

const BasketContext = createContext(null);

export function BasketProvider({ children }) {
  const [basket, dispatch] = useReducer(
    basketReducer,
    initialBasketState
  );

  return (
    <BasketContext.Provider value={{ basket, dispatch }}>
      {children}
    </BasketContext.Provider>
  );
}

export function useBasket() {
  const context = useContext(BasketContext);

  if (!context) {
    throw new Error(
      "useBasket must be used inside BasketProvider"
    );
  }

  return context;
}
