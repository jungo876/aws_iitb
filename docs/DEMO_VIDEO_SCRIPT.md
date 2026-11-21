# Demo video script (target 2:40, hard limit 3:00)

Record the screen with OBS or the Windows Game Bar (Win+Alt+R), plus a phone if you can. Speak calmly. Use the live CloudFront URL, not localhost.

| Time | Screen | Voice-over |
|---|---|---|
| 0:00–0:20 | Home page; zoom on the PRIYANKA ≠ PRIANKA card | "Every year, lakhs of students apply for scholarships paid through DBT. The portals compare your Aadhaar, bank account and certificates *letter by letter*. One missing **Y** in your name at the bank, and your scholarship gets stuck, and you find out months later." |
| 0:20–0:35 | Scroll the three steps | "KagazCheck is a one-minute pre-check. Snap your documents, and it finds the mismatches that cause rejections *before* you apply, then tells you exactly how to fix them, in your language." |
| 0:35–1:05 | Click **Try with sample documents**; show 5 docs being read; open Review | "Here's Priyanka, a fictional student from Gaya. Amazon Bedrock's Nova model reads all five documents in seconds. Notice the Aadhaar number is masked to the last four digits, and nothing is stored. She can correct anything the AI read wrongly." |
| 1:05–1:45 | Click **Find problems**; show score 60 and the two issues | "Two problems. First, the bank wrote PRIANKA instead of PRIYANKA. Our Indian-name matcher knows the difference between a spelling error, initials, a missing surname, or an account in her father's name, because each needs a different fix. Second, her income certificate is 20 months old. Each problem comes with exact steps: go to the bank with Aadhaar, ask for a name correction, and ask for DBT seeding in the same visit." |
| 1:45–2:10 | Switch to हिं; press **Listen**; switch language to Marathi/Tamil | "Most applicants are more comfortable in Hindi or their own language. The whole report switches to Hindi, Amazon Polly reads it aloud for students or parents who prefer listening, and Amazon Translate covers ten more Indian languages." |
| 2:10–2:20 | Tap **Share on WhatsApp** | "One tap sends the fix-list to a parent or the college scholarship cell on WhatsApp." |
| 2:20–2:35 | Insights page | "Every check adds to anonymous statistics. A college can see the most common blocker among its students and run a single bank camp instead of 500 separate trips." |
| 2:35–2:50 | Architecture slide (from BUILD_SUMMARY) | "It runs serverless on AWS in Mumbai: CloudFront, Lambda, Bedrock, Textract as fallback, Translate, Polly and DynamoDB, all on the Free Tier." |
| 2:50–3:00 | Back to home | "KagazCheck. Pehle jaanch, phir apply. Check first, then apply, so no student loses a scholarship to a spelling." |

**Demo Day (3 min live + 2 min Q&A).** Same flow. Have the sample flow pre-loaded in one tab and a *real* phone photo of a friend's passbook (with consent) ready to show it works on real documents.

Likely judge questions:
- *"What if the AI reads wrongly?"* The student confirms every field. The LLM only extracts; rules decide; advice is human-written.
- *"Privacy of Aadhaar?"* In-memory only, never stored; numbers masked twice; Mumbai region; only anonymous counters saved.
- *"Why not just fuzzy matching?"* Portals do exact matching. We need to tell the student *what type* of mismatch it is, because the fix differs (bank KYC, Aadhaar update with lifetime limits, board correction).
- *"How do you know it helps?"* The Insights page measures blocking problems caught before submission. Next step is piloting with a college scholarship cell.
- *"Cost at scale?"* About one paisa or less per check with Nova Lite; everything else is serverless and pay-per-use.
