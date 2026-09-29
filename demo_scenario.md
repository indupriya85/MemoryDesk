# MemoryDesk Demo Scenario

## Interaction 1

Customer ID: customer-demo-001

User:
"My card payment keeps failing when I try to purchase something online. I usually use the mobile app."

Expected behavior:
The agent helps troubleshoot the issue and stores the conversation in Hindsight.

## Interaction 2

Restart the app or use the same Customer ID.

User:
"The payment problem happened again."

Expected behavior:
The agent recalls the earlier payment issue and mobile-app context instead of treating the customer as completely new.

## What to show judges

1. First interaction with no useful previous memory.
2. Hindsight memory being stored.
3. Later interaction using the same Customer ID.
4. Hindsight recall appearing in the Memory panel.
5. A response that clearly uses relevant previous context.

The important story is:

Without memory -> generic support.

With Hindsight -> continuity and personalization.
