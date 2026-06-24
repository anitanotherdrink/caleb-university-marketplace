# Product Requirements Document — Caleb University Student Marketplace

**Product:** Secure, web-based C2C e-commerce platform for verified Caleb University students
**Source document:** *Design and Implementation of a Secure Web-Based E-Commerce Platform for Caleb University Students* (Chapters 1–3 draft)
**Stack (mandated by this PRD):** Python 3.11+ / Streamlit
**Document status:** Draft v1.0 · Owner: Product Eng · Last updated: 2026-06-24

---

## Traceability conventions

Every requirement carries one of three tags:

| Tag | Meaning |
|---|---|
| `[Src §X]` | Traces directly to a section of the source thesis (Chapters 1–3). |
| `[Assumption]` | Source is silent; an explicit decision is made here and listed in §15.2. |
| `[Industry standard]` | Standard behavior expected of this class of system, added for completeness. |

**Foundational assumption (governs the whole document).** The thesis specifies a generic three-tier web application built with "standard web technologies" `[Src §3.6]`. This PRD binds that architecture to a **Python/Streamlit** implementation: Streamlit is the presentation tier, a Python service layer is the application tier, and a SQL database is the data tier. All thesis functional and non-functional requirements are preserved; only the realization technology is fixed. `[Assumption]`

---

## 1. Executive Summary

### 1.1 Problem
Caleb University students form an active campus micro-economy (textbooks, gadgets, clothing, second-hand goods) but have no dedicated platform; they rely on WhatsApp/Telegram groups, notice boards, and word of mouth `[Src §3.4]`. These channels cannot categorize, search, or filter listings, cannot verify who is participating, keep no transaction records, and force students to expose personal contacts and meet strangers `[Src §3.4.1]`. National platforms (Jumia, Konga) are built for large-scale, long-distance, logistics-heavy trade and do not serve localized, low-value, trust-dependent campus exchange `[Src §1.2, §2.4.1]`.

### 1.2 Target users
Verified Caleb University students acting interchangeably as **buyers** and **sellers**, plus a platform **administrator** `[Src §1.6, §3.7.1]`.

### 1.3 Goals
1. Restrict access to verified students via institutional-email verification `[Src §1.4(iii), §2.2.4]`.
2. Provide a responsive, intuitive interface for listing, browsing, searching, and filtering `[Src §1.4(ii)]`.
3. Provide a product-management module for sellers to create, update, and remove listings `[Src §1.4(iv)]`.
4. Provide structured order placement and management with in-person, off-platform payment (simulated checkout) `[Src §1.6, §2.2.5]`.
5. Be evaluable on performance, usability, and security `[Src §1.4(v)]`.

### 1.4 Non-goals
- Live online payment gateway integration `[Src §1.6]`.
- Native Android/iOS apps `[Src §1.6]`.
- Users outside the verified Caleb University community `[Src §1.6]`.
- Platform-managed delivery/logistics (buyers and sellers are co-located) `[Src §1.1, §2.2.5]`.

### 1.5 North Star
> **A verified Caleb student can list, find, and safely transact a campus item end-to-end without leaving the platform or exposing personal contact details to strangers.**

### 1.6 Top success metrics

| # | Metric | Definition | Target |
|---|---|---|---|
| M1 | Verification completion rate | Verified accounts ÷ registrations started | ≥ 80% `[Assumption]` |
| M2 | Listing-to-discovery success | Sessions where a search/filter returns ≥1 result the user opens | ≥ 70% `[Assumption]` |
| M3 | Order completion rate | Orders reaching `completed` ÷ orders placed | ≥ 60% `[Assumption]` |
| M4 | p95 interaction latency | Server-side handling of a user action (search, list, place order) | < 1.5 s p95 `[Industry standard]` |
| M5 | Plaintext-credential incidents | Passwords stored or logged in plaintext | 0, always `[Src §3.3.2(i)]` |

---

## 2. Scope & Out-of-Scope

### 2.1 In scope
- Secure registration + institutional-email verification `[Src §3.3.1(i)]`
- Login/logout authentication with hashed passwords and managed sessions `[Src §3.3.1(ii), §2.2.4]`
- Profile management (view/update personal + contact details) `[Src §3.3.1(iii)]`
- Product management: create, view, edit, delete listings with title, description, price, condition, quantity, category, image `[Src §3.3.1(iv)]`
- Product discovery: browse + search + filter by keyword, category, price `[Src §3.3.1(v)]`
- Order placement generating a persistent order record `[Src §3.3.1(vi)]`
- Order management with seller-driven status lifecycle `[Src §3.3.1(vii)]`
- Administration: verify/manage users, manage categories, oversee listings & transactions `[Src §3.3.1(viii)]`
- Cart + simulated checkout (order record only; no funds transfer) `[Src §2.2.5, §1.6]`
- Role-based access control (buyer / seller / admin, least privilege) `[Src §2.2.4]`
- Responsive layout for phone and desktop `[Src §3.3.2(iii)]`

### 2.2 Out of scope (explicit exclusions)
- Live payment gateway / funds transfer `[Src §1.6, §2.2.5]`
- Native mobile apps `[Src §1.6]`
- Non-Caleb users / public access `[Src §1.6]`
- Delivery, shipping, escrow, or dispute arbitration by the platform `[Src §2.2.5]`
- Ratings/reputation engine — noted as a commercial-platform feature, **not** required because verified membership substitutes for reputation `[Src §2.2.2]`. Treated as future work. `[Assumption]`
- In-app chat/messaging — coordination happens in person on campus `[Src §2.2.5]`. Future work. `[Assumption]`

---

## 3. Users & Use Cases

### 3.1 Personas

| Persona | Role | Capabilities | Constraints |
|---|---|---|---|
| New Student | Unverified visitor | Register, verify institutional email `[Src §3.7.1]` | No marketplace access until verified |
| Registered Student (Buyer) | Verified member | Browse, search, view details, place orders, manage own orders `[Src §3.7.1]` | Can only act on own data |
| Registered Student (Seller) | Verified member | All buyer actions + create/edit/delete own listings, update status of orders on own listings `[Src §3.7.1]` | Same person as buyer; "seller" is a capability, not a separate account `[Assumption]` |
| Administrator | Platform operator | Verify/manage users, manage categories, oversee listings & transactions `[Src §3.3.1(viii)]` | Single trusted operator; no self-service admin signup `[Assumption]` |
| Authentication Service | External actor | Verifies institutional identity during registration/login `[Src §3.7.1]` | Realized as SMTP email-verification + domain check `[Assumption]` |

> **Role note.** The `role` column in the User table allows `buyer, seller, admin` `[Src §3.8.2 Table 3.1]`, but the use-case model treats every verified student as able to both buy and sell `[Src §3.7.1]`. This PRD resolves the tension by making **buyer/seller a per-action capability** of every verified student, reserving the `role` field to distinguish `student` from `admin`. `[Assumption]` (See gap G-2, §15.2.)

