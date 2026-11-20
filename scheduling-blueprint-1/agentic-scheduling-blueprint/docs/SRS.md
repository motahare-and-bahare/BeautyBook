# Software Requirements Specification (SRS)

**Product:** Multi-provider Online Scheduling Platform  
**Version:** 1.0 — Initial requirements baseline  
**Date:** 2026-11-16  
**Status:** Proposed; product decisions listed in Section 13 require confirmation.

## 1. Introduction

### 1.1 Purpose

This SRS defines the user roles, journeys, functional requirements, business rules, quality requirements, and release scope for a professional online appointment-booking platform. It is intended to support feature decomposition, specification/plan authoring, TDD, and phased delivery.

### 1.2 Product vision

Enable customers to discover service providers and reserve suitable appointment times online. Enable providers to publish services, pricing, schedules, and policies and manage their appointments. Enable platform administrators to govern users, providers, platform configuration, and operational health.

### 1.3 Scope

The platform is a multi-provider scheduling marketplace/direct-booking system. The initial architecture is a modular monolith with Vue 3 frontend and FastAPI backend. SQLite supports local development; PostgreSQL is the production database and authoritative concurrency-test database.

### 1.4 Terms

- **Customer:** person booking an appointment.
- **Provider:** person/business offering one or more bookable services.
- **Service:** provider-defined appointment type with duration, price, and policy.
- **Slot:** candidate start time and resulting appointment interval.
- **Availability rule:** recurring provider working-time rule.
- **Exception:** date-specific opening/closure or modified availability.
- **Booking:** persisted reservation and its lifecycle.
- **Active booking:** a booking state that blocks the time interval.
- **Timezone:** IANA identifier such as `Europe/Dublin`.
- **ADR:** Architecture Decision Record.
- **SPEC/PLAN:** feature-level requirements and implementation documents.

## 2. Stakeholders and user classes

### 2.1 Customer

Wants to find a suitable provider/service, understand price and duration, choose a valid time, complete a booking, and manage it afterwards.

### 2.2 Service Provider

Wants to create a trustworthy public presence, define services and prices, publish availability, control booking policies, and manage appointments.

### 2.3 Platform Administrator

Wants to operate the platform safely, manage users/providers, configure platform-wide behavior, resolve support cases, and monitor activity.

### 2.4 Public visitor

A non-authenticated visitor may browse public provider and service information and view public availability. Whether a visitor may book without an account is an open product decision.

## 3. Assumptions and constraints

1. The product initially supports one-to-one appointments with capacity one per provider/service resource.
2. Providers have an IANA timezone and define recurring availability in that local timezone.
3. Appointment instants are stored in UTC.
4. Prices are represented as integer minor units plus ISO 4217 currency code; do not use floating-point money.
5. The first usable release can support booking without online payment if payment scope is not approved.
6. Email is the initial notification channel.
7. The backend is authoritative for all permissions, pricing snapshots, availability, and booking state.
8. PostgreSQL is mandatory for production.
9. SQLite is used for local development and tests that do not depend on PostgreSQL-specific semantics.
10. Payments, SMS, external calendar synchronization, group bookings, and advanced marketplace payouts are not assumed to be first-release requirements.

## 4. User journeys

### 4.1 Customer journey: discover and book

1. Customer opens the platform.
2. Customer browses or searches providers/services.
3. Customer filters results by relevant category, name, location/online mode, price range, or availability where supported.
4. Customer opens a provider profile and reviews biography, services, duration, price, timezone, policies, and available times.
5. Customer selects a service.
6. Platform displays available slots in a clearly identified timezone.
7. Customer selects a slot and provides required booking details.
8. Customer signs in/registers or continues as guest if guest booking is enabled.
9. Customer reviews the final booking summary and confirms.
10. Backend revalidates availability and atomically creates the booking.
11. Customer receives confirmation or a pending-approval message.
12. Customer can view booking details and receive reminders.
13. Customer can cancel or reschedule within the applicable policy.

