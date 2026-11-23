# Software Requirements Specification (SRS) — BeautyBook

**Product:** BeautyBook — Online Salon Marketplace
**Document path:** `SRS.md` (project root, consolidated copy)
**Version:** 1.1-consolidated
**Date:** 2026-11-23
**Status:** Proposed for approval. Section 13 contains a senior engineering review of this document.
**Approved baseline:** `docs/SRS.md` v1.0 (2026-11-18) remains the approved product source of truth
until this consolidated document is approved **and** the duplication described in finding
`SR-01` is resolved.
**Owner:** Project owner (product decisions)
**Audience:** product owner, backend and frontend engineers, QA, operations, security reviewer

---

## 0. How to read this document

1. Sections 1–12 are **normative**: they state what the product must do. They restate and
   consolidate the approved baseline in `docs/SRS.md` v1.0, adding a per-user capability
   catalogue (Section 3) and the localization requirements already implemented in F-019
   (Section 4.12).
2. Section 13 is a **review**, not a requirement. It records weaknesses found in this document and
   in the baseline, with severity, rationale, and concrete improvements. Nothing in Section 13 is
   approved until it is turned into a feature `SPEC.md` and approved.
3. Where this document and `docs/SRS.md` disagree, `docs/SRS.md` wins until the project owner
   explicitly approves this file as the replacement. This rule exists because two documents that
   both claim to be authoritative are worse than one imperfect document (`SR-01`).

### 0.1 Relationship to the other project documents

| Document | Answers | Status |
|---|---|---|
| `SRS.md` (this file) | **What** must the product do, for whom | Proposed consolidated copy |
| `docs/SRS.md` | **What** must the product do (approved v1.0) | Approved baseline |
| `docs/ARCHITECTURE.md` | **How** the system is built | Approved |
| `docs/ROADMAP.md` | **When** it is built | Approved |
| `docs/adr/` | **Why** a technical decision was made | Accepted records |
| `Task-List.md` | **Who** builds what, in which order | Delivery queue |
| `docs/features/<ID>/SPEC.md`, `PLAN.md` | Feature-level detail and test plan | Per feature |
| `AGENTS.md` | Engineering rules that constrain all of the above | Mandatory |

### 0.2 Requirement status legend

| Priority | Meaning |
|---|---|
| **Must** | Required for the first usable release. Absence blocks release. |
| **Should** | Planned shortly after the first release; may slip with a recorded decision. |
| **Could** | Optional or later phase; must not be implemented early without an approved feature. |
| **Implemented** | Already built and verified; still requires a ratified requirement (see F-019). |

---

## 1. Introduction

### 1.1 Purpose

This document defines the users, their capabilities, the user journeys, the functional
requirements, the business rules, the data and interface requirements, the quality attributes, and
the release scope of BeautyBook. It is the input to feature specifications (`SPEC.md`),
implementation plans (`PLAN.md`), and tests.

It deliberately separates **what the product must do** (this document) from **how** it is built
(`docs/ARCHITECTURE.md`) and **when** (`docs/ROADMAP.md`).

### 1.2 Product vision

Make it easy for people to find a trustworthy beauty or hair salon, understand what it offers and
what it costs, and reserve a suitable time online. Give salon owners a professional public page and
simple tools to manage services, availability, images, and appointments. Give platform
administrators the controls and audit trail needed to operate the marketplace safely.

Success for the first release means: a customer can complete a real booking without help, a salon
owner can run their day from the dashboard, and an administrator can resolve abuse and support
cases without direct database access.

### 1.3 Scope of the first usable release

BeautyBook is a multi-salon marketplace with a Vue 3 single-page frontend and a FastAPI **modular
monolith** backend. PostgreSQL is the application database.

In scope:

- accounts, authentication, email verification, password reset, and three roles;
- salon-owner application and administrator approval;
- salon profiles and public pages with a unique slug;
- services, durations, prices, and optional buffers;
- portfolio images with content validation;
- recurring weekly working hours and date-specific time off;
- public availability display in the salon timezone;
- booking with authoritative double-booking prevention and idempotency;
- customer and salon-owner booking management, cancellation, rescheduling;
- transactional email through an outbox;
- platform administration, platform settings, and an audit trail;
- Persian / right-to-left presentation of the authentication screens (F-019).

Out of scope for the first release is enumerated in Section 10.

### 1.4 Definitions

| Term | Meaning |
|---|---|
| **Salon** | A beauty or hair business with a public profile and bookable services. |
| **Salon owner** | The user who manages a salon. In the MVP each salon has exactly one owner. |
| **Customer** | A user who books appointments. |
| **Administrator** | A privileged platform operator. |
| **Public visitor** | A person who is not signed in. |
| **Service** | A bookable offering with a name, duration, price, and optional buffers. |
| **Working hours** | Recurring weekly local-time windows during which a salon accepts appointments. |
| **Time off** | A date-specific period when a salon is unavailable. |
| **Slot** | A candidate appointment start time and the resulting service interval. |
| **Booking** | A persisted reservation with a lifecycle and a snapshot of its terms. |
| **Occupied interval** | The blocked time range: service duration plus pre/post buffers. |
| **Active booking** | A booking state that blocks its occupied time interval. |
| **Timezone** | An IANA identifier such as `Asia/Tehran` or `Europe/Berlin`. |
| **Minor units** | The smallest currency unit, for example cents for EUR/USD or rial for IRR. |
| **Idempotency key** | A client-supplied key that makes a retried command return the original result. |
| **Outbox** | A database table of pending side effects (email) written in the same transaction as the business change. |
| **ADR** | Architecture Decision Record. |
| **SPEC / PLAN** | Feature-level requirements and implementation documents. |

---

## 2. Stakeholders

| Stakeholder | Interest | Influence |
|---|---|---|
| Customer | Find and book a salon quickly; keep or cancel the appointment | High (revenue) |
| Salon owner | Fill the calendar; avoid double booking; look credible | High (supply) |
| Administrator | Operate the marketplace safely and accountably | High (risk) |
| Public visitor | Evaluate salons before signing up | Medium (funnel) |
| Project owner | Scope, cost, and priorities | Decisive |
| Engineering and operations | Buildable, testable, operable requirements | Medium |
| Regulator / data subject | Lawful processing, retention limits, access and erasure | External |

---

## 3. User classes and their capabilities

This section is the explicit answer to "who uses the system and what each of them can do". Every
capability below maps to one or more functional requirements in Section 4; no capability exists
without a requirement ID.

### 3.1 Public visitor (not signed in)

A person who has not authenticated. The visitor is a first-class user class because most customers
begin here.

| Capability | Requirement | Priority |
|---|---|---|
| Open the public site and the authentication screens | FR-CUS-001 | Must |
| Browse the list of published, non-suspended salons | FR-CUS-001, FR-SAL-007 | Must |
| Search salons by name and city | FR-CUS-003 | Must |
| Search or filter by service (and, when built, by category, price range, availability) | FR-CUS-003, FR-CUS-004 | Must / Should |
| Open a salon public page: name, description, address, contact details, photos | FR-CUS-002 | Must |
| See services with duration and price | FR-CUS-002, FR-SVC-002 | Must |
| See working hours and advertised availability with the timezone stated | FR-CUS-006, FR-CUS-007 | Must |
| Compare services and prices across salons | FR-CUS-005 | Must |
| Read the authentication screens in Persian, right to left (F-019) | FR-L10N-001…006 | Implemented |
| Register as a customer | FR-IAM-001 | Must |
| Apply as a salon owner | FR-SAL-001 | Must |
| Reset a forgotten password | FR-IAM-004 | Must |

**Explicitly not allowed:**

- see unpublished, suspended, or draft salons, or inactive services (`BR-003`);
- see any customer data, booking data, or salon-internal data;
- create an administrator account through any public path (`FR-IAM-013`);
- complete a booking **only if** the guest-booking decision (Q1) is approved; until then, booking
  requires an account.

### 3.2 Customer

A registered, active user whose role includes `customer`. The customer is the primary actor of the
booking flow.

**3.2.1 Account and identity**

| Capability | Requirement | Priority |
|---|---|---|
| Register with full name, email, password and become active immediately | FR-IAM-001 | Must |
| Verify email ownership before sensitive actions | FR-IAM-002 | Must |
| Sign in and sign out securely; sessions revoked on sign-out | FR-IAM-003, FR-IAM-011 | Must |
| Reset the password with a short-lived single-use token | FR-IAM-004 | Must |
| View and update permitted profile fields (name, contact, timezone, notification preferences) | FR-IAM-005, FR-CUS-016, FR-DSH-006 | Must / Should |
| Change the password after re-authentication | FR-IAM-006 | Must |
| Revoke other sessions after a password change | FR-IAM-011 | Must |
| Deactivate the account under a defined policy | FR-IAM-009 | Should |
| Export own data and request deletion, subject to booking-retention rules | FR-IAM-010 | Should |

**3.2.2 Discovery and comparison**

| Capability | Requirement | Priority |
|---|---|---|
| Browse and search published salons | FR-CUS-001, FR-CUS-003 | Must |
| Filter by city, category, price range, and availability | FR-CUS-004 | Should |
| View full salon details, photos, services, prices, hours | FR-CUS-002 | Must |
| Compare services and prices across salons | FR-CUS-005 | Must |
| Save favourite salons | FR-CUS-018 | Could |

**3.2.3 Booking**

| Capability | Requirement | Priority |
|---|---|---|
| Select a service and view real available slots | FR-CUS-006 | Must |
| See which timezone the times are shown in | FR-CUS-007 | Must |
| Review a final summary: salon, service, start/end, timezone, price, currency, cancellation policy | FR-CUS-008 | Must |
| Create a booking for a chosen slot | FR-CUS-009 | Must |
| Rely on the server revalidating the slot and preventing overlap | FR-CUS-010 | Must |
| Receive a clear conflict response when the slot was taken | FR-CUS-011 | Must |
| Retry safely after a network failure without creating a duplicate | FR-BKG-008, `BR-023` | Must |
| See the booking in a pending state when the salon requires approval | FR-BKG-011 | Must |
| Book as a guest (only if Q1 is approved) | FR-CUS-017 | Could |

