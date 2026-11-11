"""Build data/intent_dataset.json for CTX-001 (intent router).

14 topic groups x 5 queries x 4 intents = 280 queries.
Split is done per GROUP (not per line) so near-duplicate wording never
crosses train/validation/test. Per intent: 10 groups train, 2 validation,
2 test -> 200 / 40 / 40 overall (about 71 / 14 / 14 percent).

Usage:  python build_intent_dataset.py [output_path]
"""
import json
import random
import sys
from pathlib import Path

SEED = 42
MAX_QUERY_CHARS = 1_000

DATA = {
    "finance": [
        [
            "Extract the line items from this invoice",
            "Pull the total amount and due date from the attached bill",
            "Can you read the vendor name and invoice number from this PDF?",
            "Parse invoice INV-2048 into a table",
            "Invoice se total amount nikaalo",
        ],
        [
            "Generate a billing report for last quarter",
            "Show me the monthly billing summary for October",
            "I need a breakdown of charges by customer",
            "Create a revenue report for the third quarter",
            "Give me an itemized statement for account 4471",
        ],
        [
            "Which invoices are still unpaid?",
            "List all overdue payments from vendors",
            "Has the payment for PO 8812 been received?",
            "Show pending payables due this week",
            "¿Cuántas facturas están pendientes de pago?",
        ],
        [
            "Extract the amount from this receipt",
            "Categorize my travel expenses from the last trip",
            "Scan this restaurant receipt and log the expense",
            "What is the total of all receipts uploaded today?",
            "Add this taxi bill to my expense report",
        ],
        [
            "Match this purchase order to the supplier invoice",
            "Read the quantities and unit prices from the PO",
            "Is the PO total the same as the invoice total?",
            "Extract the shipping address and items from this purchase order",
            "Create a summary of all open purchase orders",
        ],
        [
            "Calculate the GST on this invoice",
            "What is the tax amount charged on the bill?",
            "Pull the VAT number from this document",
            "Prepare the tax summary for the quarter",
            "GST ka amount kitna hai is bill mein",
        ],
        [
            "Reconcile the bank statement with the ledger",
            "Find mismatches between invoices and payments",
            "Flag duplicate invoices from the same vendor",
            "Check whether any invoice was billed twice",
            "Compare vendor statements against our records",
        ],
        [
            "Process a refund for order 5521",
            "Issue a credit note for the returned goods",
            "How much do we owe this customer after the refund?",
            "Show all credit notes from September",
            "Calculate the prorated refund for a cancelled subscription",
        ],
        [
            "Why was I charged twice this month?",
            "Explain the extra charge on my latest bill",
            "What is the billing cycle for the enterprise plan?",
            "When is my next invoice due?",
            "Send me a copy of last month's invoice",
        ],
        [
            "Summarize the profit and loss statement",
            "Extract the balance sheet figures from the annual report",
            "What were total operating expenses in Q2?",
            "Pull the net income from this financial statement",
            "Compare this year's expenses with last year's",
        ],
        [
            "What are the payment terms in this vendor contract?",
            "Extract the penalty clause amounts from the agreement",
            "Find the net 30 terms in this supplier document",
            "How much is the late fee on this invoice?",
            "Read the total contract value from the document",
        ],
        [
            "Extract the salary components from this payslip",
            "Calculate total payroll cost for the month",
            "Show the deductions listed on this pay slip",
            "Summarize reimbursements paid to employees in March",
            "Process the vendor payment batch for Friday",
        ],
        [
            "Convert the invoice total from USD to INR",
            "What is the invoice amount in euros?",
            "Sum the amounts in column D of this bill",
            "Round the invoice subtotal and show the discount applied",
            "List invoices above 50,000 rupees",
        ],
        [
            "Generate the Q3 billing report and tell me if the export failed",
            "Extract the invoice total and then notify the finance team",
            "Pull the billing data and also tell me who handled it",
            "Pay the invoice and look for a similar earlier bill",
            "Download the billing report, the app was slow earlier",
        ],
    ],
    "support": [
        [
            "The app crashes every time I open settings",
            "Mobile app freezes on the checkout screen",
            "Fix the crash bug in the login module",
            "The dashboard keeps closing unexpectedly",
            "La aplicación se cierra sola al abrir",
        ],
        [
            "I can't log in to my account",
            "Password reset email never arrives",
            "My two-factor code is not working",
            "Account locked after too many attempts",
            "Mera login nahi ho raha hai",
        ],
        [
            "I am getting a 500 error on the upload page",
            "API returns 403 forbidden for valid tokens",
            "Page shows a blank screen after sign in",
            "Stack trace shows a null pointer exception in the payment service",
            "Timeout error when saving the form",
        ],
        [
            "The website is extremely slow today",
            "Reports take over a minute to load",
            "Search results are lagging badly",
            "Why is the app using so much memory?",
            "Response times doubled after the last release",
        ],
        [
            "Is the service down right now?",
            "Our whole team cannot access the platform",
            "Production API has been unreachable since morning",
            "Users report intermittent downtime",
            "Check the incident status for the email system",
        ],
        [
            "Open a support ticket for a broken export button",
            "Escalate ticket 3321 to the engineering team",
            "Assign this customer complaint to the right team",
            "Prioritize the open bug reports by severity",
            "Close the ticket, the issue is resolved",
        ],
        [
            "Report a bug: dates show the wrong timezone",
            "Notifications are sent twice to users",
            "The save button does nothing when clicked",
            "Uploaded images appear rotated",
            "Dropdown menu is not showing all options",
        ],
        [
            "The Slack integration stopped syncing",
            "Webhook events are not being delivered",
            "Email notifications are not arriving",
            "Calendar sync fails with an authentication error",
            "My API key suddenly stopped working",
        ],
        [
            "I want to complain about the poor service I received",
            "Customer says the product arrived damaged",
            "Client is angry about repeated outages",
            "Help me respond to a frustrated user",
            "The user is asking why their request is still pending",
        ],
        [
            "How do I fix the sync error on my phone?",
            "Troubleshoot why the printer connection fails",
            "Steps to clear cache and restore the app",
            "Reinstalling did not solve the problem, what next?",
            "Installation fails at 90 percent",
        ],
        [
            "My uploaded file is corrupted after download",
            "Export to CSV produces empty rows",
            "The report shows wrong numbers after the update",
            "Data disappeared from my dashboard",
            "Profile photo will not upload",
        ],
        [
            "The latest deployment broke the build",
            "CI pipeline fails on the unit tests",
            "Rollback the release, users cannot sign in",
            "Memory leak detected in the worker service",
            "Investigate the spike in error logs",
        ],
        [
            "App won't install on my Android phone",
            "Push notifications stopped on iOS",
            "Screen turns black during video calls",
            "Bluetooth pairing keeps failing",
            "Camera does not open inside the app",
        ],
        [
            "The invoice page crashes when I open it",
            "I need help, the search bar stopped working",
            "Billing portal shows an error on login",
            "Workflow fails with a timeout, please check the logs",
            "Fix the crash and then let me know",
        ],
    ],
    "search": [
        [
            "What is our remote work policy?",
            "Find the leave policy for new employees",
            "Where can I read the code of conduct?",
            "What does the handbook say about travel reimbursement?",
            "¿Cuál es la política de vacaciones de la empresa?",
        ],
        [
            "Find documents about the Q3 roadmap",
            "Search the wiki for onboarding guides",
            "Show me the latest architecture overview",
            "Look up the design doc for the payments service",
            "Find meeting notes from last Tuesday's planning",
        ],
        [
            "Who is the head of the legal department?",
            "When was our company founded?",
            "How many offices do we have in Europe?",
            "What products does Attenomy offer?",
            "Hamari company ka mission kya hai",
        ],
        [
            "How does our refund approval process work?",
            "Explain how single sign-on is set up internally",
            "What is the escalation process for security incidents?",
            "Describe the data retention rules we follow",
            "How are customer tickets prioritized here?",
        ],
        [
            "What is the difference between SLA and SLO?",
            "Define churn rate as used in our reports",
            "What does the term ARR mean?",
            "Explain what a vector database is",
            "Meaning of RAG in simple words",
        ],
        [
            "Summarize what we know about competitor pricing",
            "What are best practices for API versioning?",
            "Find research on customer retention strategies",
            "Give me background on the GDPR requirements",
            "What are the main points in the security whitepaper?",
        ],
        [
            "Who owns the semantic cache module?",
            "Which team handles vendor onboarding?",
            "Find the contact for the infrastructure team",
            "Who wrote the incident postmortem for March?",
            "List members of the data science group",
        ],
        [
            "What changed in the last release notes?",
            "Show the history of the pricing page",
            "When did we update the privacy policy?",
            "Find previous discussions about moving to Kubernetes",
            "Which decisions were made in the Q2 review?",
        ],
        [
            "What are the office working hours?",
            "How do I request a new laptop?",
            "What is the process to book a meeting room?",
            "Where do I find the holiday calendar?",
            "Is there a guide for setting up VPN access?",
        ],
        [
            "What is the capital of France?",
            "Explain how transformers work in machine learning",
            "What is the time complexity of quicksort?",
            "Tell me about the history of the internet",
            "How tall is Mount Everest?",
        ],
        [
            "What are our data privacy obligations?",
            "Find the contract template for new clients",
            "What does the NDA cover?",
            "Look up the compliance checklist for audits",
            "Which regulations apply to storing customer data?",
        ],
        [
            "What features are included in the enterprise plan?",
            "Does the platform support single sign-on?",
            "Which file formats can the extractor read?",
            "How many users can one workspace have?",
            "What integrations are available?",
        ],
        [
            "Compare our two pricing tiers",
            "What are the pros and cons of ONNX versus PyTorch?",
            "Show articles related to zero-trust security",
            "Find similar past projects to this one",
            "Recommend reading about prompt engineering",
        ],
        [
            "onboarding guide",
            "security policy",
            "Tell me about the refund policy",
            "Any docs on the API rate limits?",
            "Account settings documentation",
        ],
    ],
    "orchestration": [
        [
            "Run the employee onboarding workflow",
            "Start the monthly close process",
            "Execute the data refresh pipeline now",
            "Kick off the weekly reporting workflow",
            "Lanza el flujo de trabajo de aprobación",
        ],
        [
            "Schedule the report generation every Monday at 9 am",
            "Run the backup job every night at midnight",
            "Set up a recurring sync between CRM and warehouse",
            "Trigger the cleanup task at the end of each month",
            "Har subah 8 baje yeh workflow chalao",
        ],
        [
            "Extract the invoice, then validate it, then send it for approval",
            "First ingest the documents, after that index them",
            "Run extraction, then route the result to finance",
            "Chain the classifier and the summarizer agents together",
            "When the file arrives, parse it and notify the team",
        ],
        [
            "Automate the daily status email",
            "Create an automation that tags new leads",
            "Build a workflow that archives old tickets",
            "Set up auto-assignment for incoming requests",
            "Automatically escalate unresolved cases after 48 hours",
        ],
        [
            "Coordinate the research agent and the writing agent",
            "Assign this task to the planning agent",
            "Have the agents collaborate to prepare the board deck",
            "Spin up three agents to process the batch in parallel",
            "Hand over the output to the review agent",
        ],
        [
            "Trigger the deployment pipeline for staging",
            "Start the document ingestion pipeline for the new folder",
            "Fire the nightly ETL job",
            "Launch the model retraining pipeline",
            "Restart the failed pipeline run from step three",
        ],
        [
            "If the invoice is over 10k, send it to a manager for approval",
            "When a ticket is marked urgent, notify the on-call engineer",
            "Run step two only if step one succeeds",
            "Branch the workflow based on document type",
            "Retry the failed task three times, then alert me",
        ],
        [
            "Prepare the quarterly review: collect data, build slides, email the team",
            "Plan and execute the product launch checklist",
            "Run the full compliance audit workflow",
            "Orchestrate the end-to-end hiring process",
            "Execute all steps for the customer offboarding",
        ],
        [
            "Pause the onboarding workflow",
            "Show the status of all running workflows",
            "Cancel the scheduled export job",
            "Resume the paused pipeline from where it stopped",
            "Which workflows are currently queued?",
        ],
        [
            "Sync the CRM contacts to the marketing tool and send a summary",
            "Move new form submissions into the database and alert sales",
            "Connect the inbox to the ticketing system with a rule",
            "Post the daily metrics to Slack automatically",
            "Push the approved report to the shared drive",
        ],
        [
            "Process all 500 documents in parallel",
            "Run the same analysis for every region simultaneously",
            "Batch the pending tasks and run them overnight",
            "Fan out the request to all available agents",
            "Split the job into chunks and merge the results",
        ],
        [
            "Route this request through legal, then finance",
            "Send the draft to the manager and wait for approval",
            "Hand the ticket to the next team after review",
            "Create an approval flow for expense claims",
            "Loop in the security agent before deployment",
        ],
        [
            "Run workflow 7",
            "Execute pipeline daily_sync",
            "Start the agents",
            "Lance le pipeline d'ingestion maintenant",
            "Workflow shuru karo",
        ],
        [
            "Search the policy docs and then run the approval workflow",
            "Check the invoice and trigger the payment flow",
            "Investigate the error and restart the pipeline",
            "Look up the vendor, then start the onboarding workflow",
            "Find the latest report and email it to the team automatically",
        ],
    ],
}