Alternative and exception paths:
- Slot becomes unavailable before submission: show a conflict and refresh slots.
- Validation fails: preserve safe form inputs and explain field errors.
- Provider requires approval: show pending status and explain expected next step.
- Notification delivery fails: booking remains valid; retry notification asynchronously.
- Customer loses connection after submit: retry with the same idempotency key and return the original result.
- Cancellation cutoff has passed: reject or route to support according to policy.
- Provider cancels: notify customer and present next steps/refund information if payment exists.

### 4.2 Provider journey: onboard and publish

1. Provider registers and verifies email.
2. Provider completes provider profile: display name, slug, description, contact/public details, timezone, and optional avatar.
3. Provider submits profile for approval if platform policy requires it.
4. Provider creates one or more services.
5. Provider sets service title, description, duration, price/currency, buffers, booking mode, and cancellation/reschedule policy.
6. Provider defines weekly availability in local time.
7. Provider adds date-specific exceptions, holidays, and time off.
8. Provider previews the public profile and availability.
9. Provider publishes the profile/services.
10. Provider receives booking notifications and manages booking requests.
11. Provider can confirm/reject pending requests where approval mode is enabled.
12. Provider can cancel/reschedule appointments subject to policy and audit rules.
13. Provider reviews upcoming/past bookings and basic performance summaries.

Alternative and exception paths:
- Profile is rejected or requires changes: show reason and allow resubmission.
- Invalid or overlapping availability rules: explain conflict and prevent invalid save.
- Provider changes service duration/price: existing bookings retain their original snapshots.
- Provider blocks time overlapping a confirmed booking: require an explicit resolution workflow; never silently invalidate an appointment.
- Provider account is suspended: public booking is disabled and existing bookings follow an administrator-approved handling policy.

### 4.3 Provider journey: manage a booking

1. Provider opens calendar/list view.
2. Provider filters by date, status, or service.
3. Provider opens a booking and sees permitted customer details and booking history.
4. Provider confirms/rejects if pending approval.
5. Provider may initiate cancellation or rescheduling.
6. Platform validates policy and records the state transition.
7. Customer is notified.
8. Provider sees the updated calendar.

### 4.4 Administrator journey: operate the platform

1. Administrator signs in using a protected account.
2. Administrator views an operational dashboard.
3. Administrator searches and filters users/providers.
4. Administrator reviews provider applications and approves, rejects, suspends, or requests changes.
5. Administrator manages roles and permission assignments.
6. Administrator configures global settings such as platform name, support contact, default policies, enabled features, and allowed currencies/locales.
7. Administrator manages service categories and public content where applicable.
8. Administrator searches bookings for support purposes and views audit history.
9. Administrator handles abuse reports or disputes through controlled actions.
10. Administrator reviews system/operational indicators and exports permitted reports.
11. Administrator actions are recorded in an audit log.

Alternative and exception paths:
- Administrator attempts an action outside their permission: deny and log security-relevant event.
- Destructive action affects bookings: require confirmation and use safe deactivation/archival rather than cascading deletion.
- Provider disputes an administrative decision: record reason and review history.
- Sensitive data is requested: disclose only the minimum authorized information.

## 5. Functional requirements

Priority notation: `Must` = required for first usable release; `Should` = planned shortly after; `Could` = optional/later.

### 5.1 Shared identity and account requirements

- **FR-IAM-001 (Must):** The system shall support account registration using a unique email address.
- **FR-IAM-002 (Must):** The system shall verify email ownership before enabling sensitive account operations.
- **FR-IAM-003 (Must):** The system shall support secure sign-in and sign-out.
- **FR-IAM-004 (Must):** The system shall support password reset using a short-lived, single-use token.
- **FR-IAM-005 (Must):** The system shall allow users to view and update permitted profile fields.
- **FR-IAM-006 (Must):** The system shall allow users to change passwords after re-authentication or equivalent protection.
- **FR-IAM-007 (Must):** The system shall enforce server-side role and resource-level authorization.
- **FR-IAM-008 (Should):** The system should support account deactivation and reactivation under defined policy.
- **FR-IAM-009 (Should):** The system should support account export/deletion workflows subject to legal retention requirements.
- **FR-IAM-010 (Must):** The system shall rate-limit authentication and password-reset endpoints.

