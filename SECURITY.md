# Safety and privacy

This is a local, single-process demo for trusted users, not a public multi-user service.

## Data handling
Prompts and retrieved documentation can be sent to Google Gemini. Review the Gemini API terms and your project's billing/data settings before using real data. Do not submit passwords, credentials, personal records, or confidential documents. No prompt or response bodies are intentionally logged by the gateway.

The gateway keeps at most 500 sessions in RAM, with 100 messages per session. Sessions expire one hour after creation; expired entries are removed on the next session operation. Restarting the gateway also removes them. Reset deletes the current server-side conversation after a successful response. This does not delete data already processed by the model provider.

An administrator access token authorizes chat requests. Each conversation also has its own random capability token, required to read, append, or delete history. Both tokens remain in browser memory; reloading loses access. Do not share them. Limits are process-local: run a single gateway worker. Public hosting requires individual accounts, HTTPS, a shared quota store and a dedicated security review.

## Acceptable use and reporting
Do not use this demo for harassment, hate, exploitation, fraud, publishing private information without permission, or other uses prohibited by GitHub or Google Gemini. AI replies may be wrong. Model safety controls are not a complete abuse-prevention system, and this demo has no dedicated moderation service.

For a content problem, use Reset and stop the request. Report abuse to the deployment administrator privately. For a vulnerability, use the repository's private vulnerability reporting feature if enabled; otherwise contact the maintainer privately through their GitHub profile. Do not put credentials or personal chat transcripts in a public issue. An administrator can revoke access by rotating CHAT_API_TOKEN and restarting the service.

- https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies
- https://ai.google.dev/gemini-api/docs/usage-policies
- https://ai.google.dev/gemini-api/terms

## Images and repository hygiene
Every Docker build context excludes .env files, virtual environments, caches and Git metadata. Keep secrets in the local .env only. Never place a server secret in a VITE_ variable. The agent services have no published host ports, and the frontend and gateway bind only to 127.0.0.1.

Personal metadata already in published commits remains in history. Removing it requires a separately coordinated history rewrite and force push. Changing the local Git email only affects future commits.