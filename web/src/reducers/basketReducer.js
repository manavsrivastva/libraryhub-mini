
export const initialBasketState = {
  items: [],
};

export function basketReducer(state, action) {
  switch (action.type) {
    case "ADD": {
      const alreadyExists = state.items.some(
        (item) => item.isbn === action.payload.isbn
      );

      if (alreadyExists) {
        return state;
      }

      return {
        ...state,
        items: [...state.items, action.payload],
      };
    }

    case "REMOVE":
      return {
        ...state,
        items: state.items.filter(
          (item) => item.isbn !== action.payload
        ),
      };

    case "CLEAR":
      return initialBasketState;

    default:
      return state;
  }
}