### 5.2 Customer requirements

- **FR-CUS-001 (Must):** A customer shall be able to browse published provider profiles.
- **FR-CUS-002 (Must):** A customer shall be able to view a provider's active services, duration, price, currency, and booking policies.
- **FR-CUS-003 (Should):** A customer shall be able to search providers by name and service/category.
- **FR-CUS-004 (Should):** A customer shall be able to filter providers/services by supported criteria such as category, price, online/in-person mode, and availability.
- **FR-CUS-005 (Must):** A customer shall be able to view available appointment slots for a selected service.
- **FR-CUS-006 (Must):** The system shall display the timezone used to interpret appointment times.
- **FR-CUS-007 (Must):** A customer shall be able to create a booking with required contact and booking details.
- **FR-CUS-008 (Must):** The system shall show a final summary of provider, service, start/end time, timezone, price/currency, and applicable policy before confirmation.
- **FR-CUS-009 (Must):** The system shall revalidate slot availability at booking submission and prevent overlapping active bookings.
- **FR-CUS-010 (Must):** The system shall provide a clear response when a selected slot is no longer available.
- **FR-CUS-011 (Must):** A customer shall be able to view their upcoming and past bookings.
- **FR-CUS-012 (Must):** A customer shall be able to view booking status and details.
- **FR-CUS-013 (Should):** A customer shall be able to cancel a booking within the applicable cancellation policy.
- **FR-CUS-014 (Should):** A customer shall be able to request or perform rescheduling within policy.
- **FR-CUS-015 (Must):** The system shall send booking lifecycle email notifications.
- **FR-CUS-016 (Should):** The system should send configurable appointment reminders.
- **FR-CUS-017 (Should):** A customer shall be able to manage preferred timezone and notification preferences.
- **FR-CUS-018 (Could):** The system could support guest booking, subject to abuse prevention and account-claim rules.
- **FR-CUS-019 (Could):** The system could support customer reviews/ratings after completed appointments, subject to moderation.
- **FR-CUS-020 (Could):** The system could support saved/favorite providers.

### 5.3 Provider requirements

- **FR-PRO-001 (Must):** A user shall be able to apply to become a provider.
- **FR-PRO-002 (Must):** A provider shall be able to create and edit their own provider profile.
- **FR-PRO-003 (Must):** A provider shall be able to set a unique public profile slug.
- **FR-PRO-004 (Must):** A provider shall be able to set their IANA timezone.
- **FR-PRO-005 (Must):** A provider shall be able to create, edit, activate, deactivate, and archive services they own.
- **FR-PRO-006 (Must):** A service shall include at least a name, duration, price/currency or an explicit free-service designation, and active state.
- **FR-PRO-007 (Must):** A provider shall be able to define service-specific pre/post buffers where supported.
- **FR-PRO-008 (Should):** A provider shall be able to define different booking modes: instant confirmation or provider approval.
- **FR-PRO-009 (Must):** A provider shall be able to define recurring weekly availability in their local timezone.
- **FR-PRO-010 (Must):** A provider shall be able to define date-specific closures, special hours, and time off.
- **FR-PRO-011 (Must):** The system shall prevent invalid availability configurations and explain conflicts with existing bookings.
- **FR-PRO-012 (Must):** A provider shall be able to preview and publish/unpublish their public profile and services.
- **FR-PRO-013 (Must):** A provider shall be able to view bookings assigned to them.
- **FR-PRO-014 (Must):** A provider shall be able to view bookings in calendar and list formats.
- **FR-PRO-015 (Must):** A provider shall be able to confirm or reject pending bookings when approval mode is enabled.
- **FR-PRO-016 (Should):** A provider shall be able to cancel or reschedule a booking subject to policy.
- **FR-PRO-017 (Must):** A provider shall be able to view relevant customer booking details while respecting privacy rules.
- **FR-PRO-018 (Should):** A provider shall be able to configure minimum notice, maximum booking horizon, slot interval, and cancellation cutoff.
- **FR-PRO-019 (Should):** A provider shall be able to view basic booking counts and upcoming workload.
- **FR-PRO-020 (Could):** A provider could connect external calendars to import busy periods and/or publish confirmed bookings.
- **FR-PRO-021 (Could):** A provider could configure multiple staff/resources and capacity greater than one in a later release.
- **FR-PRO-022 (Could):** A provider could configure custom intake questions for a service, with data minimization and retention controls.