### 3.2 Use-case matrix (Persona × Goal × Frequency × MoSCoW)

| Goal | Persona | Frequency | Priority |
|---|---|---|---|
| Register & verify | New Student | Once | Must |
| Log in / out | Registered Student | Daily | Must |
| Edit profile | Registered Student | Rare | Should |
| Create listing | Seller | Weekly | Must |
| Edit/delete listing | Seller | Weekly | Must |
| Upload product image | Seller | Per listing | Must |
| Browse/search/filter | Buyer | Daily | Must |
| Place order (simulated checkout) | Buyer | Weekly | Must |
| Update order status | Seller | Per order | Must |
| View own orders | Buyer & Seller | Weekly | Must |
| Verify/manage users | Admin | Daily | Must |
| Manage categories | Admin | Rare | Must |
| Oversee listings/transactions | Admin | Daily | Should |

### 3.3 Roles & permissions (CRUD per object)

Legend: C=create, R=read, O=own only, –=none.

| Object | New Student | Buyer | Seller | Admin |
|---|---|---|---|---|
| Own account/profile | C (register) | R/U own | R/U own | R/U all |
| User verification flag | – | – | – | U all `[Src §3.3.1(viii)]` |
| Category | – | R | R | C/R/U/D `[Src §3.3.1(viii)]` |
| Product listing | – | R (available) | C/R/U/D **own** `[Src §3.3.1(iv)]` | R all, D (moderate) `[Src §3.3.1(viii)]` |
| Order (as buyer) | – | C/R **own** `[Src §3.3.1(vi)]` | C/R own | R all `[Src §3.3.1(viii)]` |
| Order status (as seller) | – | – | U own-listing orders `[Src §3.3.1(vii)]` | U all |

---

## 4. Functional Requirements (exhaustive)

> Each FR uses GIVEN–WHEN–THEN acceptance criteria. Telemetry event names use `snake_case`.

### FR-001 — Account Registration
- **Description / why:** A prospective user creates an account with full name, institutional email, password, and optional phone. `[Src §3.3.1(i), §3.8.2 Table 3.1]`
- **Preconditions:** Visitor not authenticated. Email domain matches the institutional domain. `[Src §2.2.4]`
- **Behavior:** Validate inputs → reject duplicate email (unique constraint) `[Src §3.8.2 Table 3.1]` → hash password (never store plaintext) `[Src §3.3.2(i)]` → create `User` with `is_verified=false` → trigger FR-002. Empty state: blank form with inline field hints. Error states: duplicate email, weak password, non-institutional domain, network failure.
- **Inputs / validation:** `full_name` ≤100 chars, not null; `email` ≤120, unique, must match `@<institution-domain>` regex `[Assumption]`; `password` ≥10 chars with mixed character classes `[Industry standard]`; `phone` ≤20, optional `[Src §3.8.2 Table 3.1]`.
- **Outputs:** Persisted unverified `User`; verification email dispatched.
- **Acceptance criteria:**
  1. GIVEN a valid institutional email and strong password, WHEN the user submits, THEN a `User` row is created with `is_verified=false` and a verification email is sent.
  2. GIVEN an email already registered, WHEN the user submits, THEN registration is rejected with "this email is already registered" and no row is created.
  3. GIVEN a non-institutional email domain, WHEN the user submits, THEN registration is rejected before any row is created.
  4. GIVEN a password under the minimum strength, WHEN the user submits, THEN the form blocks submission and shows the rule that failed.
- **Telemetry:** `registration_started`, `registration_submitted{domain_valid}`, `registration_succeeded`, `registration_rejected{reason}`.
- **Open questions:** Exact institutional domain string (see G-1, §15.2).

### FR-002 — Institutional Email Verification
- **Description / why:** Confirm the user controls a Caleb institutional address before granting marketplace access — this is the trust foundation of the platform. `[Src §2.2.4, §1.4(iii)]`
- **Preconditions:** An unverified `User` exists.
- **Behavior:** Generate a single-use, time-limited token `[Industry standard]` → email a verification link → on valid click set `is_verified=true`. Edge cases: expired token (offer resend), already-verified (idempotent success), invalid/forged token (reject). Empty state: "check your inbox" screen with resend control.
- **Inputs / validation:** Token: opaque, ≥128-bit entropy, TTL 24h `[Assumption]`.
- **Outputs:** `is_verified` flipped to true; token consumed.
- **Acceptance criteria:**
  1. GIVEN a valid unexpired token, WHEN visited, THEN `is_verified` becomes true and the user is routed to login.
  2. GIVEN an expired token, WHEN visited, THEN access is refused and a resend option is shown.
  3. GIVEN an already-verified account, WHEN the link is re-visited, THEN the system shows success without error and does not duplicate state.
- **Telemetry:** `verification_email_sent`, `verification_succeeded`, `verification_token_expired`, `verification_resent`.

### FR-003 — Authentication (Login / Logout)
- **Description / why:** A verified user logs in with credentials and can log out. `[Src §3.3.1(ii)]`
- **Preconditions:** Account exists and `is_verified=true`.
- **Behavior:** Look up by email → verify password against stored hash `[Src §2.2.4]` → on success establish a session `[Src §3.7.2]`. Block login for unverified accounts. Throttle repeated failures `[Industry standard]`. Logout clears the session.
- **Inputs / validation:** `email`, `password`. Generic failure message ("invalid email or password") to avoid user enumeration `[Industry standard]`.
- **Acceptance criteria:**
  1. GIVEN correct credentials on a verified account, WHEN the user logs in, THEN a session is created and the home page renders.
  2. GIVEN correct credentials on an unverified account, WHEN the user logs in, THEN login is refused with a prompt to verify email.
  3. GIVEN N consecutive failures, WHEN the threshold is exceeded, THEN further attempts are rate-limited.
  4. GIVEN an authenticated session, WHEN the user logs out, THEN the session is destroyed and protected pages are no longer reachable.
- **Telemetry:** `login_succeeded`, `login_failed{reason}`, `login_rate_limited`, `logout`.

### FR-004 — Session Management
- **Description / why:** Maintain authenticated state across reruns/navigation and protect against stale or hijacked sessions. `[Src §2.2.4, §2.3.3]`
- **Behavior:** Persist a signed session token; idle timeout 30 min, absolute timeout 12 h `[Assumption]`; invalidate on logout and on password change `[Industry standard]`. Protected pages redirect unauthenticated users to login.
- **Acceptance criteria:**
  1. GIVEN an authenticated session, WHEN the user navigates between pages, THEN they remain logged in without re-entering credentials.
  2. GIVEN 30 minutes of inactivity, WHEN the user acts, THEN they are required to re-authenticate.
  3. GIVEN a logged-out session token, WHEN replayed, THEN it is rejected.