**3.2.4 Managing own bookings**

| Capability | Requirement | Priority |
|---|---|---|
| See upcoming bookings, sorted by start time | FR-CUS-012, FR-DSH-001 | Must |
| See past and cancelled bookings with clear status labels | FR-CUS-013, FR-DSH-002 | Must |
| Open one booking and see its snapshot, price, policy, and history | FR-CUS-013, FR-DSH-003 | Must |
| Cancel an eligible booking within the policy window | FR-CUS-014, FR-DSH-004 | Must |
| Reschedule an eligible booking within the policy window | FR-CUS-015, FR-DSH-005 | Must / Should |
| Review a salon after a completed appointment | FR-CUS-019, FR-REV-001 | Could (future) |
| See loading, empty, error, and success states on every screen | FR-DSH-007 | Must |

**Explicitly not allowed:**

- read or modify another customer's bookings (`BR-002`, `NFR-SEC-001`);
- read or modify any salon's private data, services, hours, images, or appointment list;
- reach administrator functionality;
- change a booking's price, duration, or service snapshot;
- bypass the cancellation cutoff or the rescheduling rules;
- create a booking for an unpublished, suspended, or inactive salon (`BR-022`).

### 3.3 Salon owner

A registered user whose role includes `salon_owner` and whose application was approved. Approval
grants dashboard access; it does **not** publish the salon (`FR-SAL-001a`).

**3.3.1 Onboarding and approval**

| Capability | Requirement | Priority |
|---|---|---|
| Apply through a dedicated salon-owner registration flow with personal and basic salon data | FR-SAL-001 | Must |
| Remain unable to sign in while the application is pending or rejected | FR-IAM-012 | Must |
| Be approved or rejected by an administrator, with a recorded reason | FR-SAL-001a, FR-ADM-003 | Must |
| Sign in after approval and open the salon dashboard | FR-IAM-003, FR-SAL-001a | Must |
| Re-apply after rejection or apply as an existing customer | — | Not in first release (open, see Section 12) |

**3.3.2 Salon profile**

| Capability | Requirement | Priority |
|---|---|---|
| Create and edit own salon profile | FR-SAL-002 | Must |
| Set a unique public slug | FR-SAL-003 | Must |
| Set the salon IANA timezone and currency | FR-SAL-004 | Must |
| Set name, description, address, phone, public contact email | FR-SAL-005 | Must |
| Preview the public page | FR-SAL-006 | Must |
| Publish or unpublish the salon | FR-SAL-006 | Must |
| Have the salon hidden from the public while unpublished, suspended, or under review | FR-SAL-007, `BR-003` | Must |

**3.3.3 Services and pricing**

| Capability | Requirement | Priority |
|---|---|---|
| Create, edit, activate, deactivate, and archive own services | FR-SVC-001 | Must |
| Set name, duration in minutes, price in integer minor units, currency, active flag | FR-SVC-002 | Must |
| Add a description and optional pre/post buffers | FR-SVC-003 | Must |
| Be prevented from saving a non-positive duration or negative price | FR-SVC-004 | Must |
| Remove a service from the catalogue without deleting historical bookings | FR-SVC-005 | Must |
| Change a price or duration without rewriting existing bookings | FR-SVC-006 | Must |
| Tag or categorise services for search | FR-SVC-008 | Should |
| Define service variants and add-ons | FR-SVC-009 | Could |

**3.3.4 Portfolio images**

| Capability | Requirement | Priority |
|---|---|---|
| Upload JPEG, PNG, and WebP images up to the configured limits | FR-IMG-001, FR-IMG-003 | Must |
| Rely on content validation, not filename or client MIME type | FR-IMG-002 | Must |
| Reorder images and choose a cover photo | FR-SAL-008, FR-SAL-009 | Must |
| Delete an image from public display without corrupting other records | FR-IMG-008 | Must |
| Provide alt text for each image | FR-IMG-007 | Must |
| Have metadata such as location EXIF stripped before public serving | FR-IMG-009 | Should |
| Serve reasonably sized variants instead of full-resolution originals | FR-IMG-010 | Should |

**3.3.5 Working hours, availability, and policies**

| Capability | Requirement | Priority |
|---|---|---|
| Define recurring weekly working hours in the salon timezone, with multiple intervals per day | FR-AVL-001, FR-AVL-002 | Must |
| Define date-specific time off and unavailable periods | FR-AVL-003 | Must |
| Be prevented from saving overlapping or invalid hours | FR-AVL-004 | Must |
| Preview availability for a date range | FR-AVL-011 | Must |
| Configure minimum notice, booking horizon, slot interval, cancellation cutoff | FR-SAL-014 | Should |
| Configure approval-mode booking per salon or service | Q3, FR-SAL-011 | Must (after decision) |
| Define working hours that cross midnight | Q14 | Open |

**3.3.6 Appointment management**

| Capability | Requirement | Priority |
|---|---|---|
| See today's and upcoming appointments for own salon | FR-SAL-010, FR-ODS-001 | Must |
| Filter by date, status, and service | FR-ODS-002 | Must |
| Open an appointment and see permitted customer details and history | FR-SAL-013, FR-ODS-003 | Must |
| Confirm or reject a pending appointment when approval mode is on | FR-SAL-011, FR-ODS-004 | Must |
| Cancel or reschedule with a recorded reason and policy validation | FR-SAL-012, FR-ODS-005 | Must |
| See the effect of schedule changes on existing appointments | FR-ODS-006 | Must |
| See summary counts (upcoming, completed, cancelled) | FR-SAL-015, FR-ODS-007 | Should |
| Manage multiple staff members and assign services | FR-SAL-016 | Could (out of first release) |
| Configure custom intake questions | FR-SAL-017 | Could |

**Explicitly not allowed:**

- read or modify another salon's profile, services, images, hours, or appointments (`BR-001`);
- see the full personal data of a customer beyond what delivering the service requires
  (`FR-SAL-013` — the boundary is currently vague, see `SR-05`);
- publish the salon before approval, or keep it public while suspended;
- hard-delete a service or image that a booking or audit record references (`BR-020`);
- change a historical booking's snapshot (`BR-019`);
- grant itself the `admin` role;
- block time in a way that silently invalidates an existing appointment (a resolution workflow is
  required).

### 3.4 Administrator

A privileged platform operator. The administrator role is never obtainable through public
registration (`FR-IAM-013`, and `SR-06` for the remaining gaps).

**3.4.1 Accounts and roles**

| Capability | Requirement | Priority |
|---|---|---|
| Access a protected administrator interface | FR-ADM-001 | Must |
| Search, view, activate, suspend, and deactivate user accounts | FR-ADM-002 | Must |
| Grant or revoke roles under least privilege | FR-ADM-005 | Must |
| Grant the administrator role to another account (administrator only) | FR-ADM-005 | Must |
| Provision the first administrator out of band | FR-IAM-013 | Must |

**3.4.2 Salons and moderation**

| Capability | Requirement | Priority |
|---|---|---|
| Review salon-owner applications and approve or reject with a recorded reason | FR-ADM-003 | Must |
| Suspend a salon so it stops accepting bookings | FR-ADM-002, `BR-022` | Must |
| Request changes before a salon is published | FR-ADM-003 | Must |
| Approve, suspend, or deactivate a salon listing | FR-ADM-002 | Must |
| Manage service categories and public taxonomy | FR-ADM-007 | Should |
| Manage announcements and support contact details | FR-ADM-013 | Should |

**3.4.3 Platform configuration**

| Capability | Requirement | Priority |
|---|---|---|
| Configure platform-wide settings | FR-ADM-006 | Must |
| Configure global defaults for cancellation, booking horizon, and notification policy | FR-ADM-010 | Should |
| Configure allowed currencies and enabled features | FR-ADM-006 | Must |

**3.4.4 Support and oversight**

| Capability | Requirement | Priority |
|---|---|---|
| Search and inspect bookings for support, subject to permissions | FR-ADM-008 | Must |
| Perform controlled booking interventions with a mandatory reason | FR-ADM-009 | Should |
| View operational metrics: registrations, salons, bookings, cancellations, notification failures | FR-ADM-011 | Should |
| Export filtered reports as CSV | FR-ADM-012 | Could |
| Read the audit trail of privileged actions | FR-ADM-004 | Must |
| Be prevented from irreversibly deleting records required for booking or audit integrity | FR-ADM-014 | Must |

**Explicitly not allowed:**

- delete bookings, booking history, or audit records to "clean up" data (`FR-ADM-014`);
- create an administrator through public registration (`FR-IAM-013`);
- act outside an explicitly granted permission (`NFR-SEC-001`);
- perform a privileged action without an audit record (`FR-ADM-004`, `BR-015`);
- read customer personal data without a documented support purpose (see `SR-05`, `SR-06`).

### 3.5 Role and permission matrix

`Yes` = full capability. `Own` = only over the actor's own resources. `Scoped` = only the minimum
needed for the stated purpose, with audit. `No` = denied by the server.

| Capability area | Visitor | Customer | Salon owner | Administrator |
|---|---|---|---|---|
| Browse published salons and services | Yes | Yes | Yes | Yes |
| View advertised availability | Yes | Yes | Yes | Yes |
| Create a booking | Q1 | Yes | No | Scoped (support) |
| View a booking | No | Own | Own salon | Scoped |
| Cancel or reschedule a booking | No | Own, in policy | Own salon, in policy | Scoped, with reason |
| Manage own profile | No | Own | Own | Own |
| Manage a salon profile | No | No | Own | Scoped (moderation) |
| Manage services and prices | No | No | Own | No (read only) |
| Upload portfolio images | No | No | Own | No |
| Manage working hours and time off | No | No | Own | No |
| Approve or reject an application | No | No | No | Yes |
| Suspend a user or salon | No | No | No | Yes |
| Grant roles, including admin | No | No | No | Yes, audited |
| Change platform settings | No | No | No | Yes |
| Read the audit log | No | No | No | Yes, scoped |
| Export personal data | No | Own | Own | Scoped |

