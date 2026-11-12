# Gain.Integration.Outbound: decisions

> Why things are the way they are. Newest first. Entries marked `(from code comment - confirm)` were found in comments and need owner confirmation.

## (date unknown) Consumers always ACK; retries come from the database
- **Decision:** `IntegrationConsumer` ACKs every message, success or failure. Failures are persisted in `integration_response_details`, and `QueuePublishingScheduler` retries them (max 3).
- **Why:** avoid NACK loops that call the OEM API repeatedly; make every attempt visible on the monitoring dashboard. (inferred - confirm)
- **Where:** `BackgroundServices/IntegrationConsumer.cs`, `QueuePublishingScheduler.cs`
- **Status:** active

## (date unknown) Immediate republish for PayloadBuild / DataFetch failures
- **Decision:** republish straight away, instead of waiting for the 10-minute scheduler, when the data needed isn't there yet.
- **Why:** dependent records (e.g. follow-up needing the SF opportunity id) usually become available seconds later (from code comment - confirm).
- **Where:** `IntegrationConsumer.CallAPIs`
- **Status:** active

## 27 July (year unknown) Opportunity create sends no follow-up
- **Decision:** `RiverSfCreateOpportunityPayload.FollowUp = null`.
- **Why / requested by:** "changes requested by chandan on 27th july" (from code comment - confirm who and why).
- **Where:** `CQS/Presale/Opportunity.cs` → `CreateOpportunity_RiverSf`
- **Status:** active

## (date unknown) Receipts with mode 'W' are not sent to River Salesforce
- **Decision:** ReceiptMode `W` receipts are ACKed and discarded for `riversf`.
- **Why:** TODO (owners)
- **Where:** `IntegrationConsumer.CallAPIs`, and Common.API `CommonController` (duplicate)
- **Status:** active