- **Telemetry:** `session_started`, `session_expired{type}`, `session_invalidated`.

### FR-005 — Profile Management
- **Description / why:** A user views and updates personal and contact details. `[Src §3.3.1(iii)]`
- **Behavior:** Editable: `full_name`, `phone`. Read-only: `email` (identity anchor), `role`, `is_verified` `[Assumption]`. Validation mirrors registration.
- **Acceptance criteria:**
  1. GIVEN a logged-in user, WHEN they update name/phone with valid values, THEN changes persist and re-render.
  2. GIVEN an invalid phone, WHEN saved, THEN the update is blocked with an inline error.
  3. GIVEN any user, WHEN they open profile, THEN email/verification status display as read-only.
- **Telemetry:** `profile_viewed`, `profile_updated{fields}`, `profile_update_failed{reason}`.

### FR-006 — Create Listing
- **Description / why:** A seller creates a product listing. `[Src §3.3.1(iv)]`
- **Inputs / validation (per Table 3.3):** `title` ≤120 not null; `description` text optional; `price` DECIMAL(10,2) > 0 not null; `condition` ∈ {new, used} not null; `quantity` INT ≥1 default 1; `category_id` FK required; `image` ≥1 (see FR-009). `[Src §3.8.2 Table 3.3]`
- **Behavior:** On submit, create `Product` with `seller_id` = current user, `status=available`, `created_at=now`. Empty state: guided form. Error states: missing required field, invalid price, oversized/invalid image.
- **Acceptance criteria:**
  1. GIVEN valid fields and a valid image, WHEN submitted, THEN a `Product` is created with `status=available` and appears in discovery.
  2. GIVEN a non-positive price, WHEN submitted, THEN creation is blocked with a validation message.
  3. GIVEN a missing category, WHEN submitted, THEN creation is blocked.
- **Telemetry:** `listing_create_started`, `listing_created{category_id,condition}`, `listing_create_failed{reason}`.

### FR-007 — Edit / Update Listing
- **Description / why:** A seller updates an owned listing. `[Src §3.3.1(iv)]`
- **Behavior:** Only the owning seller (or admin) may edit `[Src §2.2.4 least privilege]`. Editable fields = all create fields plus `status` ∈ {available, sold}. Optimistic concurrency: reject stale writes `[Industry standard]`.
- **Acceptance criteria:**
  1. GIVEN an owned listing, WHEN the seller edits price/quantity, THEN changes persist and reflect in discovery.
  2. GIVEN a listing they do not own, WHEN a user attempts to edit it, THEN the action is forbidden.
  3. GIVEN a listing marked `sold`, WHEN browsing, THEN it is excluded from default available results.
- **Telemetry:** `listing_updated{fields}`, `listing_status_changed{from,to}`, `listing_edit_forbidden`.

### FR-008 — Delete Listing
- **Description / why:** A seller removes an owned listing. `[Src §3.3.1(iv)]`
- **Behavior:** Soft-delete preferred to preserve referential integrity with historical `OrderItem` rows `[Industry standard]`; admin may delete to moderate `[Src §3.3.1(viii)]`. Confirm before delete.
- **Acceptance criteria:**
  1. GIVEN an owned listing with no orders, WHEN deleted and confirmed, THEN it disappears from discovery.
  2. GIVEN an owned listing referenced by an order, WHEN deleted, THEN historical order records remain intact (price/quantity snapshot preserved — see FR-011).
  3. GIVEN a non-owner non-admin, WHEN they attempt deletion, THEN it is forbidden.
- **Telemetry:** `listing_deleted{soft|hard}`, `listing_delete_forbidden`.

### FR-009 — Product Image Upload
- **Description / why:** Listings carry at least one image. `[Src §3.3.1(iv)]` **Note:** the data dictionary omits an image column (gap G-3, §15.2); this PRD adds `image_path`. `[Assumption]`
- **Inputs / validation:** MIME ∈ {image/jpeg, image/png, image/webp}; max 5 MB per file `[Assumption]`; reject non-image content even if extension is spoofed `[Industry standard]`.
- **Behavior:** Store under a non-executable media path keyed by `product_id`; persist relative path on the `Product`. Empty state: placeholder thumbnail if image processing pending.
- **Acceptance criteria:**
  1. GIVEN a valid JPEG ≤5 MB, WHEN uploaded, THEN it is stored and rendered on the listing.
  2. GIVEN a 9 MB file, WHEN uploaded, THEN it is rejected with a size error.
  3. GIVEN a `.png` file whose bytes are not an image, WHEN uploaded, THEN it is rejected by content sniffing.
- **Telemetry:** `image_uploaded{bytes,mime}`, `image_rejected{reason}`.

### FR-010 — Product Discovery (Browse / Search / Filter)
- **Description / why:** Buyers browse and locate items by keyword, category, and price. `[Src §3.3.1(v)]`
- **Behavior:** Default view = available listings, newest first `[Assumption]`. Keyword matches title/description; category filter via `category_id`; price filter via min/max range. Combinable filters. Empty state: "no items match" with a clear-filters action. Pagination/virtualization for large result sets (see §6).
- **Inputs / validation:** keyword ≤120; price min ≤ max, both ≥0.
- **Acceptance criteria:**
  1. GIVEN listings across categories, WHEN the buyer filters by one category, THEN only that category's available listings show.
  2. GIVEN a price range, WHEN applied, THEN only listings within `[min,max]` show.
  3. GIVEN a keyword with no matches, WHEN searched, THEN an empty state with a clear-filters control renders.
  4. GIVEN keyword + category + price together, WHEN applied, THEN results satisfy all three.
- **Telemetry:** `search_performed{keyword_len,category_id,price_min,price_max,result_count}`, `listing_viewed{product_id}`, `filters_cleared`.

### FR-011 — Cart & Order Placement (Simulated Checkout)
- **Description / why:** A buyer indicates intent to purchase; the system generates and stores a persistent order record. Payment occurs in person; checkout is simulated (no funds transfer). `[Src §3.3.1(vi), §2.2.5, §1.6]`
- **Behavior:** Buyer adds item(s) to cart → checkout creates one `Order` (`status=pending`) with one or more `OrderItem` rows, each snapshotting `price` and `quantity` at order time `[Src §3.8.2 Table 3.5]`. No payment step; a confirmation screen states payment is settled in person on campus `[Src §2.2.5]`. Edge cases: quantity exceeds availability, listing became `sold` mid-flow, empty cart.
- **Inputs / validation:** `quantity` ≥1 and ≤ available; cart non-empty.
- **Acceptance criteria:**
  1. GIVEN an available item, WHEN the buyer checks out, THEN an `Order` (`pending`) plus matching `OrderItem`(s) persist with price snapshot.
  2. GIVEN a requested quantity above availability, WHEN checkout runs, THEN it is blocked with an availability error.
  3. GIVEN a listing that sold before confirmation, WHEN checkout runs, THEN the item is flagged unavailable and excluded.
  4. GIVEN a successful order, WHEN the confirmation renders, THEN it explicitly states payment is handled in person and no funds were transferred.
