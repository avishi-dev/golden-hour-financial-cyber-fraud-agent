# Golden Hour — Financial Fraud First Response

Golden Hour coordinates a financial-cyberfraud first-response workflow through ASI:One and Fetch.ai uAgents. It turns an incomplete report into reviewed facts, discrepancy questions, a source-linked action bundle, an approval-bound test email, and a persisted follow-up state.

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)

## Scope and truth boundary

This repository implements a bounded demonstration. It does not file a government complaint, freeze funds, authenticate evidence, guarantee recovery, or impersonate a bank or police service. Public/demo data must be synthetic. The email action is restricted to `DEMO_RECIPIENT_EMAIL` and is disabled unless explicitly enabled.

## Implementation plan

### Milestone 0 — platform and safety gate
1. Confirm ASI:One and Agentverse accounts, API access, event rules, and a reachable deployment path.
2. Lock the supported ASI:One model (`asi1` initially) and uAgents/ACP versions after a smoke test.
3. Keep secrets in environment/deployment secret storage; never in case records or source control.

### Milestone 1 — Coordinator, ACP, and durable case state
1. Run the Coordinator as an ACP-compatible uAgent.
2. Accept multi-turn text, acknowledge promptly, persist a case, and return a safe urgent-action response immediately.
3. Use ASI1 tool calling for typed intake extraction and next-action selection, bounded to four tool cycles per turn.
4. Register/connect the reachable agent in Agentverse and publish a truthful profile with discovery keywords.

### Milestone 2 — reviewed evidence and response bundle
1. Send a typed `AnalyzeEvidenceRequest` from Coordinator to the Evidence Agent.
2. Extract facts into strict schemas, keep evidence untrusted, detect duplicates/contradictions/injection signals, and ask targeted questions.
3. Send only validated facts to the Response Agent; create the bank email draft, 1930 brief, NCRP narrative, and missing-facts checklist.
4. Add deterministic totals, hash/manifest records, and a PDF export with an unofficial-document label.

### Milestone 3 — approval-bound execution
1. Create an exact approval record binding case version, recipient, body, attachments, payload digest, expiry, and action type.
2. Make the Action Executor resolve the recipient only from trusted configuration.
3. Send exactly once using an idempotency key; persist provider/job status and distinguish accepted, delivered, failed, and unknown.
4. Add a supported reminder adapter, cancellation, restart recovery, and reconciliation before retry.

### Milestone 4 — live ASI:One/Agentverse proof
1. Run the Coordinator and workers on a persistent host with durable storage.
2. Register the main agent and available worker profiles in Agentverse; record real addresses and profile URLs only after registration.
3. Test direct invocation and natural-language discovery in ASI:One.
4. Record a sanitized shared-chat demonstration: incomplete case, corrected contradiction, review/approval, test send, and failure recovery.

### Milestone 5 — reliability and submission
1. Run injection, stale-approval, duplicate-send, restart, and forced-failure tests.
2. Add the three ASI:One card interactions only after the text workflow works; retain a complete text fallback.
3. Prepare public repository instructions, a 3–5 minute demo, limitations, deployment costs, and verified links.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
pytest
python -m golden_hour
```

For ASI1, set `ASI_ONE_API_KEY`. For a real agent identity, set `AGENT_SEED_PHRASE`. For Agentverse/ACP registration, use a public HTTPS endpoint after local smoke tests and set `AGENTVERSE_API_KEY` only in the deployment environment.

Start the ACP Coordinator locally after setting a secret seed:

```bash
AGENT_SEED_PHRASE='local-only-secret' .venv/bin/python -m golden_hour.agent
```

Use `AGENT_MAILBOX=true` for the mailbox deployment path documented by Fetch. Do not copy a local-only endpoint into Agentverse; registration requires a reachable HTTPS endpoint.

## References
- ASI:One tool calling: https://docs.asi1.ai/documentation/build-with-asi-one/tool-calling
- ASI:One quickstart: https://docs.asi1.ai/documentation/getting-started/quickstart
- Fetch Agent Chat Protocol: https://innovationlab.fetch.ai/resources/docs/agent-communication/agent-chat-protocol
- Fetch uAgent creation and Agentverse registration: https://innovationlab.fetch.ai/resources/docs/agent-creation/uagent-creation
