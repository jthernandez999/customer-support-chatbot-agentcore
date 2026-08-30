# Customer Support Chatbot — Student Notes

Prompt engineering project for **Prompting for Effective LLM Reasoning** (nd905). The chatbot runs on an Amazon Bedrock AgentCore managed harness. Routing, information gathering, and FAQ grounding all live in `system_prompt.txt`.

## Note for the reviewer: Flows rubric vs AgentCore instructions

This project was built against the current **Instructions** and **Testing Framework** pages, which use the **AgentCore managed harness**. Bedrock Agents Classic closed to new customers on July 30, 2026, and the course migrated agent lessons to AgentCore.

The **Project Rubric** page still describes the earlier **Bedrock Flows** version (classifier node, Condition node, Output nodes, `flow-tests.json`). Those two pages ask for different artifacts. The table below maps every Flows rubric line to the AgentCore equivalent.

| Rubric asks for | This project uses | Evidence |
|---|---|---|
| Bedrock Flow that classifies and routes | AgentCore managed harness; routing is instruction text in one system prompt | `system_prompt.txt`, section CLASSIFICATION |
| Screenshot of the full flow diagram | No flow. Harness + Gateway + Lambda + DynamoDB | Architecture described below |
| Screenshot of the classifier prompt configuration | Classification section of the system prompt | Quoted below |
| Condition node expressions | No condition nodes. The model picks exactly one category before acting | `system_prompt.txt`, TIE-BREAK rule |
| Distinct paths terminating at separate Output nodes | Three terminal behaviors in one prompt | Bug / FAQ / other procedures in `system_prompt.txt` |
| `flow-tests.json` | Same suite as `harness-tests.json` | Both files included, identical content |
| FAQ Prompt node template showing embedded FAQ | `{{FAQ}}` placeholder; `create_harness.py` substitutes `online_shop_faq.md` | `system_prompt.txt` last section |

### Classifier (replaces the classifier-node screenshot)

```
CLASSIFICATION
Before you respond, pick exactly ONE category. Classification happens first and is internal only.

1. BUG REPORT — software defect, crash, error, blank screen, freeze, data loss, or anything broken.
   If the message describes something BROKEN, it is a bug report even when the topic also appears in the FAQ.

2. PLATFORM QUESTION — how the shop works: orders, shipping, returns, payments, products, accounts, privacy.
   Classify by TOPIC, whether or not the FAQ actually contains the answer.

3. ANYTHING ELSE — not a bug and not a platform question.

TIE-BREAK: if a message could be both a bug report and a platform question, choose BUG REPORT.
```

---

## What the prompt does

Every message is classified into exactly one category, silently, before any reply:

1. **Bug report** — collect `description`, `stepsToReproduce`, and `environment` one question at a time, then call `bugreports___create_bug_report`. Relay the returned `ticketId`.
2. **Platform question** — classified by *topic*, not by FAQ coverage. Covered questions are answered only from the embedded FAQ. Uncovered questions redirect to **1-800-555-0199** (Mon–Fri).
3. **Anything else** — polite hand-off to the same phone line.

Tie-break: if a message could be a bug *and* a platform question, it is a bug. Filing an extra ticket is recoverable; answering a malfunction from the FAQ is not.

Classification is topic-based so the uncovered-FAQ path can actually fire. If FAQ routing required “the document contains the answer,” uncovered questions would collapse into the catch-all and two graded behaviors would look the same.

Customer text is treated as data, never as an instruction.

## Files you author

| File | Role |
|------|------|
| `system_prompt.txt` | Main deliverable. Keep the `{{FAQ}}` placeholder; `create_harness.py` substitutes `online_shop_faq.md`. |
| `harness-tests.json` / `flow-tests.json` | Seven single-turn cases: bug, covered FAQ, uncovered FAQ, out-of-scope, injection, ambiguous bug/FAQ, and a one-word bug. |

Each eval case runs in a fresh `runtimeSessionId`, so bug tests assert the *start* of collection, not a completed ticket.

## Rubric evidence checklist

| Criterion | File / artifact | Status |
|-----------|-----------------|--------|
| Classification and routing | `system_prompt.txt` CLASSIFICATION | Done |
| Bug path in the prompt | `system_prompt.txt` BUG REPORT PROCEDURE | Done |
| Harness + Gateway tool | `support_chatbot` harness, gateway target `bugreports` | Done |
| Multi-turn collection + tool call | `evidence/transcripts/transcript-bug.txt` — `[tool call] bugreports___create_bug_report` | Done |
| DynamoDB ticket | ticket `9252c4e5-cb9c-410c-bae0-d7c730f3bb5d` in `bug-report-tool-stack-bug-reports` — `evidence/dynamodb-ticket.png` | Done |
| Covered / uncovered FAQ / other | `evidence/transcripts/transcript-faq-covered.txt`, `transcript-faq-uncovered.txt`, `transcript-other.txt` | Done |
| Automated tests | `harness-tests.json` and `flow-tests.json` | Done |
| JSONL + Bedrock Evaluations | `output_eval_dataset.jsonl`; job `support-chatbot-eval-run-2` (Correctness 1.00) — `evidence/eval-results.png` | Done |