- **Telemetry:** `cart_item_added{product_id,qty}`, `checkout_started{item_count}`, `order_placed{order_id,item_count,total}`, `checkout_blocked{reason}`.

### FR-012 — Order Management & Status Lifecycle
- **Description / why:** Buyers and sellers view orders; the seller updates status. `[Src §3.3.1(vii)]`
- **States & transitions:** `pending → confirmed → completed`; `pending → cancelled`; `confirmed → cancelled` `[Src §3.8.2 Table 3.4]`. Terminal: `completed`, `cancelled`. Illegal transitions rejected (e.g., `completed → pending`). `[Industry standard]`
- **Behavior:** Buyer sees own orders (read); seller sees orders on own listings and updates status; on `completed`, the related listing may be set `sold` `[Assumption]`.
- **Acceptance criteria:**
  1. GIVEN a `pending` order, WHEN the seller confirms, THEN status becomes `confirmed` and both parties see it.
  2. GIVEN a `confirmed` order, WHEN the seller marks complete, THEN status becomes `completed` and the listing may be set `sold`.
  3. GIVEN any order, WHEN an illegal transition is attempted, THEN it is rejected and state is unchanged.
  4. GIVEN a buyer, WHEN they view orders, THEN they see only their own.
- **Telemetry:** `order_status_changed{order_id,from,to}`, `order_status_illegal{from,to}`, `orders_viewed{role}`.

### FR-013 — Role-Based Access Control
- **Description / why:** Enforce least privilege across student and admin roles. `[Src §2.2.4]`
- **Behavior:** Every protected action checks (a) authentication, (b) verification, (c) role/ownership. Admin-only routes reject students. Ownership-scoped routes reject non-owners.
- **Acceptance criteria:**
  1. GIVEN a student, WHEN they request an admin route, THEN access is denied.
  2. GIVEN an unverified user, WHEN they request any marketplace action, THEN access is denied with a verification prompt.
  3. GIVEN a seller, WHEN they act on another seller's listing, THEN access is denied.
- **Telemetry:** `authz_denied{route,reason}`.

### FR-014 — Administration
- **Description / why:** Admin verifies/manages users, manages categories, oversees listings & transactions. `[Src §3.3.1(viii)]`
- **Behavior:** Admin can set/clear `is_verified`, deactivate users, CRUD categories `[Src §3.8.2 Table 3.2]`, view/moderate listings, and view all orders. Category delete blocked while products reference it (or reassign) `[Industry standard]`.
- **Acceptance criteria:**
  1. GIVEN a pending user, WHEN the admin verifies them, THEN `is_verified=true` and the user gains access.
  2. GIVEN a category in use, WHEN the admin deletes it, THEN deletion is blocked or requires reassignment.
  3. GIVEN any listing, WHEN the admin moderates (removes) it, THEN it leaves discovery and the seller is notified `[Assumption]`.
- **Telemetry:** `admin_user_verified`, `admin_user_deactivated`, `admin_category_changed{op}`, `admin_listing_moderated`.

---

## 5. Information Architecture & Navigation

### 5.1 Sitemap (Streamlit multipage)
```
/ (app.py)                  → router + auth gate + theming
├── Public
│   ├── Login
│   ├── Register
│   └── Verify Email (token landing)
├── Student (auth + verified)
│   ├── Home / Browse        (default after login)
│   ├── Product Detail        (dialog/page)
│   ├── Search & Filter       (inline on Browse)
│   ├── Cart                  (dialog)
│   ├── Checkout (simulated)  (dialog → confirmation)
│   ├── My Listings           (seller view: create/edit/delete)
│   ├── Listing Editor        (create/edit form)
│   ├── My Orders             (buyer + seller tabs)
│   └── Profile
└── Admin (auth + role=admin)
    ├── Users
    ├── Categories
    ├── Listings (moderation)
    └── Orders (oversight)
```
Mapping to source flow: visitor → register → verify → login → home; seller manages listings; buyer browses/searches/views/orders; seller updates status `[Src §3.6.2, §3.7.1]`.

### 5.2 Navigation rules
- Unauthenticated access to any Student/Admin page redirects to Login `[Src §3.6.2]`.
- Authenticated-but-unverified users are pinned to a "verify your email" screen `[Src §2.2.4]`.
- Admin pages hidden from the nav for non-admins (defense in depth on top of FR-013).
- Deep links: verification token URL is the only externally shared deep link; all other navigation is in-session `[Assumption]`. Streamlit reruns mean back/forward map to the browser; in-app state is held in `st.session_state` (see §9.3).

---

## 6. UX & Content Specifications

### 6.1 Per-screen specs

| Screen | Purpose | Primary actions | Key components | Layout / pagination |
|---|---|---|---|---|
| Login | Authenticate | Log in, go to register | email/password inputs, error banner | Single centered column |
| Register | Create account | Submit registration | name/email/password/phone, validation hints | Single column |
| Verify Email | Confirm ownership | Resend link | status message, resend button | Single column, no nav |
| Browse/Home | Discover items | Search, filter, open item, add to cart | search box, category select, price range, listing grid | Grid; paginate 20/page or lazy-load `[Industry standard]` |
| Product Detail | Inspect item | Add to cart, view seller | image, title, price, condition, category, seller name | Two-column (image / meta) |
| Cart | Review selection | Adjust qty, checkout | line items, totals | List |
| Checkout (sim) | Confirm order | Place order | summary, in-person-payment notice | Single column → confirmation |
| My Listings | Manage inventory | Create, edit, delete | table of own listings + status | Table, paginate 20/page |
| Listing Editor | Create/edit listing | Save, upload image | all product fields, image uploader | Form |
| My Orders | Track orders | (Seller) update status | buyer/seller tabs, status chips | Table |
| Profile | Manage identity | Update name/phone | editable + read-only fields | Form |
| Admin pages | Operate platform | Verify, manage, moderate | data tables + row actions | Tables, paginate |

### 6.2 Content states
- **Empty:** Browse with no results → "No items match your filters." + Clear filters. My Listings empty → "You haven't listed anything yet." + Create listing. My Orders empty → "No orders yet."
- **Loading:** Use `st.status`/`st.spinner` for DB-bound actions; skeleton/placeholder thumbnails for images (FR-009).
- **Error copy (samples):** "This email is already registered." / "Invalid email or password." / "That image is too large (max 5 MB)." / "This item is no longer available." Copy is plain, blame-free, and actionable, per usability heuristics `[Src §2.3.2]`.

