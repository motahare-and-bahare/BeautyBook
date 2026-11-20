# Software Requirements Specification (SRS)

**Product:** BeautyBook - Online Salon Marketplace
**Version:** 1.0 - Initial requirements baseline
**Date:** 2026-11-18
**Status:** Proposed. Product decisions in Section 13 must be confirmed before the affected
features are marked Ready.

---

## 1. Introduction

### 1.1 Purpose

This document defines the users, journeys, functional requirements, business rules, quality
requirements, and release scope for BeautyBook. It is the product-level source of truth used to
write feature specifications, implementation plans, and tests.

It intentionally separates **what the product must do** (this document) from **how the system is
built** (`docs/ARCHITECTURE.md`) and **when it is built** (`docs/ROADMAP.md`).

### 1.2 Product vision

Make it easy for people to find a trustworthy beauty or hair salon, understand what it offers and
what it costs, and reserve a suitable time online. Give salon owners a professional public page
and simple tools to manage services, availability, images, and appointments. Give platform
administrators the controls and audit trail needed to operate the marketplace safely.

### 1.3 Scope

BeautyBook is a multi-salon marketplace with a Vue 3 single-page frontend and a FastAPI modular
monolith backend. PostgreSQL is the main database. The first usable release covers:

- accounts, authentication, and three roles,
- salon profiles and public pages,
- services and prices,
- portfolio images,
- weekly working hours and unavailable periods,
- public availability display,
- booking with double-booking prevention,
- customer and salon-owner booking management,
- basic notifications,
- platform administration and audit.

Customer reviews, online payments, and advanced reporting are later phases.

### 1.4 Definitions

| Term | Meaning |
|---|---|
| **Salon** | A beauty or hair business with a public profile and bookable services. |
| **Salon Owner** | The user who manages a salon. In the MVP, each salon has one owner. |
| **Customer** | A user who books appointments. |
| **Administrator** | A privileged platform operator. |
| **Service** | A bookable offering with a name, duration, price, and optional buffers. |
| **Working hours** | Recurring weekly local-time windows during which a salon accepts appointments. |
| **Time off** | A date-specific period when a salon is unavailable. |
| **Slot** | A candidate appointment start time and the resulting service interval. |
| **Booking** | A persisted reservation with a lifecycle and a snapshot of its terms. |
| **Active booking** | A booking state that blocks its occupied time interval. |
| **Occupied interval** | The blocked time range, including service duration and pre/post buffers. |
| **Timezone** | An IANA identifier such as `Europe/Berlin`. |
| **Minor units** | The smallest currency unit, for example cents for EUR/USD. |
| **ADR** | Architecture Decision Record. |
| **SPEC / PLAN** | Feature-level requirements and implementation documents. |

---

## 2. Stakeholders and user classes

### 2.1 Customer

A person who wants to find a salon, compare services and prices, choose a valid time, book an
appointment, and manage it afterwards.

Needs:

- trustworthy salon information and photos,
- clear prices, durations, and policies,
- availability shown in an understandable timezone,
- a fast, mobile-friendly booking flow,
- confidence that the appointment is really reserved,
- simple cancellation and rescheduling.

### 2.2 Salon Owner

A person who owns or manages a salon and wants a professional public presence and control over
the salon's services, schedule, images, and appointments.

Needs:

- a public profile that looks credible,
- simple service and price management,
- flexible weekly hours and time-off handling,
- protection against double booking,
- a clear view of upcoming appointments,
- control over cancellation and rescheduling rules.

### 2.3 Administrator

A platform operator who manages users, salons, moderation, configuration, support cases, and
auditability.

Needs:

- safe user and salon management,
- the ability to suspend abusive or incorrect listings,
- platform-wide settings,
- searchable bookings for support,
- an audit trail of privileged actions.

### 2.4 Public visitor

A person who is not signed in. A visitor may browse published salons, services, prices, photos,
working hours, and advertised availability. Whether a visitor may complete a booking without an
account is an open decision (Section 13, Q1).

---

## 3. Assumptions and constraints

1. The first release supports **one salon per owner** and **one owner per salon**. Ownership
   transfer is an administrator action. This is an MVP simplification and an open decision
   (Section 13, Q4).
2. The first release models **capacity one per salon**: the salon can serve one appointment at a
   time. Multi-staff, rooms, and group appointments are out of scope until an approved feature
   adds them (Section 13, Q5).
3. Each salon has one IANA timezone used to interpret working hours.
4. Appointment instants are stored in UTC.
5. Prices are stored as integer minor units plus an ISO 4217 currency code. Floating point is
   forbidden for money.
6. The first release can operate without online payment. A booking does not require a deposit
   unless the payment feature is approved.
7. Email is the initial notification channel.
8. The backend is authoritative for permissions, pricing snapshots, availability, and booking
   state. The frontend is never a security boundary.