### 5.4 Administrator requirements

- **FR-ADM-001 (Must):** The system shall provide a protected administrator interface.
- **FR-ADM-002 (Must):** An administrator with the required permission shall be able to search, view, activate, suspend, and deactivate user accounts.
- **FR-ADM-003 (Must):** An administrator shall be able to review provider applications and approve, reject, suspend, or request changes.
- **FR-ADM-004 (Must):** The system shall record the actor, timestamp, action, target, and reason for privileged administrative actions.
- **FR-ADM-005 (Must):** An administrator shall be able to manage roles and permission assignments according to least privilege.
- **FR-ADM-006 (Must):** An administrator shall be able to configure platform-wide settings.
- **FR-ADM-007 (Should):** An administrator shall be able to manage service categories and public taxonomy.
- **FR-ADM-008 (Must):** An administrator shall be able to search and inspect bookings for support purposes, subject to permissions.
- **FR-ADM-009 (Should):** An administrator shall be able to perform controlled booking interventions with a mandatory reason and audit record.
- **FR-ADM-010 (Should):** An administrator shall be able to configure global defaults for cancellation, booking horizon, and notification policy.
- **FR-ADM-011 (Should):** An administrator shall be able to view operational metrics such as registrations, provider approvals, bookings, cancellations, and notification failures.
- **FR-ADM-012 (Could):** An administrator could export filtered reports in CSV format.
- **FR-ADM-013 (Should):** An administrator shall be able to manage platform announcements and support contact details.
- **FR-ADM-014 (Must):** The system shall prevent an administrator from silently or irreversibly deleting records required for booking/audit integrity.

### 5.5 Booking and scheduling requirements

- **FR-BKG-001 (Must):** A booking shall reference one customer, one provider, and one service.
- **FR-BKG-002 (Must):** A booking shall store start/end instants in UTC.
- **FR-BKG-003 (Must):** A booking shall preserve the timezone and material service/price/policy snapshots applicable at creation.
- **FR-BKG-004 (Must):** The system shall use half-open intervals `[start, end)` for overlap semantics.
- **FR-BKG-005 (Must):** The system shall prevent overlapping active bookings for a capacity-one provider/resource.
- **FR-BKG-006 (Must):** Booking creation shall be transactional and safe under concurrent requests.
- **FR-BKG-007 (Must):** Booking creation shall support an idempotency key to make client retries safe.
- **FR-BKG-008 (Must):** Booking states and legal transitions shall be explicitly defined.
- **FR-BKG-009 (Must):** The system shall retain booking transition history.
- **FR-BKG-010 (Must):** A pending approval request shall block its slot for a configured expiry period.
- **FR-BKG-011 (Should):** The system shall support rescheduling while preserving history and preventing a gap in reservation integrity.
- **FR-BKG-012 (Should):** The system shall support cancellation reasons and policy-based eligibility.
- **FR-BKG-013 (Must):** A service price change shall not alter the price snapshot of existing bookings.
- **FR-BKG-014 (Must):** Provider deactivation or service archival shall not delete historical bookings.

### 5.6 Notifications and integration requirements

