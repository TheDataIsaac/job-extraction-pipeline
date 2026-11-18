# Location evaluation

50 postings. 50 of 50 labels confirmed by Isaac.

## remote_scope

Correct: 47 of 50 (94%)

Rows are the true answer, columns are the model's answer.

| true \ model | anywhere | regions | countries | hybrid_or_office | not_stated |
|---|---|---|---|---|---|
| anywhere | 1 | 0 | 0 | 0 | 0 |
| regions | 0 | 21 | 0 | 0 | 0 |
| countries | 0 | 1 | 13 | 0 | 0 |
| hybrid_or_office | 0 | 0 | 2 | 12 | 0 |
| not_stated | 0 | 0 | 0 | 0 | 0 |

## Can someone living in Nigeria apply?

48 postings are labelled yes or no (10 yes, 38 no). 2 are labelled unclear and left out.

- Schema filter (`open_from_nigeria` in report.py): 46 of 48 (96%)
- Schema filter that also reads the time zone: 48 of 48 (100%)
- Baseline 1: "remote" or "worldwide" in the location label: 30 of 48 (62%)
- Baseline 2: report.py's place words in the location label: 46 of 48 (96%)
- For scale: answering "no" every time: 38 of 48 (79%)

## Did the checks catch the misses?

- Passed every check in verify.py: 49 of 50 (98%)
- Passed every check but still a miss: 5 of 5 misses

## Every miss (5)

### posthog-technical-support-engineer

- Posting: https://posthog.com/careers/technical-support-engineer
- Location label: Remote
- remote_scope: model `regions`, true `regions`
- Nigeria: model no, true yes
- Nigeria with the time zone read: model yes
- Places: model EU, US, true none
- The model quoted for remote_scope: "Remote"
- The model quoted for places: "We provide support across EU and US time zones, and we're hiring in both."
- Check problems: none
- Label note: Limited by time zone only, so regions under the rules. GMT +1 (Nigeria) is inside GMT +2 to GMT -8, so yes. The EU and US mention is about time zones, not places.

### posthog-product-manager-observability-(ex-founder-or-ex-product-engineer)

- Posting: https://posthog.com/careers/product-manager-observability-(ex-founder-or-ex-product-engineer)
- Location label: Remote
- remote_scope: model `regions`, true `regions`
- Nigeria: model no, true yes
- Nigeria with the time zone read: model yes
- Places: model GMT +2 to GMT -8, true none
- The model quoted for remote_scope: "Remote"
- The model quoted for places: "GMT +2 to GMT -8"
- Check problems: none
- Label note: Limited by time zone only, so regions under the rules. GMT +1 (Nigeria) is inside GMT +2 to GMT -8, so yes.

### airbnb-8351513

- Posting: https://careers.airbnb.com/positions/8351513/
- Location label: Singapore
- remote_scope: model `countries`, true `hybrid_or_office`
- Nigeria: model no, true no
- Nigeria with the time zone read: model no
- Places: model Singapore, true Singapore
- The model quoted for remote_scope: "Offices: Singapore, Singapore"
- The model quoted for places: "Offices: Singapore, Singapore"
- Check problems: none
- Label note: Only an office is named and nothing says remote, so hybrid_or_office under the office-city rule. Rule-dependent: countries (Singapore) is a defensible reading.

### airbnb-8336590

- Posting: https://careers.airbnb.com/positions/8336590/
- Location label: Mexico City, Mexico
- remote_scope: model `countries`, true `hybrid_or_office`
- Nigeria: model no, true no
- Nigeria with the time zone read: model no
- Places: model Mexico, true Mexico City, Mexico
- The model quoted for remote_scope: "Offices: Mexico"
- The model quoted for places: "Offices: Mexico"
- Check problems: none
- Label note: Only Mexico City and the Mexico office are named, nothing says remote, so hybrid_or_office under the office-city rule. Rule-dependent: the listing page (not the posting) says Live and Work Anywhere, which would make it countries (Mexico). Nigeria is no either way.

### amazon-clinical-quality-pm-one-medical-senior-health

- Posting: https://www.amazon.jobs/en/jobs/10514229/clinical-quality-pm-one-medical-senior-health
- Location label: USA, CA, Virtual Location - California; USA, TX, Virtual Location - Texas; USA, AZ, Virtual Location - Arizona; USA, GA, Virtual Location - Georgia; USA, MA, Virtual Location - Massachuset; USA, NH, Virtual Location - New Hampshi; USA, WA, Virtual Location - Washington; USA, CO, Virtual Location - Colorado; USA, VA, Virtual Location - Virginia; USA, NC, Virtual Location - N Carolina
- remote_scope: model `regions`, true `countries`
- Nigeria: model no, true no
- Nigeria with the time zone read: model no
- Places: model USA, AZ, Virtual Location - Arizona, USA, CA, Virtual Location - California, USA, CO, Virtual Location - Colorado, USA, GA, Virtual Location - Georgia, USA, MA, Virtual Location - Massachuset, USA, NC, Virtual Location - N Carolina, USA, NH, Virtual Location - New Hampshi, USA, TX, Virtual Location - Texas, USA, VA, Virtual Location - Virginia, USA, WA, Virtual Location - Washington, true California; Texas; Arizona; Georgia; Massachusetts; New Hampshire; Washington; Colorado; Virginia; North Carolina
- The model quoted for remote_scope: "USA, AZ, Virtual Location - Arizona - 68,700.00 - 92,700.00 USD annually"
- The model quoted for places: "USA, CA, Virtual Location - California"
- Check problems: none
- Label note: Remote, but only from the listed US states.

## Labelled unclear (2)

- atlassian-27203: the schema filter says no. Remote, but only in countries where Atlassian has a legal entity, and the posting doesn't name them. The office city before "Remote" isn't a limit on remote work.
- atlassian-27390: the schema filter says no. Remote, but only in countries where Atlassian has a legal entity, and the posting doesn't name them. The office city before "Remote" isn't a limit on remote work.