9. PostgreSQL is mandatory for the application database. SQLite is used only for fast, portable
   tests.
10. Accepted public image formats are initially JPEG, PNG, and WebP, subject to F-006.
11. The UI targets modern desktop, tablet, and mobile browsers. Exact browser support is confirmed
    in F-001.
12. Customer reviews are a future phase. They must not be implemented early.
13. The platform is initially single-region. Multi-region active-active deployment is out of
    scope.
14. All legal/privacy claims require separate review. This SRS does not assert legal compliance.

---

## 4. User journeys

### 4.1 Customer journey: discover and book

1. The customer opens BeautyBook.
2. The customer browses or searches published salons by name, city, or service.
3. The customer filters results by city, service category, price range, or availability.
4. The customer opens a salon profile and reviews:
   - name, description, address, and contact details,
   - photos and portfolio,
   - services, durations, and prices,
   - working hours and advertised availability.
5. The customer selects a service.
6. The platform displays available slots, clearly stating the timezone used.
7. The customer selects a slot and provides the required booking details.
8. The customer signs in or registers. Guest booking is allowed only if the product decision
   enables it.
9. The platform shows a final summary: salon, service, start/end time, timezone, price, currency,
   and cancellation policy.
10. The customer confirms.
11. The backend revalidates the slot and atomically creates the booking.
12. The customer sees a confirmation with a booking reference.
13. The customer can view the booking in their dashboard and receives an email confirmation.

**Alternative and failure paths:**

- The slot becomes unavailable before confirmation: show a clear conflict message and refresh the
  slots. Do not create a duplicate booking.
- The customer loses connection after submitting: retry with the same idempotency key and return
  the original result.
- Validation fails: preserve safe input and show field-level errors.
- The salon requires approval (if enabled): show a pending status and explain the next step.
- Email delivery fails: the booking remains valid; retry delivery asynchronously.
- The salon is suspended or unpublished: stop the booking flow and explain that the salon is not
  currently accepting appointments.

### 4.2 Customer journey: manage a booking

1. The customer opens "My bookings".
2. The customer sees upcoming and past bookings, with status and local time.
3. The customer opens a booking and sees the service snapshot, price, salon contact details, and
   policy.
4. The customer may cancel within the allowed window.
5. The customer may reschedule if the policy allows it.
6. The platform validates the request, updates the booking transactionally, and records the
   change.
7. The customer and salon are notified.
8. The customer sees the updated booking.

**Alternative and failure paths:**

- The cancellation cutoff has passed: reject with an explanation and, if applicable, salon
  contact information.
- The new slot is taken: keep the original booking unchanged and show alternatives.
- The booking is already cancelled or completed: show the terminal state and prevent duplicate
  actions.

### 4.3 Salon owner journey: apply, get approved, and publish

1. The owner applies through the dedicated salon-owner registration form and enters personal details
   plus basic salon information (salon name, city, phone, timezone, currency).
2. The system creates a **pending** account and a **pending** salon application. The applicant is
   not signed in and does not yet hold the salon-owner role.
3. An administrator reviews the application and approves or rejects it with a reason.
4. On approval, the account becomes active, the salon-owner role is granted, and the owner can sign
   in to the salon dashboard.
5. The owner completes the salon profile:
   - full address and unique public slug,
   - description and contact details,
   - optional logo/cover image.
6. The owner adds services with duration, price, optional description, and optional buffers.
7. The owner defines weekly working hours, including lunch breaks or split shifts.
8. The owner adds time off for holidays and other unavailable periods.
9. The owner uploads portfolio images and sets a cover photo.
10. The owner previews the public salon page and availability.
11. The owner publishes the salon. Approval unlocks the dashboard; it does not publish the salon.
12. The owner receives booking notifications and manages appointments.

**Alternative and failure paths:**

- The email already belongs to a customer or another owner: reject the application and point the
  person to sign-in support. Applying as an existing customer is a later feature.
- The application is rejected: the account remains unable to sign in, and the reason is stored for
  support. Re-application is a later feature.
- The slug is already taken: suggest alternatives and require a unique value.
- Working hours overlap or are invalid: explain the conflict and refuse to save.
- The owner tries to block time that overlaps an existing booking: require an explicit resolution
  workflow; never silently invalidate the appointment.
- An uploaded file is not a valid image or is too large: reject it with a clear message.
- The salon is suspended by an administrator: public booking is disabled; existing bookings follow
  the documented support policy.

### 4.4 Salon owner journey: manage appointments

1. The owner opens the appointment dashboard.
2. The owner filters by date, status, or service.
3. The owner opens an appointment and sees the permitted customer details and booking history.
4. The owner confirms or rejects a pending request, if approval mode is enabled.
5. The owner may cancel or reschedule according to policy.
6. The platform validates the transition, records it, and notifies the customer.
7. The dashboard updates.