- **FR-NTF-001 (Must):** The system shall send email verification and password-reset messages.
- **FR-NTF-002 (Must):** The system shall send booking-created/confirmed/pending/rejected/cancelled/rescheduled messages as applicable.
- **FR-NTF-003 (Should):** The system should send reminders at configurable intervals.
- **FR-NTF-004 (Must):** Notification delivery failure shall not roll back a committed booking.
- **FR-NTF-005 (Must):** Notification work shall be retryable and deduplicated.
- **FR-INT-001 (Could):** The system could integrate with external calendars using OAuth and least-privilege scopes.
- **FR-INT-002 (Could):** The system could accept payment-provider webhooks using signature verification and idempotent processing.
- **FR-INT-003 (Could):** The system could integrate with SMS providers through an adapter.

## 6. Business rules

- **BR-001:** A provider can manage only their own profile, services, availability, and assigned bookings.
- **BR-002:** A customer can access only their own private booking data.
- **BR-003:** Public visitors can access only published public data.
- **BR-004:** An appointment interval is half-open `[start, end)`.
- **BR-005:** A slot is not guaranteed until the booking transaction commits.
- **BR-006:** Active booking states block availability; terminal states do not, except where policy explicitly says otherwise.
- **BR-007:** For capacity one, active bookings for the same provider/resource must not overlap.
- **BR-008:** Provider recurring availability is interpreted in provider-local timezone.
- **BR-009:** Appointment instants are persisted in UTC.
- **BR-010:** Daylight-saving ambiguous/nonexistent local times must follow an explicit documented policy.
- **BR-011:** Money is stored as integer minor units plus currency code, never binary floating point.
- **BR-012:** A booking preserves a snapshot of service name, duration, price/currency, and policy.
- **BR-013:** A pending approval booking blocks the selected interval until decision or expiry.
- **BR-014:** External notification/calendar/payment calls do not occur inside the booking database transaction.
- **BR-015:** Administrative actions affecting accounts, providers, bookings, or platform policy are audited.

## 7. Data requirements

Core entities are described in `docs/ARCHITECTURE.md`. At minimum:
- User, Role, Permission, ProviderProfile
- Service, AvailabilityRule, AvailabilityException, TimeOff
- Booking, BookingEvent
- Notification/OutboxMessage, AuditLog
- Payment (only when payment feature is approved)

Data requirements:
- Enforce referential integrity.
- Use unique constraints for email, provider slug, idempotency scope/key, and other natural uniqueness rules.
- Use check constraints for valid duration, price, status, and interval values.
- Index common lookups: provider + start time, customer + start time, status + start time, service + active state.
- Define retention and deletion rules before production.
- Do not cascade-delete bookings or audit records when a user/provider/service is deactivated.

## 8. External interface requirements

### 8.1 User interface

Responsive web UI for desktop, tablet, and mobile. Required user-facing states include loading, empty, validation, conflict, success, and recoverable error.

### 8.2 API

REST API under `/api/v1`, documented by OpenAPI. Requests/responses use explicit schemas. Dates use ISO 8601. Instants include UTC offset or `Z`; timezone identifiers are separately represented where local schedule semantics matter.

### 8.3 Email

Email adapter must support templated, localized messages and delivery status tracking. Provider selection is deferred to deployment requirements.

### 8.4 Calendar/payment interfaces

Optional integrations must be defined in feature-specific specifications and ADRs before implementation.

## 9. Non-functional requirements