N_TRAIN_GROUPS, N_VAL_GROUPS, N_TEST_GROUPS = 10, 2, 2
HARD = 13  # index of the mixed / ambiguous group in every intent (14th group)
# Ambiguous groups never go to train; they are used to calibrate and to test fallback.
HARD_SPLIT = {
    "finance": "validation",
    "search": "validation",
    "support": "test",
    "orchestration": "test",
}


def build():
    rng = random.Random(SEED)
    samples = []
    for intent, groups in DATA.items():
        assert len(groups) == 14, f"{intent}: expected 14 groups, got {len(groups)}"
        for g in groups:
            assert len(g) == 5, f"{intent}: every group needs 5 queries"
        # shuffle only the 13 normal groups; the ambiguous group is placed explicitly
        order = [i for i in range(len(groups)) if i != HARD]
        rng.shuffle(order)
        n_val = N_VAL_GROUPS - (HARD_SPLIT[intent] == "validation")
        split_of = {HARD: HARD_SPLIT[intent]}
        for pos, gi in enumerate(order):
            if pos < N_TRAIN_GROUPS:
                split_of[gi] = "train"
            elif pos < N_TRAIN_GROUPS + n_val:
                split_of[gi] = "validation"
            else:
                split_of[gi] = "test"
        for gi, group in enumerate(groups):
            for qi, text in enumerate(group):
                samples.append(
                    {
                        "id": f"{intent[:3]}-{gi + 1:02d}-{qi + 1}",
                        "text": text,
                        "label": intent,
                        "group": f"{intent}-{gi + 1:02d}",
                        "split": split_of[gi],
                        "ambiguous": gi == HARD,
                    }
                )
    return samples