### 6.3 Accessibility (WCAG 2.1 AA checklist)
- [ ] All form inputs have visible labels and programmatic `aria-label`s.
- [ ] Color contrast ≥ 4.5:1 for text.
- [ ] Keyboard: full flows operable without a mouse; logical focus order on forms.
- [ ] Status changes announced (visible feedback for every action — visibility of system status `[Src §2.3.2]`).
- [ ] Images carry meaningful `alt` text (listing title).
- [ ] Touch targets ≥ 44×44 px for mobile `[Src §3.3.2(iii)]`.
- [ ] No reliance on color alone for status (use chip text: pending/confirmed/completed/cancelled).

> Streamlit caveat: native widgets set most ARIA roles, but custom HTML/components must be checked manually. Verification is part of the usability evaluation `[Src §1.4(v)]`.

---

## 7. Data Model & Storage

### 7.1 Entity-relationship (logical)
```
User 1───∞ Product      (seller_id)            [Src §3.8.1]
Category 1───∞ Product   (category_id)
User 1───∞ Order         (buyer_id)
Order 1───∞ OrderItem    (order_id)
Product 1───∞ OrderItem  (product_id)
```

### 7.2 Schema (from data dictionary, with additive fields flagged)

**User** `[Src §3.8.2 Table 3.1]`

| Field | Type | Constraints |
|---|---|---|
| user_id | INT | PK, auto |
| full_name | VARCHAR(100) | not null |
| email | VARCHAR(120) | not null, unique |
| password_hash | VARCHAR(255) | not null |
| phone | VARCHAR(20) | nullable |
| role | VARCHAR(20) | not null (`student`/`admin`) `[Assumption: see §3.1 role note]` |
| is_verified | BOOLEAN | default false |
| created_at | DATETIME | default now |
| last_login | DATETIME | nullable `[Industry standard]` |

**Category** `[Src §3.8.2 Table 3.2]`: `category_id` PK; `name` VARCHAR(60) not null unique; `description` VARCHAR(255) nullable.

**Product** `[Src §3.8.2 Table 3.3]`

| Field | Type | Constraints |
|---|---|---|
| product_id | INT | PK, auto |
| seller_id | INT | FK→User |
| category_id | INT | FK→Category |
| title | VARCHAR(120) | not null |
| description | TEXT | nullable |
| price | DECIMAL(10,2) | not null, > 0 |
| condition | VARCHAR(20) | not null (`new`/`used`) |
| quantity | INT | default 1, ≥1 |
| status | VARCHAR(20) | default `available` (`available`/`sold`) |
| created_at | DATETIME | default now |
| **image_path** | VARCHAR(255) | **not null** — *added; gap G-3* `[Assumption]` |

**Orders** `[Src §3.8.2 Table 3.4]`: `order_id` PK; `buyer_id` FK→User; `status` VARCHAR(20) default `pending` (`pending`/`confirmed`/`completed`/`cancelled`); `created_at` default now.

**OrderItem** `[Src §3.8.2 Table 3.5]`: `order_item_id` PK; `order_id` FK→Orders; `product_id` FK→Product; `quantity` INT not null; `price` DECIMAL(10,2) not null (snapshot at order time).

**EmailVerificationToken** *(added for FR-002)* `[Industry standard]`: `token_id` PK; `user_id` FK→User; `token_hash` VARCHAR(255); `expires_at` DATETIME; `consumed_at` DATETIME nullable.

### 7.3 Pydantic models (validation layer)
```python
from decimal import Decimal
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, field_validator

class Role(str, Enum):
    student = "student"
    admin = "admin"

class Condition(str, Enum):
    new = "new"
    used = "used"

class OrderStatus(str, Enum):
    pending = "pending"
    confirmed = "confirmed"
    completed = "completed"
    cancelled = "cancelled"

class UserCreate(BaseModel):
    full_name: str = Field(max_length=100)
    email: EmailStr
    password: str = Field(min_length=10)
    phone: str | None = Field(default=None, max_length=20)

    @field_validator("email")
    @classmethod
    def institutional_domain(cls, v: str) -> str:
        # domain set in config; see G-1
        if not v.lower().endswith("@calebuniversity.edu.ng"):
            raise ValueError("must be a Caleb University email")
        return v.lower()

class ProductCreate(BaseModel):
    title: str = Field(max_length=120)
    description: str | None = None
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    condition: Condition
    quantity: int = Field(default=1, ge=1)
    category_id: int

class OrderItemIn(BaseModel):
    product_id: int
    quantity: int = Field(ge=1)
```

### 7.4 Persistence choice
- **Dev:** SQLite (zero-config, file-based) — matches the project's modest scale `[Src §3.2]`.
- **Prod:** PostgreSQL — concurrency, integrity, backups `[Industry standard]`.
- **Rationale:** The thesis specifies a relational database `[Src §3.6.1, §3.8]`; SQLAlchemy abstracts both so the same models run in dev and prod.
- **Migrations:** Alembic; one baseline migration from §7.2 + a migration adding `image_path` and `EmailVerificationToken`.

### 7.5 Retention, backup, PII
- **PII held:** name, institutional email, phone, hashed password. No payment data (out of scope). `[Src §1.6]`
- **Retention:** Active while enrolled; deactivated accounts anonymized on request `[Assumption]`.
- **Backup:** Daily prod DB snapshot, 7-day retention `[Industry standard]`.
- **Password storage:** Argon2id/bcrypt hashes only; never plaintext, never logged `[Src §3.3.2(i)]`.

---

## 8. APIs & Integrations

> Streamlit is not a REST framework; the "API" here is the **typed service layer** the UI calls. Internal contracts are listed as service functions; the one external integration is SMTP.

### 8.1 Internal service contracts (service-layer "endpoints")

| Service fn | Inputs | Returns | Errors |
|---|---|---|---|
| `auth.register(UserCreate)` | user payload | `User` (unverified) | `DuplicateEmail`, `InvalidDomain` |
| `auth.verify(token)` | token | `bool` | `TokenExpired`, `TokenInvalid` |
| `auth.login(email,pwd)` | creds | session | `BadCredentials`, `NotVerified`, `RateLimited` |
| `catalog.search(filters)` | keyword/cat/price | `list[Product]` | `ValidationError` |
| `catalog.create_listing(ProductCreate,image)` | listing+file | `Product` | `ValidationError`, `ImageRejected` |
| `catalog.update_listing(id,patch)` | id+fields | `Product` | `Forbidden`, `NotFound`, `StaleWrite` |
| `orders.place(buyer_id,[OrderItemIn])` | cart | `Order` | `Unavailable`, `EmptyCart` |
| `orders.set_status(order_id,status)` | id+status | `Order` | `Forbidden`, `IllegalTransition` |
| `admin.verify_user(user_id)` | id | `User` | `Forbidden`, `NotFound` |

