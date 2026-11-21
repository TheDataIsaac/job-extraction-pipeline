# Shipment updates

**Every document here is made up.** The job numbers, people, venues, carriers and email
addresses are invented, and the `.example` domains don't exist. No real client or company data
is used.

The idea comes from Christie Lites' public job posting, which describes shipment updates,
asset tracking and KPI reporting across branches:
https://jobs.workable.com/view/iiMmL8msnzkPpyVkz7D4ju

Nothing here comes from Christie Lites, and they have not seen or approved it.

## What each document tests

| Document | What makes it hard |
|---|---|
| 01_orlando_shipped.eml | "Today" as the ship date; a count made of cases plus carts. |
| 02_vegas_delayed_snow.eml | A delay with a new delivery day. |
| 03_chicago_delivered.eml | A reply with the earlier message quoted below. |
| 04_nashville_driver_text.txt | A driver's text with the count in words. |
| 05_toronto_two_jobs.eml | Two jobs in one email. |
| 06_denver_correction.eml | The delivery date is corrected later in the email. |
| 07_vegas_return_short.eml | A return with two cases missing. |
| 08_fwd_carrier_exception.eml | A forwarded carrier notice: the PRO number is not the job number. |
| 09_forklift_reminder.eml | Not a shipment update (it mentions a "delivery" of lockers). |
| 10_seattle_running_late.eml | Late, with no reason given. |
| 11_nashville_bol_attached.eml | The piece count is only on a missing attachment. |
| 12_toronto_ops_log.txt | A log where one delivery date is before its ship date. |