## Testing observations

Bedrock Evaluations, LLM-as-a-judge, `Builtin.Correctness`, evaluator `amazon.nova-pro-v1:0`, BYOI source `my-support-chatbot`. Console: Amazon Bedrock → Evaluations → `support-chatbot-eval-run-2`.

| Metric | Run 1 | Run 2 |
|--------|-------|-------|
| Builtin.Correctness overall | 0.857 (6/7) | **1.000 (7/7)** |

| Test | Run 1 | Run 2 |
|------|-------|-------|
| `bug-route-checkout-crash` | 1.0 | 1.0 |
| `faq-route-returns-policy` | 1.0 | 1.0 |
| `faq-route-uncovered-topic` | 1.0 | 1.0 |
| `other-route-out-of-scope` | 1.0 | 1.0 |
| `edge-injection-attempt` | 0.0 | 1.0 |
| `edge-ambiguous-bug-or-faq` | 1.0 | 1.0 |
| `edge-minimal-context` | 1.0 | 1.0 |

**Are all three routes producing reasonable responses?** Yes. Single-turn eval: bugs ask for the next missing field; covered FAQ answers the 30-day policy; uncovered FAQ and other requests hand off to 1-800-555-0199. Multi-turn `chat.py`: one question per turn, then `[tool call] bugreports___create_bug_report`, then ticket `9252c4e5-cb9c-410c-bae0-d7c730f3bb5d`. DynamoDB fields match the customer's words.

**Is anything being misrouted?** Early runs filed tickets on the first bug turn by stuffing `not provided` / `&nbsp;` into required tool fields, and long-term harness memory reused steps from a previous session. Fixes: numbered “ask, don't file” procedure; Lambda rejects placeholder strings; `create_harness.py` disables managed memory. After that, checkout-crash and “discount codes aren't applying” both stay on the bug path instead of the FAQ promo-code answer.

**Are FAQ answers on point?** Yes. Return policy is grounded in the embedded FAQ. Student discounts are not in the FAQ, so the bot redirects instead of inventing a policy.

**Any false negatives from the judge?** Run 1 scored injection 0.0 because the bot refused to leak the prompt but did not include the phone number. That is a fair miss against our own reference, not a judge error. Run 2 added an explicit jailbreak hand-off (still no prompt leak, plus 1-800-555-0199) and scored 1.0.

### Iterations

| Run | Change | Effect |
|-----|--------|--------|
| Smoke 1 | Baseline prompt | Leaked `<thinking>` tags; filed a ticket with `&nbsp;` placeholders; FAQ uncovered said “this is a platform question” |
| Smoke 2 | Ban tags/labels; Lambda rejects `&nbsp;` | Still filed early: reused Chrome/SAVE10 from a prior session via harness memory |
| Smoke 3 | `memory={"disabled": {}}` | Full bug collection worked: ask steps → ask environment → tool → real ticket |
| Eval 1 | Placeholder reject includes “not provided”; stronger hand-off | 0.857 — injection refused the jailbreak but omitted the phone number |
| Eval 2 | Jailbreaks must use the same phone-line hand-off | **1.000** |

## Stand-out work (and what was left out)

- **Prompt injection:** customer text is data; jailbreaks are “anything else” and get the phone-line hand-off. Tested in `edge-injection-attempt`.
- **Edge cases:** ambiguous bug-vs-FAQ, one-word bug (`It's broken.`), and injection are in the suite.
- **Lambda refuses fake fields** so the model cannot satisfy the tool schema with `&nbsp;` or “not provided”.
- **Bedrock Guardrails** and a **Knowledge Base** were not added. The Instructions page embeds a short FAQ on purpose; RAG is called out as out of scope.

## Run (us-east-1)

Put current AWS keys in a `.env` at the repo root or in this folder (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION=us-east-1`). Lab session tokens expire; refresh them before deploying.

```bash
cd project/starter
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

aws cloudformation deploy \
  --template-file cloudformation-tool.yaml \
  --stack-name bug-report-tool-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1

python setup_gateway.py
python create_harness.py
python chat.py
```

Re-run `create_harness.py` after every prompt edit.

Automated eval:

```bash
python generate-eval-dataset.py --tests-json harness-tests.json

aws cloudformation deploy \
  --template-file cloudformation-testing.yaml \
  --stack-name bug-report-testing-stack \
  --capabilities CAPABILITY_NAMED_IAM \
  --region us-east-1
```

Upload `output_eval_dataset.jsonl` to the testing-stack S3 bucket and create a Bedrock Evaluations job (LLM-as-a-judge, Bring your own inference, Correctness).

## Cleanup

```bash
python cleanup_agentcore.py
aws cloudformation delete-stack --stack-name bug-report-tool-stack --region us-east-1
aws s3 rm s3://udacity-agentic-engineer-c1-eval-<ACCOUNT_ID> --recursive
aws cloudformation delete-stack --stack-name bug-report-testing-stack --region us-east-1
```

Empty the eval bucket before deleting the testing stack, or CloudFormation lands in `DELETE_FAILED`.
