# Customer Support Chatbot with Amazon Bedrock AgentCore

Course project for **Prompting for Effective LLM Reasoning** (nd905). A support chatbot for a fictional online shop. Routing, bug-report collection, and FAQ answering live in a single system prompt. The AgentCore managed harness runs the agent loop, session memory, and tool calls.

## Three behaviors

1. **Bug reports** — collect description, steps to reproduce, and environment over the conversation, then file a ticket with `bugreports___create_bug_report`.
2. **Platform questions** — answer from the FAQ embedded in the prompt. If the FAQ does not cover the question, redirect to 1-800-555-0199 (Mon–Fri).
3. **Anything else** — polite hand-off to the same phone line.

## Project files

Work from `project/starter/`. Notes, rubric mapping, and evaluation observations are in [`project/starter/README.md`](project/starter/README.md).

| File | Role |
|------|------|
| `project/starter/system_prompt.txt` | System prompt (main deliverable) |
| `project/starter/harness-tests.json` | Automated test suite |
| `project/starter/flow-tests.json` | Same suite (filename from the Flows-era rubric) |
| `project/starter/evidence/` | Chat transcripts and Bedrock Evaluations output |

## Setup

Requires AWS credentials for **us-east-1**, Bedrock + AgentCore access, and `us.amazon.nova-pro-v1:0`.

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

```bash
python generate-eval-dataset.py --tests-json harness-tests.json
```

Best evaluation job: **support-chatbot-eval-run-2**, Builtin.Correctness **1.000** (7/7).
