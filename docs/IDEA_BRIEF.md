# KagazCheck: Idea Brief
**"Pehle jaanch, phir apply."** Check your documents first, then apply.

Live prototype: `<LIVE_URL>` · Code: `<REPO_URL>` · Demo video: `<VIDEO_URL>`

---

## 1. The problem
India pays scholarships and welfare benefits through **Direct Benefit Transfer (DBT)**. Before any money moves, portals such as the National Scholarship Portal (NSP), PFMS and state DBT portals compare a student's details across several documents: Aadhaar, bank account, marksheet, and income and caste certificates. **The comparison is literal.**

Small, everyday paperwork errors therefore lead to rejected applications or payments that never arrive:

| What goes wrong | Real-world example |
|---|---|
| Name spelt differently by a bank clerk | Aadhaar: **PRIYANKA KUMARI**, passbook: **PRIANKA KUMARI** |
| Initials or a missing middle name | **Rahul Kumar Singh** vs **R. K. Singh** / **Rahul Singh** |
| Account in a parent's name | Passbook in father's name; most schemes pay only into the student's own account |
| Aadhaar not seeded for DBT (NPCI mapper) | Linking Aadhaar to a bank account is not the same as DBT seeding |
| Expired income certificate | Issued 20 months ago; verifying officers want a recent one |
| DOB mismatch, wrong IFSC, father's name differs, income above limit | … |

PFMS's own remedy guidance tells beneficiaries to go to their bank for Aadhaar seeding and account fixes ([PFMS Validation Payment Rejection Remedies](https://gifmis.cga.gov.in/SitePages/doc/PFMS_Validation_Payment_Rejection_Remedies.pdf)). Student guides consistently list **Aadhaar seeding, name mismatch and account status** as the main causes of failed scholarship payments.

**The cruel part is timing.** A student usually discovers the problem months later, after verification or after the payment fails, when the academic year's fees are already due. Each fix needs a separate trip to a bank branch, an Aadhaar Seva Kendra or a tehsil office, and nobody tells the student *which* trip.

## 2. Who it is for
- **Primary:** the millions of students from low-income, SC/ST/OBC/minority and rural families who apply for post-matric and central-sector scholarships every year. Many are first-generation learners applying from a phone, often in Hindi or another regional language.
- **Secondary:** college scholarship cells, CSC operators and NGO volunteers who help students fill forms. They can run a check in a minute while the student is still in front of them.
- **Also useful for:** any DBT beneficiary (PM-KISAN, pensions, LPG subsidy) whose payment depends on Aadhaar–bank name matching.

## 3. How it works
1. **Pick the scheme.** The scheme sets which documents are needed and the income limit.
2. **Snap your documents** on a phone: Aadhaar, passbook first page, 10th marksheet, income certificate and caste certificate. Photos are compressed on the phone, so it works on slow connections.
3. **AI reads them.** Amazon Bedrock (Amazon Nova, a multimodal model) extracts names, dates, IFSC, income and issue dates as strict JSON. It also detects when the wrong document was uploaded or the photo is blurry. If Bedrock is unavailable, Amazon Textract is the automatic fallback.
4. **Student confirms.** Every extracted value is shown and editable (human-in-the-loop), so OCR mistakes never become wrong advice.
5. **Deterministic rules engine** cross-checks everything:
   - An **Indian-name-aware matcher** classifies *how* names differ: spelling (`PRIYANKA`/`PRIANKA`, `SUNITA`/`SUNEETA`, `LAKSHMI`/`LAXMI`), initials, abbreviations (`MD`/`MOHD`/`MOHAMMAD`, `KR`/`KUMAR`), missing parts, word order, or an entirely different person. It also detects when the account belongs to the father or mother.
   - Date of birth, gender and father's name are compared across documents.
   - The income certificate is checked against the scheme limit and its age, including the financial year.
   - IFSC format is validated, required documents are flagged, and a DBT-seeding reminder is always given because no photo can prove seeding.
6. **Fix-list in your language.** Each problem shows severity, why it matters, and the exact steps to fix it: which office, which form, what to ask for. The steps were written by hand in **English and Hindi** and translated into **10 more Indian languages** with Amazon Translate. The student can **listen** in Hindi or Indian English (Amazon Polly) for low-literacy users, **share to WhatsApp** for parents and helpers, or **print / save as PDF**.
7. **Insights page.** Live, **anonymous** counts of which problems are most common. A college scholarship cell can see "most of our students have a bank-name mismatch" and run one bank-desk camp instead of 500 individual trips.

**Privacy by design:** photos are processed in memory in the AWS Mumbai region and never stored. Aadhaar and account numbers are masked to the last 4 digits by both the model prompt and a server-side regex. Only anonymous problem counters are saved, never names or numbers.

## 4. Impact: why the majority should care
- **Catches the problem before it costs a year.** A one-minute check replaces months of waiting followed by a failed payment.
- **Turns vague rejection into a precise errand.** Instead of "PFMS rejected", the student hears "Go to your bank with Aadhaar, ask for name correction to *Priyanka Kumari*, and in the same visit ask for DBT seeding." One trip instead of several.
- **Works for the people who most need it:** mobile-first, Hindi plus 10 Indian languages, audio, WhatsApp sharing, no login and no app install.
- **Scales to institutions.** Anonymous insights help colleges, CSCs and departments target the most common fixes.

**How we measure it:**

| Metric | How it's measured |
|---|---|
| Problems caught before submission | Per-check issue counts on the live Insights page |
| Students with at least one blocking problem | Insights KPI ("% with a problem that could block payment") |
| Time to a full check | Under 1 minute for 5 documents (end-to-end test timings) |
| Languages served | English, Hindi + 10 via Translate; audio in Hindi and English |

## 5. What's new
- Existing tools help you *find* schemes. **KagazCheck makes sure the application you submit doesn't fail.** It cross-verifies a student's *own* documents against each other, which no portal does before submission.
- An **Indian-name-specific matching engine**, not generic fuzzy matching. It explains the *type* of mismatch because the fix differs: bank KYC update, Aadhaar update (name twice in a lifetime, DOB once) or a board correction.
- **LLM for reading, rules for deciding.** Generative AI only extracts fields. Every verdict comes from transparent, unit-tested rules, and all advice is human-written. Students never get hallucinated legal advice.

## 6. Roadmap
DigiLocker pull of documents (no photos needed) · PDF / e-Aadhaar support · state-specific rule packs (income-certificate validity differs by state) · CSC/college "operator mode" for batch checks · WhatsApp chatbot front-end.