---

## 4. Functional requirements

Priority notation: **Must**, **Should**, **Could**, **Implemented** (see Section 0.2).

### 4.1 Shared identity and account

| ID | Requirement | Priority |
|---|---|---|
| FR-IAM-001 | Two separate public registration journeys: a customer journey creating an active customer account, and a salon-owner journey creating a pending account plus a pending salon application. | Must |
| FR-IAM-002 | Verify email ownership before enabling sensitive account actions. | Must |
| FR-IAM-003 | Support secure sign-in and sign-out. | Must |
| FR-IAM-004 | Support password reset with a short-lived, single-use token. | Must |
| FR-IAM-005 | Let a user view and update permitted profile fields. | Must |
| FR-IAM-006 | Let a user change the password after re-authentication or equivalent protection. | Must |
| FR-IAM-007 | Enforce role permissions and resource ownership on the server for every protected operation. | Must |
| FR-IAM-008 | Rate-limit registration, login, and password-reset requests. | Must |
| FR-IAM-009 | Support account deactivation and reactivation under a defined policy. | Should |
| FR-IAM-010 | Support account data export and deletion, subject to legal and booking-retention requirements. | Should |
| FR-IAM-011 | Revoke a session on sign-out and allow revoking other sessions after a password change. | Must |
| FR-IAM-012 | A pending or rejected salon-owner account cannot authenticate and does not hold the salon-owner role. | Must |
| FR-IAM-013 | Administrator accounts are never creatable through public registration; the first administrator is provisioned out of band, later ones only by an authorized administrator. | Must |

### 4.2 Customer

| ID | Requirement | Priority |
|---|---|---|
| FR-CUS-001 | Browse published salon profiles. | Must |
| FR-CUS-002 | View a salon's name, description, address, contact details, photos, working hours, services, durations, and prices. | Must |
| FR-CUS-003 | Search salons by name and city; search or filter by service. | Must |
| FR-CUS-004 | Filter by city, service category, price range, and availability. | Should |
| FR-CUS-005 | Compare services and prices across salons. | Must |
| FR-CUS-006 | View available appointment slots for a selected service. | Must |
| FR-CUS-007 | Display the timezone used to interpret appointment times and working hours. | Must |
| FR-CUS-008 | Show a final summary before confirmation: salon, service, start/end, timezone, price, currency, cancellation policy. | Must |
| FR-CUS-009 | Create a booking with the required details. | Must |
| FR-CUS-010 | Revalidate availability at submission and prevent overlapping active bookings. | Must |
| FR-CUS-011 | Return a clear, stable conflict response when a slot is no longer available. | Must |
| FR-CUS-012 | View own upcoming and past bookings. | Must |
| FR-CUS-013 | View the details and status of own bookings, including the snapshot. | Must |
| FR-CUS-014 | Cancel own booking within the applicable policy. | Must |
| FR-CUS-015 | Reschedule own booking within the applicable policy. | Must |
| FR-CUS-016 | Set a preferred timezone and notification preferences. | Should |
| FR-CUS-017 | Support guest booking, subject to abuse prevention and account-claim rules. | Could |
| FR-CUS-018 | Support saved or favourite salons. | Could |
| FR-CUS-019 | Review a salon after a completed appointment. | Could |

### 4.3 Salon profile and owner

| ID | Requirement | Priority |
|---|---|---|
| FR-SAL-001 | A user can apply to become a salon owner through the dedicated flow, submitting personal details and basic salon information. | Must |
| FR-SAL-001a | The owner account and application stay pending until an administrator approves; approval grants the role and dashboard access but does not publish the salon. | Must |
| FR-SAL-002 | A salon owner can create and edit own salon profile. | Must |
| FR-SAL-003 | A salon has a unique public slug. | Must |
| FR-SAL-004 | A salon owner can set the salon IANA timezone and currency. | Must |
| FR-SAL-005 | A salon owner can set name, description, address, phone, and public contact email. | Must |
| FR-SAL-006 | A salon owner can preview and publish or unpublish the salon, subject to the approval decision. | Must |
| FR-SAL-007 | Only published, non-suspended salons and their active services are publicly visible. | Must |
| FR-SAL-008 | A salon owner can upload, reorder, and delete own portfolio images. | Must |
| FR-SAL-009 | A salon owner can set one image as the cover photo. | Must |
| FR-SAL-010 | A salon owner can view appointments assigned to own salon. | Must |
| FR-SAL-011 | A salon owner can confirm or reject a pending booking when approval mode is enabled. | Must |
| FR-SAL-012 | A salon owner can cancel or reschedule by policy with a recorded reason. | Must |
| FR-SAL-013 | A salon owner can view customer booking details to the extent required to deliver the service, respecting privacy rules. | Must |
| FR-SAL-014 | A salon owner can configure minimum notice, booking horizon, slot interval, and cancellation cutoff. | Should |
| FR-SAL-015 | A salon owner can view basic booking counts and upcoming workload. | Should |
| FR-SAL-016 | A salon owner can manage multiple staff and assign services to them. | Could |
| FR-SAL-017 | A salon owner can configure custom intake questions per service. | Could |

### 4.4 Services and pricing

| ID | Requirement | Priority |
|---|---|---|
| FR-SVC-001 | Create, edit, activate, deactivate, archive, and remove own services from the public catalogue. | Must |
| FR-SVC-002 | A service has a name, duration in minutes, price in integer minor units in the salon currency, and an active state. | Must |
| FR-SVC-003 | A service supports an optional description and optional pre/post buffers. | Must |
| FR-SVC-004 | Reject non-positive durations and negative prices. | Must |
| FR-SVC-005 | Removing a booked service is a soft removal; historical bookings are never deleted. | Must |
| FR-SVC-006 | Changing a price or duration never alters an existing booking's snapshot. | Must |
| FR-SVC-007 | A service belongs to exactly one salon; an owner cannot modify another salon's service. | Must |
| FR-SVC-008 | Support a service category or tag for search and filtering. | Should |
| FR-SVC-009 | Support service variants and add-ons. | Could |

### 4.5 Portfolio and images

| ID | Requirement | Priority |
|---|---|---|
| FR-IMG-001 | Accept JPEG, PNG, and WebP uploads subject to size and content validation. | Must |
| FR-IMG-002 | Validate actual file content, not only extension or client-provided MIME type. | Must |
| FR-IMG-003 | Enforce a maximum upload size and a maximum number of images per salon. | Must |
| FR-IMG-004 | Store uploaded files outside the web root with random, non-guessable names. | Must |
| FR-IMG-005 | Prevent path traversal; never trust a client-supplied storage path. | Must |
| FR-IMG-006 | Only the owning salon can add, reorder, or delete its images. | Must |
| FR-IMG-007 | Store alt text for each image for accessibility. | Must |
| FR-IMG-008 | Deleting an image removes it from public display without corrupting unrelated records. | Must |
| FR-IMG-009 | Strip unnecessary metadata, including location EXIF, before public serving. | Should |
| FR-IMG-010 | Generate reasonably sized variants instead of serving full-resolution originals. | Should |

### 4.6 Working hours and availability

| ID | Requirement | Priority |
|---|---|---|
| FR-AVL-001 | Define recurring weekly working hours in the salon timezone. | Must |
| FR-AVL-002 | Support multiple working intervals per day, for example split shifts. | Must |
| FR-AVL-003 | Define date-specific time off and unavailable periods. | Must |
| FR-AVL-004 | Reject invalid or overlapping working-hour configuration for the same day. | Must |
| FR-AVL-005 | Generate candidate slots from service duration, pre/post buffers, slot interval, minimum notice, and booking horizon. | Must |
| FR-AVL-006 | Exclude times covered by time off, closures, or active bookings. | Must |
| FR-AVL-007 | Return UTC instants plus the salon timezone and enough local information for display. | Must |
| FR-AVL-008 | Define and test daylight-saving behaviour for nonexistent and ambiguous local times. | Must |
| FR-AVL-009 | A closed or fully unavailable day produces no slots. | Must |
| FR-AVL-010 | Public availability is advisory and does not reserve a slot. | Must |
| FR-AVL-011 | A salon owner can preview availability for a date range. | Must |

### 4.7 Booking

| ID | Requirement | Priority |
|---|---|---|
| FR-BKG-001 | A booking references exactly one customer, one salon, and one service. | Must |
| FR-BKG-002 | A booking stores start and end instants in UTC. | Must |
| FR-BKG-003 | A booking stores the occupied interval, including service buffers. | Must |
| FR-BKG-004 | A booking preserves a snapshot of service name, duration, price, currency, salon timezone, and applicable cancellation policy at creation. | Must |
| FR-BKG-005 | Use half-open intervals `[start, end)` for overlap semantics. | Must |
| FR-BKG-006 | Prevent overlapping active bookings for the same salon when capacity is one. | Must |
| FR-BKG-007 | Booking creation is transactional and safe under concurrent requests. | Must |
| FR-BKG-008 | Booking creation supports an idempotency key so retries do not create duplicates. | Must |
| FR-BKG-009 | Booking states and legal transitions are explicitly defined. | Must |
| FR-BKG-010 | Retain an append-only history of important booking state transitions. | Must |
| FR-BKG-011 | A pending approval request, if enabled, blocks its interval for a configured expiry period. | Must |
| FR-BKG-012 | Rescheduling preserves history and reservation integrity. | Must |
| FR-BKG-013 | Cancellation supports a reason and policy-based eligibility. | Must |
| FR-BKG-014 | Salon deactivation or service archival never deletes historical bookings. | Must |
| FR-BKG-015 | The booking command revalidates availability inside the authoritative transaction, regardless of what the availability endpoint returned. | Must |
| FR-BKG-016 | Booking creation respects minimum notice, booking horizon, slot alignment, working hours, and time off. | Must |

### 4.8 Customer dashboard