### 4.5 Administrator journey: operate the platform

1. The administrator signs in with a protected account.
2. The administrator sees an operational overview.
3. The administrator searches and filters users and salons.
4. The administrator reviews salon-owner applications and approves or rejects them with a reason,
   then reviews salons and approves, suspends, or requests changes.
5. The administrator manages roles and account status. Only an administrator can assign the
   administrator role, and no public registration path can create one.
6. The administrator configures platform-wide settings such as support contact, default policies,
   enabled features, and allowed currencies.
7. The administrator manages service categories.
8. The administrator searches bookings for support and views audit history.
9. The administrator performs controlled booking interventions with a mandatory reason.
10. The administrator's actions are recorded in an audit log.

**Alternative and failure paths:**

- An action is outside the administrator's permission: deny it and log the security-relevant
  event.
- A destructive action would affect bookings: require confirmation and prefer deactivation or
  archival over deletion.
- Sensitive data is requested: disclose only the minimum authorized information.

---

## 5. Functional requirements

Priority notation: **Must** = required for the first usable release; **Should** = planned shortly
after; **Could** = optional/later.

### 5.1 Shared identity and account requirements

- **FR-IAM-001 (Must):** The system shall support two separate public registration journeys: a
  customer journey that creates an active customer account, and a salon-owner journey that creates
  a pending account and a pending salon application.
- **FR-IAM-002 (Must):** The system shall verify email ownership before enabling sensitive account
  actions.
- **FR-IAM-003 (Must):** The system shall support secure sign-in and sign-out.
- **FR-IAM-004 (Must):** The system shall support password reset using a short-lived, single-use
  token.
- **FR-IAM-005 (Must):** A user shall be able to view and update permitted profile fields.
- **FR-IAM-006 (Must):** A user shall be able to change their password after re-authentication or
  equivalent protection.
- **FR-IAM-007 (Must):** The system shall enforce role permissions and resource ownership on the
  server for every protected operation.
- **FR-IAM-008 (Must):** The system shall rate-limit registration, login, and password-reset
  requests.
- **FR-IAM-009 (Should):** The system should support account deactivation and reactivation under a
  defined policy.
- **FR-IAM-010 (Should):** The system should support account data export and deletion workflows,
  subject to legal and booking-retention requirements.
- **FR-IAM-011 (Must):** The system shall revoke a session on sign-out and provide a way to revoke
  other sessions after a password change.
- **FR-IAM-012 (Must):** A pending or rejected salon-owner account shall not be able to
  authenticate and shall not hold the salon-owner role.
- **FR-IAM-013 (Must):** Administrator accounts shall never be creatable through public
  registration. The first administrator shall be provisioned out-of-band, and later administrators
  shall be created or assigned only by an authorized administrator.

### 5.2 Customer requirements

- **FR-CUS-001 (Must):** A customer shall be able to browse published salon profiles.
- **FR-CUS-002 (Must):** A customer shall be able to view a salon's name, description, address,
  contact details, photos, working hours, services, durations, and prices.
- **FR-CUS-003 (Must):** A customer shall be able to search salons by name and city, and search or
  filter by service.
- **FR-CUS-004 (Should):** A customer shall be able to filter salons by city, service category,
  price range, and availability.
- **FR-CUS-005 (Must):** A customer shall be able to compare services and prices across salons.
- **FR-CUS-006 (Must):** A customer shall be able to view available appointment slots for a
  selected service.
- **FR-CUS-007 (Must):** The system shall display the timezone used to interpret appointment times
  and working hours.
- **FR-CUS-008 (Must):** The system shall show a final booking summary before confirmation,
  including salon, service, start/end time, timezone, price, currency, and cancellation policy.
- **FR-CUS-009 (Must):** A customer shall be able to create a booking with the required details.
- **FR-CUS-010 (Must):** The system shall revalidate availability at booking submission and prevent
  overlapping active bookings.
- **FR-CUS-011 (Must):** The system shall return a clear, stable conflict response when a slot is no
  longer available.
- **FR-CUS-012 (Must):** A customer shall be able to view their own upcoming and past bookings.
- **FR-CUS-013 (Must):** A customer shall be able to view the details and status of their own
  bookings.
- **FR-CUS-014 (Must):** A customer shall be able to cancel their own booking within the applicable
  policy.
- **FR-CUS-015 (Must):** A customer shall be able to reschedule their own booking within the
  applicable policy.
- **FR-CUS-016 (Should):** A customer shall be able to set a preferred timezone and notification
  preferences.
- **FR-CUS-017 (Could):** The system could support guest booking, subject to abuse prevention and
  account-claim rules.
- **FR-CUS-018 (Could):** The system could support saved/favorite salons.
- **FR-CUS-019 (Could):** A customer could review a salon after a completed appointment (future
  phase).

