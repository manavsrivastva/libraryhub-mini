App
└── BrowserRouter
    └── MemberProvider
        └── BasketProvider
            ├── CssBaseline
            └── Routes
                │
                ├── Layout
                │   ├── Navbar
                │   │   └── Member Selector
                │   └── Catalogue
                │       └── BookList
                │           └── BookCard
                │               └── AvailabilityBadge
                │
                ├── Layout
                │   ├── Navbar
                │   └── BookDetails
                │
                ├── Layout
                │   ├── Navbar
                │   └── MyLoans
                │
                ├── Layout
                │   ├── Navbar
                │   └── BorrowBasket
                │
                ├── Layout
                │   ├── Navbar
                │   └── AddBook
                │
                └── Layout
                    ├── Navbar
                    └── NotFound


State ownership diagram
App — shared providers

MemberContext

useState
- selectedMemberId
- setSelectedMemberId
  
  Used by Navbar and member-dependent pages


BasketContext

useReducer
- basket
- dispatch
  
  ADD / REMOVE / CLEAR



Individual pages — local state

Catalogue · BookDetails · MyLoans · AddBook