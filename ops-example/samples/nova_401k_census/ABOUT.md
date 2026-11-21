# 401(k) census data

**Every document here is made up.** The people, plan sponsors, email addresses and figures are
invented, and the `.example` domains don't exist. No real client or employee data is used.

The idea comes from Nova 401(k) Associates' public job posting, which describes turning client
payroll data into census and recordkeeper files and replacing manual PDF reading:
https://job-boards.greenhouse.io/nova401/jobs/5453770008

Nothing here comes from Nova 401(k) Associates, and they have not seen or approved it.

## What each document tests

| Document | What makes it hard |
|---|---|
| 01_redfern_new_hires.eml | Two new hires; one isn't enrolled, so there's no deferral. |
| 02_cobalt_termination.eml | Nothing. A clean termination, as a baseline. |
| 03_lakeside_scanned_register.txt | Text from a scanned PDF, with O for 0 and l for 1. |
| 04_brannock_part_timer.eml | Hours will be sent next week. |
| 05_redfern_deferral_change.eml | Deferral given as 6%, then "he changed it to 4% in July". |
| 06_cobalt_rehire.eml | A rehire: two hire dates and an old termination date. |
| 07_lakeside_census_paste.txt | A pasted table where one termination date is before the hire date. |
| 08_brannock_bonus.eml | Pay that may wrongly include an excluded bonus. |
| 09_redfern_invoice_question.eml | Not census data (it has a dollar amount and a date). |
| 10_cobalt_payroll_export.eml | Forwarded payroll-provider report, three employees. |
| 11_redfern_correction.eml | Corrects a hire date sent earlier. |
| 12_lakeside_missing_attachment.eml | The census is in a missing attachment; one leaver is in the body. |
