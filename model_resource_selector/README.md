# Model Resource Selector Cell

This cell keeps agentic automation cheap, modular and auditable. It chooses a
small model/resource profile for each automation need instead of defaulting to an
expensive frontier model.

Selection rules:

- public/non-sensitive work can use free public quotas,
- private work prefers local/self-hosted recovered hardware,
- high-cost GPU/local workloads require an energy justification, ideally OZE or
  otherwise free/low-cost energy,
- every choice is a recommendation artifact, not a hidden runtime switch.