### 5.3 Salon profile and owner requirements

- **FR-SAL-001 (Must):** A user shall be able to apply to become a salon owner through the
  dedicated salon-owner registration flow, submitting personal details and basic salon information.
- **FR-SAL-001a (Must):** A salon-owner account and its application shall remain pending until an
  administrator approves them; approval grants the salon-owner role and dashboard access but does
  not publish the salon.
- **FR-SAL-002 (Must):** A salon owner shall be able to create and edit their own salon profile.
- **FR-SAL-003 (Must):** A salon shall have a unique public slug.
- **FR-SAL-004 (Must):** A salon owner shall be able to set the salon's IANA timezone and currency.
- **FR-SAL-005 (Must):** A salon owner shall be able to set the salon's name, description, address,
  phone number, and public contact email.
- **FR-SAL-006 (Must):** A salon owner shall be able to preview and publish or unpublish their
  salon, subject to the onboarding/approval decision.
- **FR-SAL-007 (Must):** Only published, non-suspended salons and their active services shall be
  publicly visible.
- **FR-SAL-008 (Must):** A salon owner shall be able to upload, reorder, and delete portfolio
  images that belong to their salon.
- **FR-SAL-009 (Must):** A salon owner shall be able to set one image as the salon's cover photo.
- **FR-SAL-010 (Must):** A salon owner shall be able to view appointments assigned to their salon.
- **FR-SAL-011 (Must):** A salon owner shall be able to confirm or reject a pending booking when
  approval mode is enabled.
- **FR-SAL-012 (Must):** A salon owner shall be able to cancel or reschedule an appointment
  according to policy, with a recorded reason.
- **FR-SAL-013 (Must):** A salon owner shall be able to view the customer's booking details to the
  extent required to deliver the service, while respecting privacy rules.
- **FR-SAL-014 (Should):** A salon owner shall be able to configure minimum booking notice,
  booking horizon, slot interval, and cancellation cutoff.
- **FR-SAL-015 (Should):** A salon owner shall be able to view basic booking counts and upcoming
  workload.
- **FR-SAL-016 (Could):** A salon owner could manage multiple staff members and assign services to
  them.
- **FR-SAL-017 (Could):** A salon owner could configure custom intake questions for a service.

### 5.4 Service and pricing requirements

- **FR-SVC-001 (Must):** A salon owner shall be able to create, edit, activate, deactivate,
  archive, and remove services from the public catalogue.
- **FR-SVC-002 (Must):** A service shall include a name, duration in minutes, price in integer
  minor units in the salon's ISO 4217 currency, and active state.
- **FR-SVC-003 (Must):** A service shall support an optional description and optional pre/post
  buffers.
- **FR-SVC-004 (Must):** The system shall reject non-positive durations and negative prices.
- **FR-SVC-005 (Must):** Removing a service from the catalogue shall be a soft removal when the
  service is referenced by a booking, and shall never delete historical bookings.
- **FR-SVC-006 (Must):** A service price or duration change shall not alter the snapshot of an
  existing booking.
- **FR-SVC-007 (Must):** A service shall belong to exactly one salon, and an owner shall not be able
  to modify another salon's service.
- **FR-SVC-008 (Should):** The system should support a service category or tag for search and
  filtering.
- **FR-SVC-009 (Could):** The system could support service variants and add-ons.

### 5.5 Portfolio and image requirements

- **FR-IMG-001 (Must):** The system shall accept JPEG, PNG, and WebP uploads, subject to size and
  content validation.
- **FR-IMG-002 (Must):** The system shall validate the actual file content, not only the filename
  extension or client-provided MIME type.
- **FR-IMG-003 (Must):** The system shall enforce a maximum upload size and a maximum number of
  images per salon.
- **FR-IMG-004 (Must):** The system shall store uploaded files outside the web root with random,
  non-guessable names.
- **FR-IMG-005 (Must):** The system shall prevent path traversal and shall never trust a
  client-supplied storage path.
- **FR-IMG-006 (Must):** Only the owning salon shall be able to add, reorder, or delete its images.
- **FR-IMG-007 (Must):** The system shall store alt text for each image for accessibility.
- **FR-IMG-008 (Must):** Deleting an image shall remove it from public display without corrupting
  unrelated records.
- **FR-IMG-009 (Should):** The system should strip unnecessary metadata, including location EXIF,
  before public serving.
- **FR-IMG-010 (Should):** The system should generate reasonably sized variants for the public
  profile rather than serving full-resolution originals.

### 5.6 Working hours and availability requirements

- **FR-AVL-001 (Must):** A salon owner shall be able to define recurring weekly working hours in
  the salon's local timezone.
- **FR-AVL-002 (Must):** The system shall support multiple working intervals per day, for example
  a morning and an afternoon shift separated by a lunch break.
