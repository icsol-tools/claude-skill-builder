# Gain.Integration.Outbound: evals

> Run each in a fresh Claude Code session in plan mode ("plan only, don't edit"). If the plan misses something, fix the pack.

## E1 "Send RSA cancellation to River SF as a new sub-process `cancelrsa`"
- **Must touch:** mapper-row script, `GetRSADetailsQuery` (or a new details query), payload + response classes under `RiverSF/`, `ApiEndpoints`, `IRSA`/`RSA` new method, `IntegrationConsumer` case, `IntegrationResponseSyncConsumer` case, `UpdateRSACommand` handling.
- **Must not:** throw from the domain method; skip the sync consumer case; concatenate SQL.
- **Pass if:** the plan lists both consumer cases and the mapper row, and uses `FailureStage` values correctly.

## E2 "Job card updates are failing with PayloadBuild for some dealers. Find out why"
- **Must touch:** starts from `integration_response_details` for the ReferenceSlno, then `GetJobCardDetailsQueryHandler` / `TSWorkshop.dbo.GetJobCardDetailsForIntegration` and the validation in `Workshop/JobCard.cs`.
- **Must not:** guess the proc's logic without exporting it.
- **Pass if:** the plan maps `PayloadBuild` to validation/mapping and asks for the row's `ErrorMessage`.

## E3 "Make the retry limit configurable"
- **Must touch:** all three limits (consumer `dbRetryCount < 3`, `GetPendingRetryRecordsQueryHandler` SQL `RetryCount < 3`, `MaxQueueRetryCount`) and `appsettings.json`.
- **Must not:** change only one of them; inline the value into SQL.
- **Pass if:** a single config key drives both `< 3` checks, passed as a SQL parameter.

## E4 "Add a field `ColorCode` to the booking payload sent to SF"
- **Must touch:** `GetBookingDetailsForIntegration` proc (result set **by position**), `BookingDetails`/result classes, `RiverSfCreateBookingPayload`, mapping in `Product/Booking.cs`.
- **Must not:** reorder result sets; break the other booking sub-processes that share the payload.
- **Pass if:** the plan adds the column at the end of the right result set and checks all 9 booking codes.