| ID | Requirement | Priority |
|---|---|---|
| FR-DSH-001 | Show upcoming bookings sorted by start time. | Must |
| FR-DSH-002 | Show past and cancelled bookings with clear status labels. | Must |
| FR-DSH-003 | Open a booking and show its snapshot and history. | Must |
| FR-DSH-004 | Cancel an eligible booking. | Must |
| FR-DSH-005 | Reschedule an eligible booking. | Should |
| FR-DSH-006 | Update profile and preferred timezone. | Must |
| FR-DSH-007 | Provide loading, empty, error, and success states on every screen. | Must |

### 4.9 Salon owner dashboard

| ID | Requirement | Priority |
|---|---|---|
| FR-ODS-001 | Show today's and upcoming appointments for own salon. | Must |
| FR-ODS-002 | Filter appointments by date, status, and service. | Must |
| FR-ODS-003 | Open an appointment and view permitted customer details. | Must |
| FR-ODS-004 | Confirm or reject pending appointments when approval mode is enabled. | Must |
| FR-ODS-005 | Cancel or reschedule with a recorded reason and policy validation. | Must |
| FR-ODS-006 | Show the effect of schedule changes on existing appointments. | Must |
| FR-ODS-007 | Show summary counts (upcoming, completed, cancelled). | Should |

### 4.10 Administration

| ID | Requirement | Priority |
|---|---|---|
| FR-ADM-001 | Provide a protected administrator interface. | Must |
| FR-ADM-002 | Search, view, activate, suspend, and deactivate user accounts and salons with the required permission. | Must |
| FR-ADM-003 | Review salon-owner applications and approve or reject with a recorded reason. | Must |
| FR-ADM-004 | Record actor, timestamp, action, target, and reason for privileged actions. | Must |
| FR-ADM-005 | Manage role assignments under least privilege; only an administrator may grant the administrator role; no public path may create one. | Must |
| FR-ADM-006 | Configure platform-wide settings. | Must |
| FR-ADM-007 | Manage service categories and public taxonomy. | Should |
| FR-ADM-008 | Search and inspect bookings for support, subject to permissions. | Must |
| FR-ADM-009 | Perform controlled booking interventions with a mandatory reason and audit record. | Should |
| FR-ADM-010 | Configure global defaults for cancellation, booking horizon, and notification policy. | Should |
| FR-ADM-011 | View operational metrics: registrations, salons, bookings, cancellations, notification failures. | Should |
| FR-ADM-012 | Export filtered reports as CSV. | Could |
| FR-ADM-013 | Manage announcements and support contact details. | Should |
| FR-ADM-014 | Prevent irreversible deletion of records required for booking or audit integrity. | Must |

### 4.11 Notifications

| ID | Requirement | Priority |
|---|---|---|
| FR-NTF-001 | Send email-verification and password-reset messages. | Must |
| FR-NTF-002 | Send booking-created, confirmed, cancelled, and rescheduled messages as applicable. | Must |
| FR-NTF-003 | Notify the salon owner of new and cancelled bookings. | Must |
| FR-NTF-004 | A notification failure never rolls back a committed booking. | Must |
| FR-NTF-005 | Notification work is retryable and deduplicated. | Must |
| FR-NTF-006 | Send appointment reminders at configurable intervals. | Should |
| FR-NTF-007 | Notification payloads contain no unnecessary personal data. | Must |

### 4.12 Localization and right-to-left presentation (F-019)

These requirements are already implemented and verified in F-019. They are listed here so the SRS
describes the product as it actually is; they still need formal ratification (see `SR-07`).

| ID | Requirement | Status |
|---|---|---|
| FR-L10N-001 | The document declares `lang="fa"` and `dir="rtl"`; the default interface locale is Persian. | Implemented |
| FR-L10N-002 | User-visible strings on the authentication screens are Persian, except the brand wordmark and user-entered data. | Implemented |
| FR-L10N-003 | Latin data such as email addresses and passwords keeps left-to-right direction inside the right-to-left layout. | Implemented |
| FR-L10N-004 | Enum values from the API (`customer`, `active`, …) are displayed through Persian label maps; API contracts stay language-neutral. | Implemented |
| FR-L10N-005 | The font stack prefers a Persian-capable family and falls back to installed system fonts. | Implemented |
| FR-L10N-006 | Persian text avoids letter-spacing and text-transform; layout uses logical properties (`inset-inline-*`, `text-align: start`). | Implemented |
| FR-L10N-007 | Business data such as salon names, service names, and addresses accepts Persian text, including ZWNJ and Persian digits. | Not yet specified |
| FR-L10N-008 | Dates, times, prices, and phone numbers are formatted for the chosen locale, while instants stay stored in UTC. | Not yet specified |
| FR-L10N-009 | Emails, error pages, and future screens follow the same locale and direction rules. | Not yet specified |

### 4.13 Reviews (future phase)

Recorded for traceability only. Must not be implemented before F-015 is Ready.

| ID | Requirement | Priority |
|---|---|---|
| FR-REV-001 | A customer with a completed booking could submit one review for that booking. | Could |
| FR-REV-002 | A review could contain a 1–5 rating and optional text. | Could |
| FR-REV-003 | A salon owner could reply to a review. | Could |
| FR-REV-004 | A public salon page could show an aggregate rating and review count. | Could |
| FR-REV-005 | An administrator could hide or remove reviews that violate policy, with an audit record. | Could |
| FR-REV-006 | Reviews could be moderated before publication, per the product decision. | Could |

---

## 5. Business rules and invariants

| ID | Rule |
|---|---|
| BR-001 | A salon owner can manage only their own salon, services, images, working hours, time off, and appointments. |
| BR-002 | A customer can access only their own private booking data. |
| BR-003 | Public visitors can access only published, non-suspended salon data and active services. |
| BR-004 | An appointment interval is half-open `[start, end)`. |
| BR-005 | A slot is not guaranteed until the booking transaction commits. |
| BR-006 | Only blocking states occupy time. Terminal states do not block availability. |
| BR-007 | For capacity one, active bookings for the same salon must not overlap, including buffers. |
| BR-008 | Recurring working hours are interpreted in the salon's IANA timezone. |
| BR-009 | Appointment instants are persisted in UTC. |
| BR-010 | Daylight-saving ambiguous and nonexistent local times follow an explicit documented policy and are covered by tests. |
| BR-011 | Money is stored as integer minor units plus an ISO 4217 currency code, never binary floating point. |
| BR-012 | A booking preserves a snapshot of service name, duration, price, currency, salon timezone, and applicable policy. |
| BR-013 | A pending approval booking, if enabled, blocks the selected interval until decision or expiry. |
| BR-014 | External email, storage, and payment calls do not occur inside the booking database transaction. |
| BR-015 | Administrative actions affecting accounts, salons, bookings, or platform policy are audited. |
| BR-016 | A salon's public slug is unique and case-insensitive. |
| BR-017 | A service must have a positive duration and a non-negative price. |
| BR-018 | A booking's occupied interval includes its pre/post buffers. |
| BR-019 | Changing a service or salon must not rewrite historical booking snapshots. |
| BR-020 | Deactivation, suspension, or archiving must not cascade-delete bookings or audit records. |
| BR-021 | Uploaded images must pass content validation before being stored or served. |
| BR-022 | An inactive or unpublished salon cannot receive new bookings. |
| BR-023 | An idempotent retry with the same key and the same request returns the original result; a different request with the same key is rejected. |
| BR-024 | Reviews, if later enabled, require a completed booking and follow the moderation policy. |

Proposed additions, **not approved**, tracked in Section 13:

| ID | Proposed rule | Finding |
|---|---|---|
| BR-P-01 | Personal data has a defined retention period per entity, and erasure never deletes booking or audit records required for integrity. | SR-05 |
| BR-P-02 | High-risk administrator actions require a second authorized administrator (dual control). | SR-06 |
| BR-P-03 | The default locale is `fa-IR` with right-to-left layout; the API stays locale-neutral. | SR-07 |
| BR-P-04 | The cancellation policy is a versioned entity; a booking snapshot references the exact policy version. | SR-03 |
| BR-P-05 | Audit records are append-only and tamper-evident; no application role can update or delete them. | SR-15 |
| BR-P-06 | Changing a salon slug keeps a redirect from the old slug for a defined period. | SR-20 |

---

## 6. Data requirements

### 6.1 Core entities

At minimum, as described in `docs/ARCHITECTURE.md`:

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

### 6.2 Integrity and constraints

- Enforce referential integrity with foreign keys.
- Unique constraints: normalized email, salon slug, idempotency scope/key, natural uniqueness rules.
- Check constraints: positive durations, non-negative prices, valid statuses, valid weekdays, valid
  intervals.
- One salon per owner and one owner per salon are enforced by the database while the MVP rule holds
  (see Q4).
- Timestamps for appointment instants use a timezone-aware type and are written in UTC.
- Money columns are integers plus a currency column; no floating-point money type anywhere.

### 6.3 Indexes and access paths

Indexes for: salon + time range, customer + time range, salon + status, service + active state,
city + published state, unique normalized email, unique slug, and the booking overlap constraint
support structure.

### 6.4 Images

Store image files outside the database; store only validated metadata, alt text, ordering, and
storage keys. Deleting an image removes it from public display without corrupting booking or audit
records.

### 6.5 Gaps acknowledged here

- Retention and deletion periods are required but not yet numeric (`NFR-PRIV-001`, `SR-05`).
- The cancellation-policy entity referenced by `BR-012` is not in the entity list (`SR-03`).
- Audit-log columns, immutability, and retention are not specified (`SR-15`).
- No import/migration path for existing salon data is described (deliberately out of scope).

---

## 7. External interface requirements

### 7.1 User interface

- Responsive web UI for desktop, tablet, and mobile; mobile-first customer booking flow.
- Required states on every data-driven screen: loading, empty, validation error, conflict, success,
  recoverable error with retry.
- Accessible forms, labels, focus states, announced errors, and keyboard-only operation.
- Clear timezone display wherever a time is shown.
- Persian, right-to-left default presentation (Section 4.12).
- No authorization decision lives only in the UI; the server denies independently.