- **FR-AVL-003 (Must):** A salon owner shall be able to define date-specific time off and
  unavailable periods.
- **FR-AVL-004 (Must):** The system shall reject invalid or overlapping working-hour configuration
  for the same day.
- **FR-AVL-005 (Must):** The platform shall generate candidate slots using the service duration,
  pre/post buffers, slot interval, minimum notice, and booking horizon.
- **FR-AVL-006 (Must):** The platform shall exclude times covered by time off, closures, or active
  bookings.
- **FR-AVL-007 (Must):** The availability API shall return UTC instants plus the salon timezone and
  enough local information for display.
- **FR-AVL-008 (Must):** The system shall define and test daylight-saving behavior for nonexistent
  and ambiguous local times.
- **FR-AVL-009 (Must):** A closed day or fully unavailable day shall produce no slots.
- **FR-AVL-010 (Must):** Availability shown publicly is advisory and does not reserve a slot.
- **FR-AVL-011 (Must):** A salon owner shall be able to preview availability for a date range.

### 5.7 Booking requirements

- **FR-BKG-001 (Must):** A booking shall reference one customer, one salon, and one service.
- **FR-BKG-002 (Must):** A booking shall store start and end instants in UTC.
- **FR-BKG-003 (Must):** A booking shall store the occupied interval, including service buffers.
- **FR-BKG-004 (Must):** A booking shall preserve a snapshot of the service name, duration, price,
  currency, salon timezone, and applicable cancellation policy at creation time.
- **FR-BKG-005 (Must):** The system shall use half-open intervals `[start, end)` for overlap
  semantics.
- **FR-BKG-006 (Must):** The system shall prevent overlapping active bookings for the same salon
  when capacity is one.
- **FR-BKG-007 (Must):** Booking creation shall be transactional and safe under concurrent
  requests.
- **FR-BKG-008 (Must):** Booking creation shall support an idempotency key so client retries do not
  create duplicates.
- **FR-BKG-009 (Must):** Booking states and legal transitions shall be explicitly defined.
- **FR-BKG-010 (Must):** The system shall retain an append-only history of important booking state
  transitions.
- **FR-BKG-011 (Must):** A pending approval request, if enabled, shall block its interval for a
  configured expiry period.
- **FR-BKG-012 (Must):** Rescheduling shall preserve history and maintain reservation integrity.
- **FR-BKG-013 (Must):** Cancellation shall support a reason and policy-based eligibility.
- **FR-BKG-014 (Must):** Salon deactivation or service archival shall not delete historical
  bookings.
- **FR-BKG-015 (Must):** The booking command shall revalidate availability inside the authoritative
  database transaction, regardless of what the availability endpoint returned.
- **FR-BKG-016 (Must):** Booking creation shall respect minimum notice, booking horizon, slot
  alignment, working hours, and time off.

### 5.8 Customer dashboard requirements

- **FR-DSH-001 (Must):** A customer shall see upcoming bookings sorted by start time.
- **FR-DSH-002 (Must):** A customer shall see past and cancelled bookings with clear status labels.
- **FR-DSH-003 (Must):** A customer shall be able to open a booking and view its snapshot and
  history.
- **FR-DSH-004 (Must):** A customer shall be able to cancel an eligible booking.
- **FR-DSH-005 (Should):** A customer shall be able to reschedule an eligible booking.
- **FR-DSH-006 (Must):** A customer shall be able to update their profile and preferred timezone.
- **FR-DSH-007 (Must):** The dashboard shall show loading, empty, error, and success states.

### 5.9 Salon owner dashboard requirements

- **FR-ODS-001 (Must):** A salon owner shall see today's and upcoming appointments for their salon.
- **FR-ODS-002 (Must):** A salon owner shall be able to filter appointments by date, status, and
  service.
- **FR-ODS-003 (Must):** A salon owner shall be able to open an appointment and view permitted
  customer details.
- **FR-ODS-004 (Must):** A salon owner shall be able to confirm or reject pending appointments when
  approval mode is enabled.
- **FR-ODS-005 (Must):** A salon owner shall be able to cancel or reschedule with a recorded
  reason and policy validation.
- **FR-ODS-006 (Must):** A salon owner shall see the effect of schedule changes on existing
  appointments.
- **FR-ODS-007 (Should):** A salon owner shall see basic summary counts (upcoming, completed,
  cancelled).

### 5.10 Administrator requirements

- **FR-ADM-001 (Must):** The system shall provide a protected administrator interface.
- **FR-ADM-002 (Must):** An administrator with the required permission shall be able to search,
  view, activate, suspend, and deactivate user accounts.
- **FR-ADM-003 (Must):** An administrator shall be able to review salon-owner applications and
  approve or reject them with a recorded reason.
- **FR-ADM-004 (Must):** The system shall record the actor, timestamp, action, target, and reason
  for privileged administrative actions.