### 8.2 Third-party: SMTP email (verification)
- **Provider:** institutional SMTP or transactional service (e.g., provider with API key). `[Assumption]`
- **Failure handling:** if send fails, queue + retry with exponential backoff (3 attempts), surface a "resend" control to the user `[Industry standard]`.
- **Quotas/rate limits:** cap verification emails per address (e.g., 3/hour) to prevent abuse `[Industry standard]`.
- **Idempotency:** token generation is idempotent per active request; re-sends invalidate prior unconsumed tokens.

---

## 9. Python + Streamlit Implementation Plan

### 9.1 Architecture (textual)
```
[ Browser ]
    │  (HTTPS via reverse proxy / platform TLS)
    ▼
[ Streamlit presentation tier ]      app.py + pages/  + components/
    │  typed function calls
    ▼
[ Service layer (application tier) ] services/  (auth, catalog, orders, admin)
    │  repository interfaces
    ▼
[ Data layer ]                       models/ (SQLAlchemy) → SQLite(dev)/Postgres(prod)
                                     media/  (product images, non-executable)
```
Maps 1:1 to the thesis three-tier model `[Src §3.6.1]`: presentation = Streamlit, application = services, data = SQL DB.

### 9.2 Project structure
```
/app.py                      # router, theme, auth gate, global error boundary
/pages/
    01_login.py  02_register.py  03_verify.py
    10_browse.py 11_listing_editor.py 12_my_listings.py
    13_cart.py   14_my_orders.py 15_profile.py
    90_admin_users.py 91_admin_categories.py 92_admin_orders.py
/components/                  # reusable UI: listing_card, filter_bar, status_chip
/services/                    # auth.py catalog.py orders.py admin.py email.py
/models/                      # sqlalchemy.py pydantic_schemas.py
/data/                        # sqlite db (dev), migrations/
/media/                       # uploaded product images
/tests/                       # unit + e2e
/.streamlit/config.toml
pyproject.toml
```

### 9.3 State management (`st.session_state`)
- Naming: `auth_user`, `auth_session_token`, `cart_items`, `active_filters`, `editing_listing_id`. Prefix by domain.
- Lifecycle: set on login (FR-003), cleared on logout (FR-003) and expiry (FR-004). Cart persists across reruns within a session; cleared after `order_placed`.
- Auth gate pattern (top of every protected page):
```python
from services import auth
def require_auth(verified=True, admin=False):
    user = st.session_state.get("auth_user")
    if not user:
        st.switch_page("pages/01_login.py")
    if verified and not user.is_verified:
        st.switch_page("pages/03_verify.py")
    if admin and user.role != "admin":
        st.error("Admins only."); st.stop()
    return user
```

### 9.4 Caching
- `st.cache_resource`: DB engine/session factory, SMTP client — one per process, no TTL.
- `st.cache_data(ttl=60)`: category list, browse results — short TTL so new listings appear quickly.
- Invalidation: call `.clear()` on the relevant cached function after `listing_created`/`updated`/`deleted` so discovery reflects writes immediately (FR-006/007/008).

### 9.5 Long-running tasks
- Image processing and email send use `st.status("Sending verification…")` / `st.progress` for visible feedback (system-status heuristic `[Src §2.3.2]`).

### 9.6 File handling
- `st.file_uploader(type=["jpg","jpeg","png","webp"])`; enforce 5 MB cap and content-sniff MIME (FR-009); write to `/media/<product_id>/`; store relative path. Configure Streamlit `server.maxUploadSize`. Temp files cleared on failure.

### 9.7 Secrets & config
- `st.secrets` / env vars for `DB_URL`, `SMTP_*`, `SESSION_SIGNING_KEY`, `INSTITUTION_DOMAIN`. No secrets in code or VCS `[Src §2.3.3]`.

### 9.8 Minimal skeletons

`app.py`:
```python
import streamlit as st
from services import auth

st.set_page_config(page_title="Caleb Marketplace", layout="wide")

def main():
    try:
        if "auth_user" not in st.session_state:
            st.switch_page("pages/01_login.py")
        st.title("Campus Marketplace")
        # nav handled by Streamlit pages/ + role-aware hiding
    except Exception:
        st.error("Something went wrong. Please retry.")
        st.stop()

main()
```

Service with typed interface + exception mapping:
```python
# services/orders.py
from models.pydantic_schemas import OrderItemIn, OrderStatus
class Unavailable(Exception): ...
class IllegalTransition(Exception): ...

_ALLOWED = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"completed", "cancelled"},
    "completed": set(), "cancelled": set(),
}

def place(buyer_id: int, items: list[OrderItemIn], repo) -> "Order":
    if not items:
        raise ValueError("empty cart")
    for it in items:
        p = repo.get_product(it.product_id)
        if p.status != "available" or it.quantity > p.quantity:
            raise Unavailable(p.title)
    return repo.create_order(buyer_id, items)  # snapshots price per item

def set_status(order_id: int, new: OrderStatus, actor, repo) -> "Order":
    o = repo.get_order(order_id)
    if new.value not in _ALLOWED[o.status]:
        raise IllegalTransition(f"{o.status}->{new.value}")
    return repo.update_order_status(order_id, new.value)
```

Component (validated form):
```python
# components/listing_form.py
import streamlit as st
from models.pydantic_schemas import ProductCreate
from pydantic import ValidationError

def listing_form(categories, on_submit):
    title = st.text_input("Title", max_chars=120)
    price = st.number_input("Price (₦)", min_value=0.01, step=0.01)
    condition = st.selectbox("Condition", ["new", "used"])
    qty = st.number_input("Quantity", min_value=1, value=1, step=1)
    cat = st.selectbox("Category", categories, format_func=lambda c: c.name)
    img = st.file_uploader("Image", type=["jpg","jpeg","png","webp"])
    if st.button("Save listing"):
        try:
            payload = ProductCreate(title=title, price=price,
                condition=condition, quantity=qty, category_id=cat.category_id)
            on_submit(payload, img)
        except ValidationError as e:
            st.error(e.errors()[0]["msg"])
```

### 9.9 Testing
- **Unit (`pytest`):** services (auth domain check, order transition matrix, price snapshot) and Pydantic validators. Target ≥80% line coverage on `services/` + `models/`.
- **E2E smoke (Playwright against the running Streamlit app):** register→verify→login→list→search→order→status. One happy path + 3 negative paths (unverified login, oversized image, illegal status transition).

### 9.10 Performance targets
- Cold start < 5 s; warm interaction p95 < 1.5 s (M4). Profile DB queries with `EXPLAIN`; index `Product(category_id, status)`, `Product(seller_id)`, `OrderItem(order_id)`, `User(email)`.

### 9.11 i18n / formatting
- Single locale (English), currency ₦ (NGN), timezone Africa/Lagos; store timestamps in UTC, render local `[Assumption]`.

---

## 10. Non-Functional Requirements

