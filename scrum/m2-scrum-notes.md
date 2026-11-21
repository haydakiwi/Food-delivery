# Milestone 2 Scrum Notes

## November 13, 2026 — M2 Planning

### Discussion
- Reviewed the Milestone 2 requirements: integrate the M1 components into one
  Customer → Restaurant → Menu → Cart → Checkout → Order workflow.
- Identified the cross-subsystem business rules that the live demonstration
  will test (deactivated customers, one active cart, one restaurant per cart,
  unavailable items, valid quantities, price revalidation at checkout, cart
  closed only after the order is saved).
- Agreed on an implementation order based on dependencies: data layer first,
  then customer accounts and authentication, then cart/checkout/orders, then
  frontend integration.

### Role Assignments
- **Member 1 — Customer, Cart & Order data models, repositories, persistence:** Janhvi
- **Member 2 — Customer accounts, authentication & authorization:** Shukan
- **Member 3 — Restaurant/menu integration, cart, checkout & orders:** Jay
- **Member 4 — Frontend integration, CI, documentation & submission:** Hayden

### Outcome
- Each member created GitHub issues for their work and agreed to coordinate
  model structures and repository method signatures before building services.

---

## November 16, 2026 — Progress Update: Data Layer and Authentication

### Work completed
- Janhvi: shared `JsonRepository` base (PR #24), Customer (PR #25), Cart
  (PR #26), and Order repositories with a cross-file integrity check (PR #27).
  CI caught a missing `typing` import on Python 3.11/3.12, fixed in PR #24.
- Shukan: customer registration, sign-in, account management, deactivation,
  and role-based authorization (PR #29).

### Outcome
- Data layer and authentication merged; cart, checkout, and orders unblocked.

---

## November 20, 2026 — Progress Update: Cart, Checkout, Orders, Frontend

### Work completed
- Jay: cart service and API, checkout service, and order history (PR #30).
- Hayden: customer registration/sign-in, cart, checkout, and order frontend
  workflow (PR #33).
- Shukan: M2 Decision Receipt and provenance documentation (PR #35).

### Outcome
- The end-to-end workflow worked through the API and the frontend.

---

## November 20, 2026 — Integration Review

### Discussion
- Reviewed the remaining M2 work against the requirements.
- Jay added backend-calculated cart subtotal, delivery fee, and total
  (PR #51), reviewed and merged after error-handling and test feedback.
- Identified remaining gaps: frontend cart quantity/remove/clear controls and
  totals display, showing the created order after checkout, a
    `GET /orders/{order_id}` endpoint, README updates for M2, integrated
  workflow tests, Project Board updates, and M2 scrum notes.
  
### Assignments
- **Hayden:** frontend cart controls and totals, order display after checkout,
  and an integrated workflow test.
- **Janhvi:** `GET /orders/{order_id}`, end-to-end workflow test, README
  update, and M2 scrum notes.
- **Jay:** review the remaining pull requests and keep the Decision Receipt
  current.
- **Shukan:** Project Board updates and a final documentation check.

### Outcome
- Agreed to merge the remaining work through reviewed pull requests, run the
  full test suite, and only then create the `m2-integrated-system` tag.