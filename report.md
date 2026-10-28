I'll search for datasets and benchmarks on failure attribution in LLM multi-agent systems and compile them for you.

I found 20 datasets in four groups. Group 1 is the best fit for your problem: those datasets label which agent failed and at which step.

**1. Core MAS failure-attribution benchmarks (agent + decisive step)**

- **Who&When** (ICML 2025). This is the original benchmark for the task. It has failure logs from 127 LLM multi-agent systems, with annotations linking each failure to a specific agent and decisive error step. There are 184 annotated failure tasks built on GAIA and AssistantBench queries, split into Hand-Crafted and Algorithm-Generated subsets on Hugging Face (Kevin355/Who_and_When).
- **TraceElephant** (ACL 2026). It has 380 traces, 220 of them failed, from Captain-Agent, Magentic-One and SWE-Agent on GAIA, AssistantBench and SWE-Bench. Its main difference from Who&When: it keeps full execution traces and reproducible environments, and full traces raise attribution accuracy by up to 76.5% over partial observation.
- **MP-Bench** (ICML 2026). It drops the assumption of one root cause and allows several plausible ones. Only 16.2% of steps were marked as failure-inducing by all three annotators, and disagreement reached up to 60%. The code and dataset are at github.com/yeonjun-in/MP-Bench.
- **Who&When Pro** (ICML 2026). It replays a successful prefix exactly and then injects a failure, producing 12,326 failed trajectories with gold labels across 3 modalities and 26 benchmarks. The sources are 15 agentic frameworks covering text, image and video, with both single- and multi-agent setups.
- **LongRCA Bench** (2026). This one targets very long traces. It has 1,140 failed trajectories across five domains with no injected errors, human labels for the responsible role and earliest root-cause step, and a median length of 145 steps. A 200-trajectory LongRCA-Mini subset is available for cheaper screening.
- **AgentRx** (Microsoft, 2026). It has 115 manually annotated failed trajectories from τ-bench, Flash and Magentic-One, with a nine-category failure taxonomy. It is on Hugging Face as microsoft/AgentRx and requires accepting the terms.

**2. Large synthetic datasets, mainly for training attributors**

- **TracerTraj** (AgenTracer, ICLR 2026). More than 2,000 failure trajectories were generated with counterfactual replay and programmatic fault injection. Its test splits have 215 cases across three domains, and it is commonly evaluated alongside Who&When.
- **Aegis / Aegis-Bench** (ICLR 2026). It has 9,533 trajectories labeled with the faulty agents and error modes, made by an LLM that injects context-aware errors into successful runs. The sources are six MAS frameworks (LLM Debate, MacNet, AgentVerse, DyLAN, SmolAgents, Magentic-One) on MATH, SciBench, GSM8K, HumanEval, MMLU and GAIA.
- **CORRECT-Error** (ICML 2026). More than 2,000 annotated trajectories were built with an error-injection pipeline guided by real-world error distributions and then checked by humans.
- **AgentErrata** (2026). It is built by fault injection and balanced across failure categories for diagnosis benchmarks. Less public detail is available for this one.

**3. Failure-taxonomy datasets (failure-mode labels, mostly no step labels)**

- **MAST-Data / MAD** (NeurIPS 2025). It has 1,642 traces across 7 MAS frameworks, 8 benchmarks and 5 LLMs, with binary labels for 14 MAST failure modes. Those labels come from an LLM judge, not human annotators. A separate MAST-Data-human set has 21 traces, each labeled by three experts.
- **TRAIL** (Patronus AI). It has 148 human-annotated long-context traces containing 841 errors, built on GAIA and SWE-Bench, and includes both single- and multi-agent systems.

**4. Related trajectory-debugging datasets (mostly single-agent or one domain)**

These are useful for checking whether a method generalizes or for pretraining:

- **AgentErrorBench and AgentDebug-Traj2k.** AgentErrorBench has annotated failure trajectories from ALFWorld, GAIA and WebShop. Traj2k is a larger set produced by a proposer–reviewer pipeline.
- **SearchAuditBench.** It has 1,243 failed deep-search trajectories labeled with critical error steps, root causes and repair rubrics.
- **Failure as a Process.** It has 1,794 manually annotated CLI coding-agent trajectories (over 63,000 steps) from Terminal-Bench.
- **TrajErrBench** (from TrajDebug). It follows the Who&When decisive-error annotation protocol on τ²-Bench and SWE-Bench Pro failures.
- **AgentHallu.** It has 693 trajectories from 7 agent frameworks and focuses on finding the steps responsible for hallucinations.
- **Others:**
  - **MemTrace** targets agent memory failures; it has 160 traces.
  - **HORIZON** studies long-horizon failures; it has 3,100+ trajectories with failures attributed by an LLM judge.
  - **MegaRCA-Mix** is a small, hard test set; it has 50 human-annotated long-horizon failure trials.

**Recommendation.** For a standard evaluation, use Who&When, TraceElephant and MP-Bench. Add Who&When Pro or LongRCA if you need scale or long traces, and use TracerTraj or Aegis as training data. Several of the 2026 datasets are recent preprints, so check that their data has actually been released before you rely on them.

I can put this into a Sheets tracker with columns for size, label granularity, natural vs. injected errors, and download links.

Sources:
- [Who&When paper (arXiv 2505.00212)](https://arxiv.org/abs/2505.00212v3) · [Who&When HF dataset](https://huggingface.co/datasets/Kevin355/Who_and_When/blob/main/README.md)
- [TraceElephant (ACL 2026)](https://aclanthology.org/2026.acl-long.912/) · [arXiv PDF](https://arxiv.org/pdf/2604.22708)
- [MP-Bench (arXiv 2603.25001)](https://arxiv.org/html/2603.25001v1)
- [Who&When Pro (ICML 2026)](https://icml.cc/virtual/2026/77950) · [Emergent Mind summary](https://www.emergentmind.com/papers/2607.09996)
- [LongRCA Bench (arXiv 2608.15242)](https://arxiv.org/pdf/2608.15242)
- [AgentRx blog (Microsoft Research)](https://microsoft.com/en-us/research/blog/systematic-debugging-for-ai-agents-introducing-the-agentrx-framework)
- [AgenTracer / TracerTraj (ICLR 2026)](https://iclr.cc/virtual/2026/poster/10007726)
- [Aegis (ICLR 2026)](https://iclr.cc/virtual/2026/poster/10006419) · [VerifyMAS dataset details](https://arxiv.org/pdf/2605.17467)
- [CORRECT / CORRECT-Error](https://www.amazon.science/publications/correct-condensed-error-recognition-via-knowledge-transfer-in-multi-agent-systems)
- [AgentErrata (arXiv 2609.02371)](https://arxiv.org/pdf/2609.02371)
- [MAST-Data HF](https://huggingface.co/datasets/mcemri/MAST-Data) · [MAST paper](https://arxiv.org/html/2503.13657v3)
- [TRAIL (Patronus AI)](https://www.patronus.ai/blog/introducing-trail-a-benchmark-for-agentic-evaluation)
- [AgentDebug / AgentErrorBench](https://icml.cc/virtual/2026/77923)
- [SearchAuditor](https://arxiv.org/pdf/2608.05212)
- [Failure as a Process](https://huggingface.co/papers/2607.09510)
- [TrajDebug](https://arxiv.org/pdf/2608.06346)
- [AgentHallu](https://arxiv.org/html/2601.06818v1)
- [HORIZON](https://papers.cool/arxiv/2604.11978)
- [MegaRCA-Mix](https://huggingface.co/papers/2609.13463)