| NFR | Requirement | Threshold | Verification |
|---|---|---|---|
| Security | Verified-only access, hashed passwords, encrypted transport `[Src §3.3.2(i)]` | 0 plaintext creds; TLS on all traffic | Code review + pen test §11 |
| Usability | Usable without training by an ordinary student `[Src §3.3.2(ii)]` | ≥80% task success in usability test | Heuristic eval (Nielsen) + user test `[Src §2.3.2]` |
| Responsiveness | Adapts to phone & desktop `[Src §3.3.2(iii)]` | Usable at 360px–1440px | Manual device matrix |
| Performance | Prompt response under normal load `[Src §3.3.2(iv)]` | p95 < 1.5 s (M4) | Load test |
| Reliability | Consistent behavior; data integrity `[Src §3.3.2(v)]` | FK constraints enforced; 99% successful actions | Integration tests |
| Maintainability | Modular organization `[Src §3.3.2(vi)]` | Layered structure §9.2; cyclomatic complexity caps | Lint + review |
| Observability | Logs/metrics/traces `[Industry standard]` | All FR telemetry emitted | Telemetry audit §12 |
| Portability | Runs on SQLite & Postgres `[Industry standard]` | Same suite passes on both | CI matrix |

---

## 11. Security & Privacy

### 11.1 Threat model (STRIDE)

| Threat | Example | Mitigation |
|---|---|---|
| **S**poofing | Outsider poses as a student | Institutional-email verification; verified-only access `[Src §2.2.4, §3.4.1(ii)]` |
| **T**ampering | Altering listings/orders of others | Ownership checks (FR-013); FK integrity; input validation `[Src §2.3.3]` |
| **R**epudiation | Denying an order was placed | Persistent order records + audit timestamps `[Src §3.3.1(vii)]` |
| **I**nfo disclosure | Leaking PII/credentials | Hashed passwords; TLS in transit; least-privilege queries `[Src §2.3.3, §3.3.2(i)]` |
| **D**enial of service | Login flooding, upload abuse | Rate limiting (FR-003); upload size caps (FR-009) |
| **E**levation | Student reaching admin actions | Role checks on every admin route (FR-013) |

### 11.2 AuthN / AuthZ / sessions
- AuthN: email+password, Argon2id/bcrypt hashing `[Src §2.2.4]`.
- AuthZ: RBAC + ownership, least privilege `[Src §2.2.4]`.
- Sessions: signed tokens, idle/absolute timeouts, invalidation on logout/password change (FR-004).

### 11.3 Input handling & supply chain
- Validate/sanitize all inputs via Pydantic; parameterized queries only (no string-built SQL) to prevent injection `[Src §2.3.3]`.
- Content-sniff uploads (FR-009); render images from a non-executable path.
- Dependency scanning (`pip-audit`) in CI; generate an SBOM (CycloneDX) per release `[Industry standard]`.

### 11.4 Privacy
- Collect only what FR-001 needs; no payment data `[Src §1.6]`. Privacy notice at registration `[Industry standard]`. Account anonymization on deactivation (§7.5).

---

## 12. Analytics & Experimentation

### 12.1 Event taxonomy (selected; full set inline per FR)

| Event | When | Key properties |
|---|---|---|
| `registration_succeeded` | account created | domain_valid |
| `verification_succeeded` | email verified | latency_to_verify |
| `login_succeeded` / `login_failed` | auth attempt | reason |
| `listing_created` | seller publishes | category_id, condition |
| `search_performed` | filter applied | result_count, filters |
| `order_placed` | checkout confirmed | item_count, total |
| `order_status_changed` | status update | from, to |
| `authz_denied` | blocked action | route, reason |

### 12.2 Dashboards & guardrails
- **Funnel:** registration → verification → first login → first listing/first order (drives M1, M3).
- **Discovery:** search→view→order conversion (M2).
- **Guardrails:** `login_failed` rate, `authz_denied` rate, p95 latency (M4), `checkout_blocked` reasons.

### 12.3 Experimentation
- A/B testing is **not** required for v1 (single small community) `[Assumption]`. If trialed later, candidate test: default sort (newest vs. price) measured on M2; success = +5% search→view with no M3 regression.

---

## 13. Rollout & Operations

### 13.1 Environments & flags
- `dev` (SQLite, local), `staging` (Postgres, seeded), `prod` (Postgres). Feature flags for admin-moderation and (future) ratings.

### 13.2 Deployment options
- **Option A — Streamlit Community Cloud (fastest):** push repo to GitHub → connect app → set `DB_URL`, `SMTP_*`, `SESSION_SIGNING_KEY` in Secrets → deploy. Suits demo/evaluation `[Src §1.4(v)]`. Note: external Postgres + media storage needed (ephemeral filesystem).
- **Option B — Docker on a cloud VM (production):**
  1. `Dockerfile` (python:3.11-slim, install `pyproject`, `EXPOSE 8501`, `CMD streamlit run app.py`).
  2. `docker compose` with `app` + `postgres` + volume for `/media` + reverse proxy (nginx/Caddy) terminating **TLS** (provides the encrypted transport NFR `[Src §3.3.2(i)]`).
  3. Configure `INSTITUTION_DOMAIN` and SMTP creds via env.

### 13.3 CI/CD (GitHub Actions jobs)
`lint` (ruff) → `type-check` (mypy) → `test` (pytest + coverage gate) → `security` (pip-audit) → `build` (docker) → `deploy` (on main, to staging then prod with manual approval).

### 13.4 Monitoring & runbooks
- Alerts: p95 latency > 1.5 s (5 min), error rate > 2%, verification email send-failure spike, DB connection saturation.
- Runbooks: (a) emails not sending → check SMTP creds/quota, fall back to manual admin verification; (b) DB locked (SQLite dev) → switch to Postgres; (c) image storage full → rotate/clear orphaned media; (d) login flood → confirm rate-limit active, block offending source.

---

## 14. Timeline & Resourcing

| Milestone | Deliverable | Depends on | Size |
|---|---|---|---|
| M0 Foundation | Project scaffold, DB models, auth gate | — | S |
| M1 Identity | Register, verify, login, sessions (FR-001–004) | M0 | M |
| M2 Listings | Product CRUD + image (FR-006–009) | M1 | M |
| M3 Discovery | Browse/search/filter (FR-010) | M2 | S |
| M4 Orders | Cart, simulated checkout, status (FR-011–012) | M2, M3 | M |
| M5 Admin + RBAC | Admin tools, RBAC hardening (FR-013–014) | M1–M4 | S |
| M6 Evaluate | Performance, usability, security tests (M-metrics) | M1–M5 | M |

**Critical path:** M0→M1→M2→M4→M6 (identity and listings gate orders and evaluation).

### 14.1 Risks (likelihood × impact)

