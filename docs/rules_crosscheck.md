# `imci-selected-v0` machine-readable rule set — Domain Expert Crosscheck

**Source:** Derived from WHO Integrated Management of Childhood Illness, Chart Booklet, March 2014

**Population:** Children aged 2 to 59 months

Review each EdgeIMCI-encoded rule derived from the WHO IMCI chart: does its condition, classification, and action set preserve the selected source logic?
These are not WHO-authored machine-readable rules and do not represent complete IMCI. Tick the box in the last column if correct, or write a note if something is wrong.

| Rule ID | Clinical Area | If (condition) | Then | Actions / Note | WHO page | Correct? |
|---|---|---|---|---|---|---|
| IMCI-GDS-UNABLE-TO-DRINK | General danger signs | Child has: unable to drink or breastfeed | Very severe disease | Complete assessment quickly; Give pre-referral treatment immediately; Prevent low blood sugar; Keep warm; Urgent referral | p.5 (chart 1 of 76) | ☐ |
| IMCI-GDS-VOMITS-EVERYTHING | General danger signs | Child has: vomits everything | Very severe disease | Complete assessment quickly; Give pre-referral treatment immediately; Prevent low blood sugar; Keep warm; Urgent referral | p.5 (chart 1 of 76) | ☐ |
| IMCI-GDS-CONVULSIONS-HISTORY | General danger signs | Child has: had convulsions | Very severe disease | Complete assessment quickly; Give pre-referral treatment immediately; Prevent low blood sugar; Keep warm; Urgent referral | p.5 (chart 1 of 76) | ☐ |
| IMCI-GDS-LETHARGIC-OR-UNCONSCIOUS | General danger signs | Child has: lethargic or unconscious | Very severe disease | Complete assessment quickly; Give pre-referral treatment immediately; Prevent low blood sugar; Keep warm; Urgent referral | p.5 (chart 1 of 76) | ☐ |
| IMCI-GDS-CONVULSING-NOW | General danger signs | Child has: convulsing now | Very severe disease | Give diazepam (if convulsing now); Complete assessment quickly; Give pre-referral treatment immediately; Prevent low blood sugar; Keep warm; Urgent referral | p.5 (chart 1 of 76) | ☐ |
| IMCI-RESP-FAST-BREATHING-2-12M | Cough or difficult breathing | Child aged 2 to 12 months with respiratory rate ≥ 50 breaths/min | Sets: fast breathing = yes (used by rule IMCI-RESP-PNEUMONIA-FAST-BREATHING) | Not a classification rule — this is a threshold check that feeds the respiratory classification rules below | p.6 (chart 2 of 76) | ☐ |
| IMCI-RESP-FAST-BREATHING-12-60M | Cough or difficult breathing | Child aged 12 to 60 months with respiratory rate ≥ 40 breaths/min | Sets: fast breathing = yes (used by rule IMCI-RESP-PNEUMONIA-FAST-BREATHING) | Not a classification rule — this is a threshold check that feeds the respiratory classification rules below | p.6 (chart 2 of 76) | ☐ |
| IMCI-RESP-SEVERE-DANGER-SIGN | Cough or difficult breathing | Any general danger sign is present | Severe pneumonia or very severe disease | Give first dose of appropriate antibiotic; Urgent referral | p.6 (chart 2 of 76) | ☐ |
| IMCI-RESP-SEVERE-STRIDOR | Cough or difficult breathing | Child has: stridor when calm | Severe pneumonia or very severe disease | Give first dose of appropriate antibiotic; Urgent referral | p.6 (chart 2 of 76) | ☐ |
| IMCI-RESP-PNEUMONIA-CHEST-INDRAWING | Cough or difficult breathing | Child has: chest indrawing | Pneumonia | Give oral amoxicillin for 5 days; Soothe throat and relieve cough; Advise when to return immediately; Follow up in 3 days | p.6 (chart 2 of 76) | ☐ |
| IMCI-RESP-PNEUMONIA-FAST-BREATHING | Cough or difficult breathing | Fast breathing detected (threshold met) | Pneumonia | Give oral amoxicillin for 5 days; Soothe throat and relieve cough; Advise when to return immediately; Follow up in 3 days | p.6 (chart 2 of 76) | ☐ |
| IMCI-RESP-COUGH-OR-COLD | Cough or difficult breathing | None of the above conditions met (fallback) | Cough or cold | Soothe throat and relieve cough; Advise when to return immediately; Follow up in 5 days if not improving | p.6 (chart 2 of 76) | ☐ |
| IMCI-DIARRHOEA-SEVERE-DEHYDRATION | Diarrhoea dehydration | At least 2 of: lethargic or unconscious = yes; sunken eyes = yes; drinking status in (Unable to drink, Drinks poorly); skin pinch = Goes back very slowly | Severe dehydration | If no other severe classification: Give fluid for severe dehydration (Plan C)<br><br>If other severe classification present: Urgent referral; Frequent ORS sips during referral; Continue breastfeeding | p.7 (chart 3 of 76) | ☐ |
| IMCI-DIARRHOEA-SOME-DEHYDRATION | Diarrhoea dehydration | At least 2 of: restless or irritable = yes; sunken eyes = yes; drinking status = Drinks eagerly / thirsty; skin pinch = Goes back slowly | Some dehydration | If no other severe classification: Give fluid, zinc and food (Plan B); Advise when to return immediately; Follow up in 5 days if not improving<br><br>If other severe classification present: Urgent referral; Frequent ORS sips during referral; Continue breastfeeding | p.7 (chart 3 of 76) | ☐ |
| IMCI-DIARRHOEA-NO-DEHYDRATION | Diarrhoea dehydration | None of the above conditions met (fallback) | No dehydration | Give fluid, zinc and food (Plan A); Advise when to return immediately; Follow up in 5 days if not improving | p.7 (chart 3 of 76) | ☐ |