def validate(samples):
    seen = {}
    for s in samples:
        key = s["text"].strip().lower()
        assert key not in seen, f"duplicate text: {s['text']!r}"
        seen[key] = s["id"]
        assert s["text"].strip(), f"blank text in {s['id']}"
        assert len(s["text"]) <= MAX_QUERY_CHARS, f"too long: {s['id']}"
    group_splits = {}
    for s in samples:
        group_splits.setdefault(s["group"], set()).add(s["split"])
    assert all(len(v) == 1 for v in group_splits.values()), "group leaked across splits"
    assert not any(s["ambiguous"] and s["split"] == "train" for s in samples), \
        "ambiguous queries must not be in train"


def summarize(samples):
    counts = {}
    for s in samples:
        counts.setdefault(s["split"], {}).setdefault(s["label"], 0)
        counts[s["split"]][s["label"]] += 1
    return counts


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "data/intent_dataset.json")
    samples = build()
    validate(samples)
    counts = summarize(samples)
    totals = {k: sum(v.values()) for k, v in counts.items()}
    n_ambiguous = {
        sp: sum(1 for s in samples if s["split"] == sp and s["ambiguous"])
        for sp in totals
    }
    doc = {
        "meta": {
            "ticket": "CTX-001",
            "seed": SEED,
            "labels": list(DATA.keys()),
            "total": len(samples),
            "split_method": (
                "grouped by topic, per intent: 10 train / 2 validation / 2 test groups; "
                "the ambiguous group of each intent is held out of train "
                "(finance, search -> validation; support, orchestration -> test)"
            ),
            "split_totals": totals,
            "per_split_per_label": counts,
            "ambiguous_per_split": n_ambiguous,
            "note": "Noise, gibberish and injection strings are NOT in this file; they are a separate stress set for tests.",
        },
        "samples": samples,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {out}  total={len(samples)}  splits={totals}  ambiguous={n_ambiguous}")
    for split, per in counts.items():
        print(f"  {split}: {per}")


if __name__ == "__main__":
    main()