### 7.2 API

- REST under `/api/v1`, documented by FastAPI-generated OpenAPI.
- Explicit request and response schemas; never raw ORM objects.
- ISO 8601 timestamps; instants include `Z` or an explicit offset; IANA timezone identifiers are
  separate fields.
- One error envelope: `{"error": {"code", "message", "fields", "request_id"}}`.
- Status codes: `401` unauthenticated, `403` authenticated but unauthorized, `409` booking conflict,
  `422` validation error.
- Pagination on every potentially unbounded list.
- Idempotency keys on booking creation and other retry-sensitive commands.
- Stable, machine-readable error codes; the frontend maps codes to localized text.

### 7.3 Email

- Templated messages with delivery status tracking through an outbox.
- Provider selected in F-003/F-013 and documented in an ADR.
- No unnecessary personal data in the payload.
- A delivery failure never invalidates a committed booking.

### 7.4 Image storage

- Filesystem adapter for local development; S3-compatible or equivalent durable storage in
  production (ADR-0006, F-006).
- Files served through a controlled endpoint or a storage origin, never from the source tree.
- Upload content validated before storage; metadata stripped before public serving where practical.

### 7.5 Payments and calendars

Out of scope for the first usable release. Each requires its own SPEC, PLAN, threat review, and ADR
before implementation.

---

## 8. Non-functional requirements

| ID | Requirement | Current target | Measurable today? |
|---|---|---|---|
| NFR-SEC-001 | Backend authorization and ownership checks on every protected operation. | Mandatory | Yes (negative tests) |
| NFR-SEC-002 | Passwords stored with Argon2id via a maintained library. | Mandatory | Yes (inspection + test) |
| NFR-SEC-003 | Rate limiting on authentication, reset, public availability, and booking endpoints. | Mandatory, no numbers yet | No (see SR-23) |
| NFR-SEC-004 | No secrets or sensitive personal data in logs or API errors. | Mandatory | Partly (log review) |
| NFR-SEC-005 | CSRF protection for state-changing cookie-authenticated requests. | Mandatory | Yes |
| NFR-SEC-006 | Upload validation by content, size, and type before storage. | Mandatory | Yes |
| NFR-REL-001 | A committed booking stays committed even if email delivery fails. | Mandatory | Yes |
| NFR-REL-002 | Booking creation is safe under concurrency and client retries. | Mandatory | Yes on PostgreSQL |
| NFR-REL-003 | A failed migration leaves the database in a known state with documented rollback. | Mandatory | Yes (manual) |
| NFR-PERF-001 | p95 under 500 ms for ordinary API calls under an agreed test load. | Provisional | No load model yet (SR-10) |
| NFR-PERF-002 | Availability latency benchmarked with representative schedules and booking volume. | Provisional | No (SR-10) |
| NFR-SCALE-001 | Horizontal application scaling without in-process session state. | Design rule | Yes |
| NFR-MAINT-001 | Every change includes automated tests and relevant documentation. | Mandatory | Process |
| NFR-MAINT-002 | Schema changes only through Alembic migrations. | Mandatory | Process |
| NFR-MAINT-003 | Backend passes formatter, linter, and type checker. | Mandatory | Yes |
| NFR-MAINT-004 | Frontend passes type check, lint, and unit tests. | Mandatory | Yes |
| NFR-OBS-001 | Structured logs, request IDs, health checks, and metrics for critical operations. | Mandatory | Partly (SR-25) |
| NFR-BCP-001 | Documented backups and tested restore procedures in production. | Mandatory, no RPO/RTO | No (SR-11) |
| NFR-ACC-001 | The UI targets WCAG 2.2 AA. | Mandatory | Not measured (SR-17) |
| NFR-PRIV-001 | Minimize personal data; define retention, export, and deletion procedures. | Mandatory, no numbers | No (SR-05) |
| NFR-COMP-001 | No legal-compliance claim without a documented review. | Mandatory | Process |

All numeric targets above are **provisional** until load, availability, and recovery requirements
are agreed (Section 13 proposes concrete starting values).

---

## 9. Acceptance criteria for the first usable release

Product acceptance:

1. A customer can register, verify their email, sign in, and sign out.
2. A salon owner can apply, be approved by an administrator, sign in, complete a salon profile, add
   services, set working hours, add time off, upload photos, and publish the salon.
3. A customer can find a published salon, inspect an active service, view available slots, and create
   a booking.
4. The booking summary shows the salon timezone, local time, UTC instant, price, currency, and
   cancellation policy.
5. A customer can view their own booking and cannot access another customer's booking.
6. A salon owner can view only their own salon's bookings and cannot access another salon's data.
7. An administrator can approve or suspend a salon and manage users, with every privileged action
   audited.
8. Two simultaneous requests for the same overlapping interval produce exactly one active booking;
   the other receives a clear conflict response.
9. A retry with the same idempotency key does not create a duplicate booking.
10. Times display correctly across salon and customer timezones and across daylight-saving
    boundaries.
11. A customer can cancel or reschedule within policy; a cancelled slot becomes available again.
12. A salon owner can cancel or reschedule with a recorded reason, and the customer sees the change.
13. A booking confirmation email is queued; a delivery failure does not invalidate the booking.

Release gates (process, not product behaviour — see `SR-22`):

14. Backend tests pass on PostgreSQL, including the concurrency suite.
15. Frontend tests and critical browser end-to-end journeys pass.
16. Migrations upgrade a clean PostgreSQL database and the previous supported schema.
17. No known critical or high security issue remains open.

---

## 10. Out of scope for the first usable release

Unless explicitly approved through the feature process:

- multiple staff per salon, rooms, equipment, or capacity greater than one;
- group sessions and classes;
- marketplace commissions, salon payouts, and subscriptions;
- online payments and deposits (F-016);
- customer reviews and ratings (F-015);
- native mobile applications;
- video conferencing;
- SMS and push notifications;
- external calendar synchronization;
- advanced CRM or marketing automation;
- AI recommendations or conversational booking;
- multi-region active-active deployment;
- event sourcing, CQRS, and microservices;
- advanced analytics or a data warehouse;
- data import from an existing salon system.

---

## 11. Traceability to the delivery queue

| Requirement area | Backlog task | Status (2026-11-23) |
|---|---|---|
| Documentation baseline | F-000 | Done |
| Authentication and minimal foundation | F-001 | In Progress |
| Authorization and ownership policies | F-002 | Proposed |
| Account lifecycle and profile | F-003 | Proposed |
| Salon profile and public page | F-004 | Proposed |
| Services and pricing | F-005 | Proposed |
| Portfolio and images | F-006 | Proposed |
| Working hours and availability | F-007 | Proposed |
| Public discovery and comparison | F-008 | Proposed |
| Booking core and concurrency | F-009 | Proposed |
| Customer dashboard | F-010 | Proposed |
| Salon owner dashboard | F-011 | Proposed |
| Cancellation and rescheduling | F-012 | Proposed |
| Notifications and reminders | F-013 | Proposed |
| Administration and audit | F-014 | Proposed |
| Reviews (future) | F-015 | Proposed |
| Payments (future) | F-016 | Proposed |
| Reporting (future) | F-017 | Proposed |
| Production readiness | F-018 | Proposed |
| Persian localization and RTL authentication screens | F-019 | Done |

This is an **area-to-task** map. It is not sufficient traceability; `SR-16` explains the missing
requirement-to-test link.

---

## 12. Product decisions requiring confirmation

| # | Decision | Status | Blocks |
|---|---|---|---|
| Q1 | Must every customer create an account, or can a visitor book and claim later? | Open | F-009 |
| Q2 | Salon onboarding: dedicated owner flow with administrator approval | **Resolved 2026-11-18** (F-001 SPEC, ADR-0010). Review SLA and existing-customer path still open. | F-004, F-013, F-014 |
| Q3 | Booking mode: instant confirmation, owner approval, or configurable per salon or service? | Open | F-009, F-011 |
| Q4 | Is one salon per owner and one owner per salon acceptable for the first release? | Open | F-004 |
| Q5 | Is capacity one per salon acceptable, or are staff and resources required immediately? | Open | F-007, F-009 |
| Q6 | Which launch market(s) and which currency and locale defaults? | Open (de facto `fa-IR` / IRR for the UI, not ratified) | F-001, F-004 |
| Q7 | What are the default and owner-overridable cancellation and no-show rules? | Open | F-012 |
| Q8 | Default booking horizon, minimum notice, slot granularity, pending-request expiry? | Open | F-007, F-009 |
| Q9 | Is a deposit or full payment required in the first release? | Open | F-016 |
| Q10 | Which production image storage provider? | Open | F-006 |
| Q11 | Which transactional email provider and sender identity? | Open | F-013 |
| Q12 | When are reviews enabled, and are they pre-moderated? | Open | F-015 |
| Q13 | Is city-based search sufficient, or is geocoding and radius search required? | Open | F-008 |
| Q14 | Must salons be able to define working hours that cross midnight? | Open | F-007 |
| Q15 | Is the first release English-only? | **Contradicted** by the shipped Persian/RTL authentication screens | F-001, F-004 |

When a decision is made, record it in the relevant feature SPEC and, if architectural, in an ADR.
Do not leave a decision implicit in code.

---

## 13. Senior engineering review

**Reviewed by:** senior software engineer (documentation review)
**Date:** 2026-11-23
**Scope:** this SRS, the approved baseline `docs/SRS.md` v1.0, and their fit with `AGENTS.md`,
`docs/ARCHITECTURE.md`, the delivery queue, and the code that exists today.

### 13.1 Overall verdict

This is a **better-than-average early SRS**. It is unusually disciplined about the things that
usually break booking products: half-open intervals, UTC storage, integer money, idempotency,
authoritative server-side revalidation, snapshotting of booking terms, audit of privileged actions,
and an explicit out-of-scope list. The separation of *what / how / when* is the right structure, and
several requirements read like they were written by someone who has debugged a double booking at
2 a.m.

It is **not yet a specification you can build a paid product from without further decisions**. Three
classes of weakness dominate:

1. **Decisions are still open where acceptance criteria already assume an answer.** Cancellation
   policy (Q7), booking mode (Q3), guest booking (Q1), and capacity (Q5) are unresolved, yet
   acceptance criteria 8 and 11 depend on them. A test cannot be written against "policy-based
   eligibility" when no policy exists.
2. **Non-functional requirements are stated as intentions, not numbers.** "p95 under 500 ms under an
   agreed test load", "documented backups", "rate-limited", "WCAG 2.2 AA", "minimize personal data"
   cannot be verified or failed. Untestable NFRs become permanent debt.
3. **Privacy, localization, and administrative safety are under-specified relative to their risk.**
   The product stores names, emails, phone numbers, and appointment histories for a consumer
   marketplace, ships a Persian RTL interface, and gives one role broad power over users and salons —
   yet there are no retention periods, no data classification, no separation of duties, and the SRS
   still asks whether the release is English-only.

Severity counts: **7 High, 1 Medium-High, 10 Medium, 1 Low-Medium, 6 Low** (25 findings).
Findings are ordered by risk, not by section.

### 13.2 Findings

#### SR-01 — Two documents both claim to be the product source of truth

**Severity:** High (documentation integrity)
**Evidence:** `docs/SRS.md` v1.0 says it "is the product-level source of truth"; this file restates
the same requirements. Section 0.3 of the baseline says a decision must not live implicitly in code,
yet the authority now lives implicitly in two files.
**Why it matters:** the next requirement change will be made in one file and not the other. Within a
month, an engineer will implement the wrong priority. Duplicated requirements also double the review
cost and hide drift from CI.
**Recommendation:**
- Choose one normative file. Preferred: keep `docs/SRS.md` as the only normative SRS, and turn the
  root `SRS.md` into a short index plus the capability catalogue, with a generated requirement list.
- If the root file must be normative instead, delete or clearly demote `docs/SRS.md` in the same
  change and update every link (`README.md`, `AGENTS.md`, feature specs).
- Add a CI check that fails when requirement IDs, priorities, or counts differ between the two files.
- Record the decision in an ADR, because document authority is a long-lived architectural choice.

#### SR-02 — The booking state machine is required but never defined

**Severity:** High (data integrity)
**Evidence:** `FR-BKG-009` says states and legal transitions "shall be explicitly defined"; they are
not defined anywhere. `BR-006` refers to "blocking states" and "terminal states" without listing
them. `FR-BKG-011` and `FR-BKG-013` add pending and cancelled behaviours without naming states.
**Why it matters:** every downstream feature (availability, cancellation, dashboards, notifications,
admin intervention) switches on status values. If the set of states and the transition table are
not fixed now, each feature invents its own, and availability will block or free the wrong
intervals — which is exactly the class of bug this product cannot afford.
**Recommendation:** add a normative state table with, at minimum: `pending_approval`, `confirmed`,
`cancelled_by_customer`, `cancelled_by_owner`, `expired`, `completed`, `no_show`. For each: who may
enter it, from which states, whether it occupies the occupied interval, whether it is terminal,
whether email is sent, and whether it is audited. Add one acceptance test per transition, including
illegal ones.

#### SR-03 — Cancellation and no-show policy is open, yet acceptance depends on it

**Severity:** High (scope and testability)
**Evidence:** Q7 is open; `FR-CUS-014`, `FR-CUS-015`, `FR-BKG-013`, `FR-DSH-004`, `FR-ODS-005`, and
acceptance criterion 11 all say "within policy". `BR-012` requires the booking to snapshot "the
applicable cancellation policy", but Section 6 has no policy entity.
**Why it matters:** cancellation is where money, trust, and support load concentrate. "Policy-based"
is not implementable: you cannot store a snapshot of an entity that does not exist, and you cannot
write a negative test for an undefined cutoff.
**Recommendation:**
- Add a `cancellation_policies` entity (versioned): cutoff before start, fee or deposit consequence
  (MVP: consequence may be "none"), no-show rule, owner-override limits, effective dates.
- Add `bookings.cancellation_policy_id` and `bookings.policy_snapshot` (JSON or columns) as an
  explicit snapshot, referenced by `BR-012`.
- Decide Q7 and encode at least three test cases: exactly at the cutoff, one minute before, one
  minute after; plus a policy change after booking creation that must **not** alter the snapshot.
- Do this before F-012 is marked Ready, not during it.

#### SR-04 — Guest booking is an unresolved decision with schema consequences

**Severity:** High (data model)
**Evidence:** Q1 is open; `FR-CUS-017` is "Could"; the customer journey says "Guest booking is
allowed only if the product decision enables it"; `FR-BKG-001` requires exactly one customer per
booking.
**Why it matters:** guest booking changes the booking table (`customer_id` nullable or a separate
`guest_contact` model), the identity and verification flow (email claim tokens), the authorization
model (token-based booking access), abuse controls, and the notification flow. Retrofitting it into
a schema built on "one authenticated customer per booking" is a migration plus a security review.
**Recommendation:** decide Q1 before F-009. If deferred, make `FR-BKG-001` explicit that
`customer_id` is `NOT NULL` in the first release and record the reversal cost in the F-009 SPEC.

#### SR-05 — Personal data handling is named but not specified

**Severity:** High (privacy and legal risk)
**Evidence:** `NFR-PRIV-001` requires "minimize personal data and define retention, export, and
deletion procedures"; no data classification, no retention periods, no erasure-versus-booking
conflict rule, no admin access logging, no export format. `FR-SAL-013` lets a salon owner see
customer details "to the extent required to deliver the service" without saying which fields.
`FR-IAM-010` promises export and deletion "subject to booking-retention requirements" without
saying what those are.
**Why it matters:** this product stores identity data, contact data, and a behavioural history
(who booked which salon when). Support staff and salon owners are the most likely sources of
unauthorized disclosure. "We minimize data" is not a control; a field list is.
**Recommendation:**
- Add a data classification table (public / internal / personal / sensitive) and a field-level
  visibility matrix: what the salon owner sees (probably first name, masked phone, service, time,
  notes the customer chose to share), what support sees, what is never shown.
- Define retention per entity: sessions, verification and reset tokens, bookings, booking events,
  audit logs, outbox messages, uploaded images, deleted accounts.
- Define erasure semantics: anonymize the customer record while retaining the booking's financial
  and audit facts; document which fields are pseudonymized.
- Log every admin read of customer PII, not only writes (`BR-015` currently covers actions).
- Replace "where possible/practical" with pass/fail rules.

#### SR-06 — Administrator power has no separation of duties

**Severity:** High (security and insider risk)
**Evidence:** one `admin` role with `FR-ADM-002` (users), `FR-ADM-005` (role grants), `FR-ADM-009`
(booking interventions), `FR-ADM-006` (platform settings), and `FR-ADM-004` (audit). No MFA, no
dual control, no break-glass procedure, no session lifetime for admins, no restriction on reading
customer data, no requirement that audit records be immutable.
**Why it matters:** a single compromised administrator account can grant itself more power, alter
policies, read personal data, and edit the only evidence. "Audited" is a detective control; it does
not prevent the action, and it is worthless if the same role can modify the log.
**Recommendation:**
- Split permissions (user moderation, salon moderation, role administration, billing/support,
  audit read) and require explicit grants; `admin` becomes a role set, not one flag.
- Require MFA (TOTP or WebAuthn) for administrator sign-in; short session lifetime with
  re-authentication for high-risk actions.
- Require dual control for: granting the admin role, ownership transfer, irreversible suspension of
  a paying salon, and any booking intervention that changes price or time after confirmation.
- Make `audit_logs` append-only at the database level (revoke UPDATE/DELETE, or a write-only role),
  with a hash chain or periodic external export.
- Add a break-glass first-admin procedure (out-of-band provisioning, documented rotation).
- Add negative tests: an administrator without the specific permission receives `403`.

#### SR-07 — Localization is missing from the SRS while the product is already Persian

**Severity:** High (product-market fit and consistency)
**Evidence:** Q15 asks "Is the first release English-only?", while F-019 has already shipped
`lang="fa"` / `dir="rtl"` authentication screens with Persian error messages. The SRS has no
localization section, no locale requirement, no RTL rule, no date/price formatting rule, and no
requirement that business data accept Persian text.
**Why it matters:** the SRS is now a false description of the product. Worse, the unanswered
question invites a future engineer to "restore" English or to build the remaining screens
left-to-right. Persian input also has concrete technical consequences: ZWNJ, Arabic-Indic versus
Persian digits, text direction in mixed strings, search normalization (`ی`/`ي`, `ک`/`ك`), and
collation.
**Recommendation:**
- Ratify Section 4.12 as normative and resolve Q15 as `fa-IR`, right-to-left, with English as a
  possible second locale later.
- Add: search and uniqueness normalization rules for Persian text; acceptance of Persian digits in
  phone and price inputs; formatting rules for dates, times, and prices; email and error-page
  localization; translation ownership and review process.
- Decide explicitly whether the Jalali calendar is displayed. If yes, the API must still exchange
  UTC instants plus IANA timezone, and the calendar is presentation only.
- Add an accessibility check for RTL reading order and mixed-direction content.

#### SR-08 — Concurrency is required but the evidence bar is not in the SRS

**Severity:** Medium-High (release gate)
**Evidence:** `NFR-REL-002` and acceptance criterion 8 require safety under concurrency, but the SRS
never names the mechanism or the test environment. `AGENTS.md` requires a PostgreSQL exclusion
constraint and a concurrent integration test; the SRS does not repeat that obligation, so a reader
of the SRS alone could satisfy it with an application-level check.
**Why it matters:** "check then insert" passes code review and fails in production. The requirement
must be testable at the level of the guarantee, not the implementation.
**Recommendation:** state that the overlap guarantee is enforced by the database (exclusion
constraint on the occupied interval per salon, or an approved proven alternative recorded in
ADR-0003), and that the concurrency suite runs against PostgreSQL in CI on every pull request.
Add a negative test that bypasses the service layer and attempts a direct insert.