- **FR-ADM-005 (Must):** An administrator shall be able to manage role assignments according to
  least privilege. Only an administrator may grant the administrator role; no public registration
  path may create one.
- **FR-ADM-006 (Must):** An administrator shall be able to configure platform-wide settings.
- **FR-ADM-007 (Should):** An administrator shall be able to manage service categories and public
  taxonomy.
- **FR-ADM-008 (Must):** An administrator shall be able to search and inspect bookings for support,
  subject to permissions.
- **FR-ADM-009 (Should):** An administrator shall be able to perform controlled booking
  interventions with a mandatory reason and audit record.
- **FR-ADM-010 (Should):** An administrator shall be able to configure global defaults for
  cancellation, booking horizon, and notification policy.
- **FR-ADM-011 (Should):** An administrator shall be able to view operational metrics such as
  registrations, salons, bookings, cancellations, and notification failures.
- **FR-ADM-012 (Could):** An administrator could export filtered reports in CSV format.
- **FR-ADM-013 (Should):** An administrator shall be able to manage announcements and support
  contact details.
- **FR-ADM-014 (Must):** The system shall prevent an administrator from irreversibly deleting
  records required for booking or audit integrity.

### 5.11 Notification requirements

- **FR-NTF-001 (Must):** The system shall send email-verification and password-reset messages.
- **FR-NTF-002 (Must):** The system shall send booking-created, confirmed, cancelled, and
  rescheduled messages as applicable.
- **FR-NTF-003 (Must):** The system shall notify the salon owner of new and cancelled bookings.
- **FR-NTF-004 (Must):** Notification delivery failure shall not roll back a committed booking.
- **FR-NTF-005 (Must):** Notification work shall be retryable and deduplicated.
- **FR-NTF-006 (Should):** The system should send appointment reminders at configurable intervals.
- **FR-NTF-007 (Must):** Notification payloads shall not include unnecessary personal data.

### 5.12 Review requirements (future phase)

These requirements are recorded for traceability but are **out of scope** for the first usable
release. They must not be implemented before F-015 is Ready.

- **FR-REV-001 (Could):** A customer with a completed booking could submit one review for that
  booking.
- **FR-REV-002 (Could):** A review could contain a 1-5 rating and optional text.
- **FR-REV-003 (Could):** A salon owner could reply to a review.
- **FR-REV-004 (Could):** A salon's public page could show an aggregate rating and review count.
- **FR-REV-005 (Could):** An administrator could hide or remove reviews that violate policy, with
  an audit record.
- **FR-REV-006 (Could):** Reviews could be moderated before publication, according to the product
  decision.

---

## 6. Business rules

- **BR-001:** A salon owner can manage only their own salon, services, images, working hours, time
  off, and appointments.
- **BR-002:** A customer can access only their own private booking data.
- **BR-003:** Public visitors can access only published, non-suspended salon data and active
  services.
- **BR-004:** An appointment interval is half-open `[start, end)`.
- **BR-005:** A slot is not guaranteed until the booking transaction commits.
- **BR-006:** Only blocking states occupy time. Terminal states do not block availability.
- **BR-007:** For capacity one, active bookings for the same salon must not overlap, including
  buffers.
- **BR-008:** Recurring working hours are interpreted in the salon's IANA timezone.
- **BR-009:** Appointment instants are persisted in UTC.
- **BR-010:** Daylight-saving ambiguous and nonexistent local times follow an explicit documented
  policy and are covered by tests.
- **BR-011:** Money is stored as integer minor units plus an ISO 4217 currency code, never binary
  floating point.
- **BR-012:** A booking preserves a snapshot of service name, duration, price, currency, salon
  timezone, and applicable policy.
- **BR-013:** A pending approval booking, if enabled, blocks the selected interval until decision
  or expiry.
- **BR-014:** External email, storage, and payment calls do not occur inside the booking database
  transaction.
- **BR-015:** Administrative actions affecting accounts, salons, bookings, or platform policy are
  audited.
- **BR-016:** A salon's public slug is unique and case-insensitive.
- **BR-017:** A service must have a positive duration and a non-negative price.
- **BR-018:** A booking's occupied interval includes its pre/post buffers.
- **BR-019:** Changing a service or salon must not rewrite historical booking snapshots.
- **BR-020:** Deactivation, suspension, or archiving must not cascade-delete bookings or audit
  records.
- **BR-021:** Uploaded images must pass content validation before being stored or served.
- **BR-022:** An inactive or unpublished salon cannot receive new bookings.
- **BR-023:** An idempotent retry with the same key and same request returns the original result; a
  different request with the same key is rejected.
- **BR-024:** Reviews, if later enabled, require a completed booking and follow the moderation
  policy.

---

## 7. Data requirements