| Risk | L | I | Mitigation |
|---|---|---|---|
| Streamlit session/auth limitations vs. true web app | M | H | Signed-token sessions + auth gate (FR-004); document caveats |
| SMTP deliverability to institutional domain | M | H | Transactional provider; manual admin verification fallback |
| Image storage ephemeral on Community Cloud | M | M | Use external object storage or Docker volume (Option B) |
| Scope creep into live payments | L | H | Hold the line on simulated checkout `[Src §1.6]` |
| Single-locale assumptions | L | L | Centralize formatting in one module |

---

## 15. Traceability & Coverage

### 15.1 Coverage matrix

| Source requirement | PRD section(s) | Feature ID | Acceptance tests |
|---|---|---|---|
| Registration & verification §3.3.1(i) | §2.1, §4 | FR-001, FR-002 | FR-001.1–4, FR-002.1–3 |
| Authentication §3.3.1(ii) | §4 | FR-003, FR-004 | FR-003.1–4, FR-004.1–3 |
| Profile management §3.3.1(iii) | §4 | FR-005 | FR-005.1–3 |
| Product management §3.3.1(iv) | §4, §7 | FR-006/007/008/009 | FR-006–009 (12 cases) |
| Product discovery §3.3.1(v) | §4, §6 | FR-010 | FR-010.1–4 |
| Order placement §3.3.1(vi) | §4 | FR-011 | FR-011.1–4 |
| Order management §3.3.1(vii) | §4 | FR-012 | FR-012.1–4 |
| Administration §3.3.1(viii) | §4 | FR-014 | FR-014.1–3 |
| RBAC / least privilege §2.2.4 | §3.3, §4, §11 | FR-013 | FR-013.1–3 |
| Simulated checkout §2.2.5, §1.6 | §2.1, §4 | FR-011 | FR-011.4 |
| Security NFR §3.3.2(i) | §10, §11 | NFR, threat model | §11 verification |
| Usability NFR §3.3.2(ii), §2.3.2 | §6.3, §10 | A11y checklist | Heuristic + user test |
| Responsiveness §3.3.2(iii) | §6, §10 | layout specs | Device matrix |
| Performance §3.3.2(iv) | §9.10, §10 | M4 | Load test |
| Reliability §3.3.2(v) | §7, §10 | FK/integrity | Integration tests |
| Maintainability §3.3.2(vi) | §9.2, §10 | layered structure | Lint + review |
| Three-tier architecture §3.6 | §9.1 | architecture | — |
| Data model §3.8 | §7 | schema | Migration tests |

### 15.2 Gaps & assumptions

| ID | Item | Type | Owner | Due |
|---|---|---|---|---|
| G-1 | Exact institutional email domain (e.g., `@calebuniversity.edu.ng`) not stated in source | Gap → config | Product | Before M1 |
| G-2 | `role` enum lists buyer/seller/admin but use-cases treat every student as both; PRD makes role = student/admin and buyer/seller a capability | Resolved assumption | Eng | Confirm at M0 |
| G-3 | Product image required in §3.3.1(iv) but absent from Table 3.3; PRD adds `image_path` | Gap → schema | Eng | M2 |
| G-4 | "Authentication Service" external actor (§3.7.1) is realized as SMTP verification + domain check | Assumption | Eng | M1 |
| G-5 | Cart appears in §2.2.5 conceptually; order placement in §3 is per-item. PRD supports multi-item cart | Assumption | Product | M4 |
| G-6 | Password policy, session timeouts, rate-limit thresholds not specified | Assumption | Security | M1 |
| G-7 | Listing moderation notification to seller (FR-014.3) | Assumption | Product | M5 |

---

## 16. Appendix

### 16.1 Glossary

| Term | Definition |
|---|---|
| C2C | Consumer-to-consumer commerce between individual students `[Src §1.7(iii)]` |
| Verified student | A confirmed member of the Caleb student community `[Src §1.7(vi)]` |
| Simulated checkout | Order flow producing a record without funds transfer; payment in person `[Src §2.2.5]` |
| Product management module | Seller component to create/view/update/remove listings `[Src §1.7(vii)]` |
| Responsive design | Layout adapting to screen size `[Src §1.7(viii)]` |
| CIA triad | Confidentiality, Integrity, Availability security model `[Src §2.3.3]` |
| RBAC | Role-based access control |
| Snapshot | Price/quantity copied onto an OrderItem at order time |

### 16.2 ASCII wireframes

Browse:
```
┌───────────────────────────────────────────────┐
│  Campus Marketplace        [Cart] [Profile] [⎋]│
│  ┌ search ─────────┐ [Category ▾] ₦[min]-[max] │
│  └─────────────────┘ [Apply] [Clear]           │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐                    │
│  │img │ │img │ │img │ │img │   ← listing grid   │
│  │₦…  │ │₦…  │ │₦…  │ │₦…  │                    │
│  └────┘ └────┘ └────┘ └────┘                    │
└───────────────────────────────────────────────┘
```
Order confirmation (simulated):
```
┌──────────────────────────────────────────────┐
│  Order #1042 placed — status: PENDING          │
│  1 × "Used Calculus textbook"  ₦3,500          │
│  ⓘ Payment is settled in person on campus.     │
│    No money was transferred by the platform.   │
│  [View my orders]                              │
└──────────────────────────────────────────────┘
```

### 16.3 `.streamlit/config.toml`
```toml
[server]
maxUploadSize = 5          # MB, matches FR-009
enableCORS = false
enableXsrfProtection = true

[theme]
primaryColor = "#1f6feb"
base = "light"
```

### 16.4 `requirements.txt`
```
streamlit>=1.36
sqlalchemy>=2.0
alembic>=1.13
pydantic[email]>=2.7
argon2-cffi>=23.1
python-dotenv>=1.0
pytest>=8.0
pytest-cov>=5.0
playwright>=1.44
pip-audit>=2.7
ruff>=0.5
mypy>=1.10
psycopg[binary]>=3.1   # prod Postgres
```

### 16.5 Sample `.env` keys (names only)
```
DB_URL=
SMTP_HOST=
SMTP_PORT=
SMTP_USER=
SMTP_PASSWORD=
SESSION_SIGNING_KEY=
INSTITUTION_DOMAIN=
MEDIA_ROOT=
```

---

## Final checklist
- [x] All source-doc requirements are represented and traceable (§15.1 maps every §3.3.1/§3.3.2 item to an FR/NFR and tests).
- [x] All features have acceptance criteria (GIVEN-WHEN-THEN) and telemetry (§4).
- [x] Python/Streamlit plan is production-ready: state (§9.3), caching (§9.4), secrets (§9.7), tests (§9.9), deploy (§13.2).
- [x] Security (§11), privacy (§11.4), accessibility (§6.3), and performance (§9.10/§10) targets specified.
- [x] Risks (§14.1), open questions, and owners (§15.2) listed.