#### SR-09 — Money rules stop at storage

**Severity:** Medium (correctness and support)
**Evidence:** `BR-011` fixes integer minor units and ISO 4217. Nothing covers tax, rounding,
multi-currency salons, refunds, deposits, display formatting, or what a price change does to a
pending booking. Q9 leaves payments open but F-016 will need these answers.
**Why it matters:** prices are the most visible promise in the product and the most common support
dispute. Ambiguity here tends to surface as a one-cent mismatch in a snapshot.
**Recommendation:** add explicit rules: MVP is single-currency per salon; no tax computation in the
first release (or specify inclusive versus exclusive); rounding only at display time; snapshots are
immutable including currency; add a decision now on whether a pending approval booking keeps its
price if the service price changes while pending.

#### SR-10 — Performance and scale targets are not measurable

**Severity:** Medium (operability)
**Evidence:** `NFR-PERF-001` "p95 under 500 ms ... under an agreed test load"; `NFR-PERF-002`
"benchmarked with representative schedules"; no user count, dataset size, concurrency, endpoint
budget, or error budget.
**Why it matters:** without a load model, no one can say whether the system is fast enough, and the
availability endpoint — the most expensive query in the product — has no budget at all.
**Recommendation:** propose and approve concrete starting targets, for example: 50 000 salons,
1 000 000 bookings, 200 concurrent users, p95 ≤ 300 ms for read endpoints, p95 ≤ 500 ms for
availability over a 14-day range, p95 ≤ 800 ms for booking creation, p99 ≤ 2 s, error rate < 0.5 %.
Then add a repeatable load script and a CI smoke benchmark.

#### SR-11 — No recovery objectives

**Severity:** Medium (business continuity)
**Evidence:** `NFR-BCP-001` only requires "documented backups and tested restore procedures".
**Why it matters:** "we have backups" is not a recovery plan. A marketplace that loses a day of
bookings loses trust permanently, and the overlap constraint makes partial restores dangerous.
**Recommendation:** set RPO ≤ 15 minutes with point-in-time recovery, RTO ≤ 4 hours, daily restore
drills into a scratch environment, quarterly full restore rehearsal, and a documented
"bookings-after-restore" reconciliation procedure.

#### SR-12 — Availability semantics are underspecified

**Severity:** Medium (correctness)
**Evidence:** `FR-AVL-005` introduces slot interval, buffers, minimum notice, and horizon without
defining how they combine. `FR-BKG-016` requires slot alignment without defining alignment origin.
Q14 leaves overnight hours open. `BR-010` requires a DST policy without stating it (AGENTS says
nonexistent local times are skipped and ambiguous times use the first occurrence, `fold=0`).
Nothing defines which date "today" means for the owner dashboard.
**Why it matters:** this is the highest-defect area in any booking system, and the requirements as
written permit several defensible but different implementations.
**Recommendation:** add a normative algorithm with worked examples:
- occupied interval = `[start − pre_buffer, start + duration + post_buffer)`;
- candidate starts are aligned to the slot interval relative to the working-window start;
- a slot is offered only if the entire occupied interval fits inside one working window and does not
  intersect time off or a blocking booking;
- minimum notice is measured from the current instant, and horizon is measured in the salon's local
  calendar;
- nonexistent local times are skipped, ambiguous times use `fold=0`;
- "today" is the salon's local date, displayed with the customer's timezone where relevant.
Then add table-driven tests, including a DST spring-forward and fall-back day.

#### SR-13 — Notification requirements omit deliverability and consent

**Severity:** Medium (trust and compliance)
**Evidence:** `FR-NTF-001…007` cover content and retry, but not sender authentication
(SPF/DKIM/DMARC), bounce and complaint handling, unsubscribe for reminders, email localization,
outbox lag, or what happens when an address is permanently invalid.
**Why it matters:** booking confirmations are the customer's proof of reservation. If they land in
spam or arrive a day late, support load rises and no-shows increase.
**Recommendation:** add requirements for a verified sending domain, bounce and complaint
suppression list, reminder opt-out, localized templates, outbox lag alert (for example p95 < 60 s),
retry with exponential backoff and a dead-letter state, and a metric for delivery failure rate.

#### SR-14 — Image requirements are not testable

**Severity:** Medium (security and cost)
**Evidence:** `FR-IMG-003` "maximum upload size and maximum number of images" without numbers;
`FR-IMG-009` "where practical"; `FR-IMG-010` "reasonably sized". No malware scan, no decompression
bomb limit, no orphan cleanup, no cache headers, no storage quota per salon.
**Why it matters:** image upload is the classic remote-code-execution and storage-cost vector.
"Reasonable" cannot be asserted in a test.
**Recommendation:** fix numbers (for example 5 MB per file, 30 images per salon, 20 MP decoded
limit), require re-encode rather than pass-through, require stripping of all EXIF, define variant
sizes (thumbnail 320 px, card 800 px, full 1600 px), delete orphaned files on a schedule, and add
`Content-Security-Policy` plus `Content-Disposition: inline` with a strict `Content-Type` on serving.

#### SR-15 — Audit requirements lack a schema and an immutability guarantee

**Severity:** Medium (accountability)
**Evidence:** `FR-ADM-004` lists actor, timestamp, action, target, reason. No schema, no
append-only enforcement, no retention, no access control, no PII policy inside audit records, no
query or export requirement, no tamper evidence.
**Why it matters:** an audit trail that can be edited by the party under investigation has no
evidentiary value, and one without retention policy either grows forever or disappears too early.
**Recommendation:** specify columns (id, occurred_at, actor_id, actor_role, action, target_type,
target_id, reason, request_id, ip_hash, before/after diff where safe), append-only grants, retention
(for example 24 months), read permission separated from write, and a documented export for
investigations.

#### SR-16 — Traceability stops at task level

**Severity:** Medium (quality assurance)
**Evidence:** Section 11 maps requirement areas to F-tasks. There is no requirement-to-spec-to-test
link, and no gate that a `Must` requirement has at least one automated test.
**Why it matters:** the Definition of Done claims test coverage, but nothing proves it. Requirements
quietly disappear between SPEC writing and implementation.
**Recommendation:** add a machine-readable requirement index (YAML or a Markdown table with stable
IDs) and a CI check that every `Must` ID appears in at least one feature SPEC and one test name or
test marker. Generate the human-readable traceability table from it so it cannot drift.

#### SR-17 — Accessibility is a slogan

**Severity:** Medium (legal and usability)
**Evidence:** `NFR-ACC-001` "target WCAG 2.2 AA", plus one line in Section 7.1.
**Why it matters:** accessibility is verifiable, and a booking flow that cannot be completed by
keyboard or screen reader excludes customers. In an RTL product, reading order and focus order are
additional failure modes.
**Recommendation:** add concrete acceptance criteria: full booking flow by keyboard only; visible
focus on every interactive element; labelled inputs and announced errors; status changes announced
via live regions; contrast ≥ 4.5:1 for text; touch targets ≥ 24×24 CSS px; no color-only status;
correct `dir` per element; automated axe check plus one manual screen-reader pass per release.

#### SR-18 — No legal and consent surface

**Severity:** Medium (product readiness)
**Evidence:** `NFR-COMP-001` correctly refuses to claim compliance, but the SRS has no terms of
service, privacy notice, cookie consent, age limit, or marketing-consent requirement.
**Why it matters:** a consumer marketplace that collects accounts and sends transactional and
marketing email needs these pages before launch, regardless of jurisdiction details. Their absence
is a launch blocker, not a legal nicety.
**Recommendation:** add requirements for published terms and privacy notice with versioned consent
records, age eligibility, cookie and analytics consent (if analytics exist), and a documented
process for legal review. Keep the honest statement that compliance is not claimed until reviewed.

#### SR-19 — Timezone lifecycle and display ownership are ambiguous

