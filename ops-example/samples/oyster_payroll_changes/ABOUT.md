# Payroll change emails

**Every document here is made up.** The people, companies, email addresses and amounts are
invented, and the `.example` domains don't exist. No real client or employee data is used.

The idea comes from Oyster's public job posting for a Service Delivery Automation Analyst,
where payroll inputs (salary changes, expenses, time off, bonuses, country notes) arrive as
emails and documents that someone has to turn into payroll records:
https://jobs.ashbyhq.com/oyster/f5291a09-f28c-45b1-9bf9-eebb50c712da

Nothing here comes from Oyster, and Oyster has not seen or approved it.

## What each document tests

| Document | What makes it hard |
|---|---|
| 01_ferreira_salary.eml | Nothing. A clean salary change, as a baseline. |
| 02_otieno_bonus.eml | The amount is written in words. |
| 03_kowalski_leave.eml | A reply corrects the start date ("it's 1 March not 1 Feb"). |
| 04_ruiz_expense.eml | No currency, for an employee in Mexico. |
| 05_kestrel_spot_bonuses.eml | Two employees in one email. |
| 06_mokoena_termination.eml | Forwarded thread with two last days; the newest one wins. |
| 07_asante_expenses.eml | The total is only in an attachment that isn't there. |
| 08_team_dinner.eml | Not a payroll change at all (it mentions a quiz "bonus round"). |
| 09_almeida_salary.eml | The subject and the body give different salaries. |
| 10_santos_unpaid_leave.txt | A chat message with typos. |
| 11_raman_salary_india.eml | Indian number format (₹1,85,000) and a tax-regime note. |
| 12_bennett_bonus.eml | 03/01/2027 from a US manager about a UK employee: January or March? |