Core entities are described in `docs/ARCHITECTURE.md`. At minimum:

- `users`, `user_roles`, `sessions`
- `email_verification_tokens`, `password_reset_tokens`
- `salons`, `salon_photos`
- `services`
- `working_hours`, `time_off`
- `bookings`, `booking_events`
- `outbox_messages`
- `audit_logs`
- `platform_settings`
- `reviews` (future phase only)

Data requirements:

- Enforce referential integrity with foreign keys.
- Use unique constraints for normalized email, salon slug, idempotency scope/key, and natural
  uniqueness rules.
- Use check constraints for positive durations, non-negative prices, valid statuses, valid
  weekdays, and valid intervals.
- Use indexes for common lookups: salon + time range, customer + time range, salon + status,
  service + active state, city + published state.
- Store images outside the database; store only validated metadata and storage keys.
- Define retention and deletion rules before production.
- Do not cascade-delete bookings, booking history, or audit records when a user, salon, or service
  is deactivated.
- Keep currency consistent within a salon unless a future feature explicitly supports multiple
  currencies.

---

## 8. External interface requirements

### 8.1 User interface

- Responsive web UI for desktop, tablet, and mobile.
- Mobile-first layout for the customer booking flow.
- Required states: loading, empty, validation error, conflict, success, and recoverable error.
- Accessible forms, labels, focus states, and error messages.
- Clear timezone display wherever a time is shown.

### 8.2 API

- REST API under `/api/v1`.
- Documented by OpenAPI, generated by FastAPI.
- Explicit request and response schemas; no raw ORM objects.
- ISO 8601 timestamps. Instants include a UTC offset or `Z`; IANA timezone identifiers are
  represented separately.
- Consistent error envelope and stable error codes.
- Pagination on list endpoints.
- Idempotency keys for booking creation.

### 8.3 Email

- Email adapter supports templated messages and delivery status tracking.
- The concrete provider is selected in F-003/F-013 and documented.
- Email content must not leak unnecessary personal data.

### 8.4 Image storage

- Local development may use a filesystem adapter.
- Production should use S3-compatible object storage or an equivalent durable service.
- The concrete choice is recorded in ADR-0006 and implemented in F-006.
- Files are served through a controlled endpoint or a storage origin, never from the application's
  source tree.

### 8.5 Payments and calendars

Optional integrations are out of scope for the first usable release and require their own SPEC,
PLAN, threat review, and ADR before implementation.

---

## 9. Non-functional requirements

- **NFR-SEC-001:** All protected operations shall enforce backend authorization and ownership
  checks.
- **NFR-SEC-002:** Passwords shall be stored with Argon2id via a maintained library.
- **NFR-SEC-003:** Authentication, password reset, public availability, and booking endpoints shall
  be rate-limited.
- **NFR-SEC-004:** Secrets and sensitive personal data shall not be written to logs.
- **NFR-SEC-005:** State-changing cookie-authenticated requests shall be protected against CSRF.
- **NFR-SEC-006:** Uploaded files shall be validated by content, size, and type before storage.
- **NFR-REL-001:** A committed booking shall remain committed even if email delivery fails.
- **NFR-REL-002:** Booking creation shall be safe under concurrent attempts and client retries.
- **NFR-REL-003:** A migration failure shall leave the database in a known state; rollback
  procedures shall be documented.
- **NFR-PERF-001:** Initial target: p95 under 500 ms for ordinary API calls under an agreed test
  load, excluding external provider latency.
- **NFR-PERF-002:** Availability endpoint latency shall be benchmarked with representative
  schedules and booking volume.
- **NFR-SCALE-001:** The modular monolith shall support horizontal application scaling without
  relying on in-process session state.
- **NFR-MAINT-001:** Code changes shall include automated tests and relevant documentation.
- **NFR-MAINT-002:** Database changes shall be managed through Alembic migrations.
- **NFR-MAINT-003:** Backend code shall pass formatting, linting, and type checking configured in
  F-001.
- **NFR-MAINT-004:** Frontend code shall pass formatting, linting, type checking, and Vitest.
- **NFR-OBS-001:** The system shall provide structured logs, request IDs, health checks, and
  metrics for critical operations.
- **NFR-BCP-001:** Production shall have documented backups and tested restore procedures.
- **NFR-ACC-001:** The UI shall target WCAG 2.2 AA.
- **NFR-PRIV-001:** The platform shall minimize personal data and define retention, export, and
  deletion procedures.
- **NFR-COMP-001:** The system shall not claim legal compliance without a documented review.

Targets are provisional until load, availability, and recovery requirements are agreed.

---

## 10. Acceptance criteria for the first usable release

1. A customer can register, verify their email, sign in, and sign out.
2. A salon owner can apply, be approved by an administrator, sign in, complete a salon profile, add
   services, set working hours, add time off, upload photos, and publish the salon.