**Severity:** Low-Medium (correctness)
**Evidence:** `FR-CUS-007` requires showing the timezone used, but not whose timezone is shown where.
`FR-CUS-016` lets a customer set a preferred timezone without saying how it interacts with salon
local time. Nothing mentions the tzdata version, even though DST rules change by law (Iran abolished
DST in 2022).
**Why it matters:** the same instant can be displayed three ways (salon local, customer local, UTC)
and a stale tzdata package silently shifts every future appointment.
**Recommendation:** state the display rule (booking confirmation shows salon local time as primary
and the customer's local time as secondary), pin and update the tzdata dependency, and add a
regression test using a historical DST transition plus one future-dated rule change.

#### SR-20 — Slug and lifecycle rules for public pages are incomplete

**Severity:** Low (SEO and support)
**Evidence:** `BR-016` requires a unique case-insensitive slug. No rule for reserved words,
renaming, redirects, slug reuse after deletion, or what the public page shows after a salon is
suspended.
**Why it matters:** broken public links are lost bookings, and slug reuse can silently serve the
wrong business.
**Recommendation:** define reserved slugs, permanent redirects from old slugs for at least 12
months, no reuse of a slug for a different salon, and explicit public behaviour for suspended and
unpublished salons (404 versus 410 versus a "temporarily unavailable" page).

#### SR-21 — Future review requirements create scope-creep pressure

**Severity:** Low (scope control)
**Evidence:** `FR-REV-001…006` sit inside the main functional requirement list with priority
"Could", while Section 10 says reviews are out of scope.
**Why it matters:** a reader scanning "functional requirements" may treat reviews as in scope, and
rating aggregates are notoriously hard to add cleanly later.
**Recommendation:** move review requirements into a clearly separated appendix or the F-015 SPEC,
and keep one line in Section 10 that points to it.

#### SR-22 — Product acceptance and release gates are mixed

**Severity:** Low (governance)
**Evidence:** acceptance criteria 1–13 describe product behaviour; 14–17 describe process (tests,
migrations, security review).
**Why it matters:** a product owner cannot sign off on "the concurrency suite passes on
PostgreSQL", and a release engineer cannot sign off on "the summary shows the timezone". Mixing them
makes both sign-offs ambiguous.
**Recommendation:** split into "product acceptance" and "release gates", each with its own owner.

#### SR-23 — Rate limiting has no numbers

**Severity:** Low (security)
**Evidence:** `FR-IAM-008` and `NFR-SEC-003` require rate limiting with no thresholds, no scope
(IP, account, device), no response behaviour, and no lockout or backoff policy.
**Why it matters:** without numbers, the control is untested and easy to set so loosely that it does
nothing, or so tightly that it locks out real users.
**Recommendation:** propose starting values (for example login 5 per minute per IP and 10 per hour
per account, registration 3 per hour per IP, password reset 3 per hour per account, availability 60
per minute per IP, booking 10 per minute per account), a `429` response with `Retry-After`, generic
messages that do not reveal account existence, and tests for both limits.

#### SR-24 — Two names for one concept

**Severity:** Low (clarity)
**Evidence:** "booking" and "appointment" are used interchangeably throughout, including in
requirement IDs (`FR-BKG`) and dashboards (`FR-ODS`, appointment).
**Why it matters:** small, but it propagates into schema names, API paths, and UI labels, and it
makes cross-references ambiguous.
**Recommendation:** define `booking` as the persisted record and `appointment` as the calendar
occurrence in user-facing copy; use `booking` in code, schema, and API.

#### SR-25 — Observability requirements are not actionable

**Severity:** Low (operations)
**Evidence:** `NFR-OBS-001` requires structured logs, request IDs, health checks, and metrics, but no
specific metrics, no alert thresholds, no runbook requirement.
**Why it matters:** the failure modes that matter here are specific: booking conflict spikes, outbox
lag, availability latency, failed migrations. Generic "metrics" will not catch them.
**Recommendation:** require at least: booking attempts, conflicts, and commits; outbox backlog and
age; availability latency histogram; authentication failure rate; admin action count; database
connection saturation. Add alert thresholds and a short runbook per alert (F-018).

### 13.3 What is genuinely strong (keep it)

1. **Interval discipline.** Half-open `[start, end)`, an explicit occupied interval including
   buffers, and a database-level overlap guarantee is the correct design and is rarely written down
   this early.
2. **Server authority.** "The booking command revalidates availability inside the authoritative
   transaction" (`FR-BKG-015`) is the single most important sentence in the document.
3. **Snapshotting.** Booking terms are frozen at creation (`BR-012`, `FR-SVC-006`), which prevents
   the classic "price changed under a confirmed booking" bug.
4. **Money as integer minor units.** Correct, and stated twice, which is fine.
5. **Idempotency with mismatch rejection** (`BR-023`) rather than a blind retry.
6. **Roles and ownership as server-side concerns**, with no public admin creation path.
7. **Honest non-claims.** `NFR-COMP-001` refuses to assert legal compliance; the out-of-scope list
   is explicit; open decisions are listed instead of being silently decided.
8. **Process integration.** Requirement IDs, priorities, and task links make the document usable by
   a delivery queue, which is more than most SRS documents achieve.

### 13.4 Remediation plan (proposed, not approved)

| Priority | Action | Findings | Suggested owner |
|---|---|---|---|
| P0 — before F-009 is Ready | Ratify one normative SRS and make the other a generated view | SR-01 | F-000 |
| P0 | Publish the booking state table and transition tests | SR-02 | F-009 SPEC |
| P0 | Define the cancellation-policy entity and snapshot | SR-03 | F-012 SPEC |
| P0 | Decide guest booking and record the schema consequence | SR-04 | F-009 SPEC |
| P0 | Add the database overlap guarantee and PostgreSQL concurrency gate to the SRS | SR-08 | F-009 SPEC, ADR-0003 |
| P1 — before F-012/F-014 | Data classification, field visibility, retention, erasure, admin PII read logging | SR-05 | new F-020 privacy |
| P1 | Permission split, MFA, dual control, immutable audit | SR-06, SR-15 | F-002, F-014 |
| P1 | Ratify localization requirements and resolve Q15 | SR-07 | new F-021 localization |
| P1 | Availability algorithm with worked examples and DST tests | SR-12, SR-19 | F-007 SPEC |
| P1 | Numeric image limits and serving headers | SR-14 | F-006 SPEC |
| P1 | Money display, tax, rounding, and single-currency rules | SR-09 | F-005 SPEC |
| P1 | Terms, privacy notice, consent records | SR-18 | new F-022 legal surface |
| P2 — before production | Performance and scale numbers plus load script | SR-10 | F-018 |
| P2 | RPO/RTO and restore drills | SR-11 | F-018 |
| P2 | Requirement-to-test traceability gate | SR-16 | F-000, CI |
| P2 | Accessibility acceptance criteria | SR-17 | F-019 follow-up |
| P2 | Email deliverability and outbox SLO | SR-13 | F-013 |
| P2 | Observability metrics, alerts, runbooks | SR-25 | F-018 |
| P3 | Move future review requirements out of the main functional list | SR-21 | F-015 SPEC |
| P3 | Slug lifecycle, acceptance split, terminology, rate-limit numbers | SR-20, SR-22…SR-24 | respective SPECs |

Note: F-020, F-021, and F-022 are **proposals from this review**, not registered tasks. They must be
registered in `Task-List.md` with a SPEC and PLAN before any work starts, per `AGENTS.md` Section 4.

### 13.5 Review checklist for the next revision

Before the next version of this document is approved, confirm:

- [ ] Exactly one normative SRS exists and every link points to it.
- [ ] Every Q1–Q15 item is either resolved with a date and ADR/SPEC reference, or explicitly
      deferred with the affected acceptance criterion marked as blocked.
- [ ] Every `Must` requirement has at least one test reference or a justified manual check.
- [ ] Every numeric claim in Section 8 has a number, a measurement method, and an owner.
- [ ] The booking state table, transition rules, and blocking semantics are present.
- [ ] The privacy section lists data categories, retention periods, visibility per role, and erasure
      semantics.
- [ ] The administrator section separates permissions, requires MFA, and defines dual control.
- [ ] Localization is normative, including RTL, Persian text normalization, and display formatting.
- [ ] Product acceptance and release gates are separated.
- [ ] No requirement contradicts `docs/SRS.md` or `AGENTS.md`; if it does, the conflict is resolved
      in this document rather than left implicit.

---

## Appendix A — Persian summary of user capabilities (non-normative)

این بخش فقط برای خوانایی سریع توسط تیم فارسی‌زبان است و سند معتبر همان بخش‌های انگلیسی است.

**بازدیدکننده (بدون ورود):** دیدن سالن‌های منتشرشده، جست‌وجو بر اساس نام و شهر، دیدن خدمات، قیمت‌ها،
مدت زمان، تصاویر، ساعت کاری و زمان‌های آزاد اعلام‌شده، ثبت‌نام مشتری، درخواست سالن‌داری، بازیابی رمز.
بدون حساب کاربری هیچ داده‌ای از مشتری یا سالن خصوصی دیده نمی‌شود و حساب مدیر ساخته نمی‌شود.

**مشتری:** ثبت‌نام و ورود امن، تأیید ایمیل، بازیابی رمز، ویرایش پروفایل و منطقهٔ زمانی، جست‌وجو و
مقایسهٔ سالن‌ها، دیدن زمان‌های آزاد واقعی، دیدن خلاصهٔ نهایی (سالن، خدمت، زمان شروع و پایان، منطقهٔ
زمانی، قیمت، ارز، سیاست لغو)، ثبت نوبت با جلوگیری از رزرو تکراری، مشاهدهٔ نوبت‌های آینده و گذشته،
مشاهدهٔ جزئیات و تاریخچهٔ نوبت، لغو و جابه‌جایی نوبت در چارچوب سیاست. مشتری هرگز نوبت یا دادهٔ مشتری
دیگری را نمی‌بیند و به بخش مدیر یا سالن‌دار دسترسی ندارد.

**صاحب سالن:** درخواست سالن‌داری و ماندن در وضعیت «در انتظار تأیید» تا تصمیم مدیر، ورود پس از تأیید،
ساخت و ویرایش پروفایل سالن با پیوند یکتا، تعیین منطقهٔ زمانی و ارز، انتشار یا لغو انتشار سالن، مدیریت
خدمات و قیمت‌ها و بافرها، آپلود و مرتب‌سازی و حذف تصاویر با متن جایگزین، تعریف ساعت کاری هفتگی و
مرخصی، پیش‌نمایش زمان‌های آزاد، دیدن نوبت‌های سالن خود، تأیید یا رد درخواست‌های معلق، لغو یا جابه‌جایی
با ثبت دلیل. صاحب سالن به دادهٔ سالن دیگر دسترسی ندارد، نمی‌تواند نوبت تاریخی را حذف یا بازنویسی کند و
نمی‌تواند نقش مدیر بگیرد.

**مدیر:** ورود به پنل محافظت‌شده، جست‌وجو و فعال/تعلیق/غیرفعال‌سازی حساب‌ها، بررسی درخواست‌های
سالن‌داری و تأیید یا رد با دلیل، تعلیق سالن، مدیریت نقش‌ها با اصل حداقل دسترسی، تنظیمات سراسری پلتفرم،
مدیریت دسته‌بندی خدمات، جست‌وجوی نوبت‌ها برای پشتیبانی، مداخلهٔ کنترل‌شده در نوبت با دلیل اجباری، دیدن
گزارش‌های عملیاتی و فهرست رویدادهای حسابرسی. مدیر نمی‌تواند سابقهٔ نوبت یا رویداد حسابرسی را برای
«تمیزکاری» حذف کند و هیچ اقدام ممتازی بدون ثبت در حسابرسی انجام نمی‌شود.

**تصمیم‌های باز مهم:** رزرو مهمان، سیاست لغو و عدم‌حضور، حالت تأیید نوبت، ظرفیت بیشتر از یک، زبان و
تقویم پیش‌فرض، و منطقهٔ زمانی نمایش. این‌ها باید پیش از آماده‌شدن فیچرهای مربوطه تصمیم‌گیری شوند.