- **NFR-SEC-001:** All protected operations shall enforce backend authorization and ownership checks.
- **NFR-SEC-002:** Passwords shall be stored using a modern adaptive password hash such as Argon2id.
- **NFR-SEC-003:** Authentication, password reset, public availability, and booking endpoints shall be rate-limited.
- **NFR-SEC-004:** Secrets and sensitive personal data shall not be written to logs.
- **NFR-SEC-005:** State-changing cookie-authenticated requests shall be protected against CSRF.
- **NFR-REL-001:** A committed booking shall remain committed even if email delivery fails.
- **NFR-REL-002:** Booking creation shall be safe under concurrent attempts and client retries.
- **NFR-PERF-001:** Initial target: p95 under 500 ms for ordinary API calls under an agreed test load, excluding external provider latency.
- **NFR-PERF-002:** Availability endpoint latency and throughput shall be benchmarked with representative provider schedules and booking volume.
- **NFR-SCALE-001:** The modular monolith shall support horizontal application scaling without relying on in-process session state.
- **NFR-MAINT-001:** Code changes shall include automated tests and relevant documentation.
- **NFR-MAINT-002:** Database changes shall be managed through Alembic migrations.
- **NFR-OBS-001:** The system shall provide structured logs, request IDs, health checks, and metrics for critical operations.
- **NFR-BCP-001:** Production shall have documented backups and tested restore procedures.
- **NFR-ACC-001:** The UI shall target WCAG 2.2 AA.
- **NFR-PRIV-001:** The platform shall minimize personal data and define retention/export/deletion procedures.

Targets are provisional until load, availability, and recovery requirements are agreed.

## 10. Acceptance criteria for first usable release

1. A customer can find a published provider, inspect an active service, view available slots, and create a booking.
2. A customer can view their own booking and cannot access another customer's booking.
3. A provider can manage their profile, services, weekly availability, exceptions, and assigned bookings.
4. A provider can view and manage pending/confirmed bookings according to the selected booking mode.
5. An administrator can approve/suspend providers and manage core platform settings with audited actions.
6. The system prevents two simultaneous overlapping active bookings for the same capacity-one provider.
7. Booking retries with the same idempotency key do not create duplicate bookings.
8. Times display correctly across provider/customer timezones and daylight-saving boundary tests.
9. Booking notifications are queued reliably; notification failure does not invalidate the booking.
10. Backend tests pass on SQLite where portable and PostgreSQL for production-specific behavior, including concurrency.
11. Frontend tests and critical Playwright journeys pass.
12. Migrations can upgrade a clean PostgreSQL database and the previous supported schema.

## 11. Out of scope for the first usable release unless explicitly approved

- Multi-provider organizations with complex staff/resource pools.
- Group sessions and capacity greater than one.
- Marketplace commissions and provider payouts.
- Native mobile applications.
- Video conferencing.
- Advanced CRM/marketing automation.
- AI recommendations or conversational booking.
- Multi-region active-active deployment.
- Event sourcing and microservices.
- Advanced analytics warehouse.

## 12. Traceability to feature backlog

| Requirement area | Backlog task |
|---|---|
| Foundation and tooling | F-001 |
| Identity and accounts | F-002 |
| Roles and permissions | F-003 |
| Provider onboarding/profile | F-004 |
| Service catalog and pricing | F-005 |
| Availability and timezones | F-006 |
| Public discovery | F-007 |
| Booking and concurrency | F-008 |
| Customer booking management | F-009 |
| Provider booking management | F-010 |
| Cancellation/rescheduling | F-011 |
| Notifications/reminders | F-012 |
| Administration and audit | F-013 |
| Payments | F-014 |
| External calendars | F-015 |
| Reporting | F-016 |
| Production readiness | F-017 |

## 13. Product decisions requiring confirmation

These decisions must be resolved before the affected feature is marked Ready:

1. Is guest booking allowed, or must every customer create an account?
2. Is provider onboarding automatically published or admin-approved?
3. Can each provider choose instant booking versus approval, or is one platform-wide mode required?
4. Is online payment mandatory for any service in the first release? If yes, which provider, currencies, refund rules, and payment timing?
5. Which countries, currencies, and languages are in the initial launch?
6. Are services online, in-person, or both? Is location/address management required?
7. Is capacity strictly one, or must the model support rooms, staff, equipment, or group sessions?
8. What are default and provider-overridable cancellation/reschedule/no-show policies?
9. What booking horizon, minimum notice, slot granularity, and pending-request expiry should apply?
10. Which email provider and calendar integrations are required?
11. Are provider subscriptions/plans or platform commissions part of the business model?
12. What are the expected user count, booking volume, peak concurrency, availability target, RPO, and RTO?