3. A customer can find a published salon, inspect an active service, view available slots, and
   create a booking.
4. The booking summary shows the salon timezone, local time, UTC instant, price, currency, and
   cancellation policy.
5. A customer can view their own booking and cannot access another customer's booking.
6. A salon owner can view only their own salon's bookings and cannot access another salon's data.
7. An administrator can approve or suspend a salon and manage users, with every privileged action
   audited.
8. Two simultaneous requests for the same overlapping salon interval result in exactly one active
   booking; the other receives a clear conflict response.
9. A retry with the same idempotency key does not create a duplicate booking.
10. Times display correctly across salon/customer timezones and across daylight-saving boundaries.
11. A customer can cancel or reschedule a booking within policy; a cancelled slot becomes
    available again.
12. A salon owner can cancel or reschedule with a recorded reason, and the customer sees the
    change.
13. Booking confirmation email is queued; a delivery failure does not invalidate the booking.
14. Backend tests pass on PostgreSQL, including the concurrency suite.
15. Frontend tests and critical browser end-to-end journeys pass.
16. Migrations can upgrade a clean PostgreSQL database and the previous supported schema.
17. No known critical or high security issue remains open.

---

## 11. Out of scope for the first usable release

Unless explicitly approved through the feature process:

- Multiple staff members per salon, rooms, equipment, or capacity greater than one.
- Group sessions and classes.
- Marketplace commissions, salon payouts, and subscriptions.
- Online payments and deposits (planned as F-016).
- Customer reviews and ratings (planned as F-015).
- Native mobile applications.
- Video conferencing.
- SMS and push notifications.
- External calendar synchronization.
- Advanced CRM or marketing automation.
- AI recommendations or conversational booking.
- Multi-region active-active deployment.
- Event sourcing, CQRS, and microservices.
- Advanced analytics or a data warehouse.

---

## 12. Traceability to the feature backlog

| Requirement area | Backlog task |
|---|---|
| Documentation baseline | F-000 |
| Authentication and minimal foundation | F-001 |
| Authorization and ownership policies | F-002 |
| Account lifecycle and profile | F-003 |
| Salon profile and public page | F-004 |
| Services and pricing | F-005 |
| Portfolio and images | F-006 |
| Working hours and availability | F-007 |
| Public discovery and comparison | F-008 |
| Booking core and concurrency | F-009 |
| Customer dashboard | F-010 |
| Salon owner dashboard | F-011 |
| Cancellation and rescheduling | F-012 |
| Notifications and reminders | F-013 |
| Administration and audit | F-014 |
| Reviews (future) | F-015 |
| Payments (future) | F-016 |
| Reporting (future) | F-017 |
| Production readiness | F-018 |

---

## 13. Product decisions requiring confirmation

These decisions must be resolved before the affected feature is marked Ready:

1. **Guest booking:** Must every customer create an account, or can a visitor book and claim the
   booking later? (Blocks F-009.)
2. **Salon onboarding:** *Resolved 2026-11-18.* Salon owners use a dedicated registration flow;
   their account and application stay pending until an administrator approves them. Approval
   unlocks the dashboard but does not publish the salon. See F-001 SPEC and ADR-0010. (Still open:
   the exact review service level and the existing-customer application path, F-004/F-013/F-014.)
3. **Booking mode:** Instant confirmation, owner approval, or configurable per salon/service?
   (Blocks F-009/F-011.)
4. **Salon ownership model:** Is one salon per owner and one owner per salon acceptable for the
   first release? (Blocks F-004.)
5. **Capacity:** Is one appointment per salon at a time acceptable, or are staff/resources required
   immediately? (Blocks F-007/F-009.)
6. **Countries, currencies, and languages:** Which launch market(s) and which currency/locale
   defaults? (Blocks F-001/F-004.)
7. **Cancellation and no-show policy:** What are the default and owner-overridable rules? (Blocks
   F-012.)
8. **Booking rules:** What are the default booking horizon, minimum notice, slot granularity, and
   pending-request expiry? (Blocks F-007/F-009.)
9. **Payment:** Is a deposit or full payment required in the first release? (Blocks F-016 scope.)
10. **Image storage:** Which production storage provider will be used? (Blocks F-006.)
11. **Email provider:** Which transactional email provider and sender identity? (Blocks F-013.)
12. **Reviews:** When will reviews be enabled, and are they pre-moderated? (Blocks F-015.)
13. **Search location:** Is city-based search sufficient, or is geocoding/radius search required?
    (Blocks F-008.)
14. **Overnight hours:** Must salons be able to define working hours that cross midnight? (Blocks
    F-007.)
15. **Languages:** Is the first release English-only? (Blocks F-001/F-004.)

When a decision is made, record it in the relevant feature SPEC and, if it is architectural, in an
ADR. Do not leave a decision implicit in code.
