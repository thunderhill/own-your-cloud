# Chapter 18 — Reclaiming the Margin

> *The question is no longer whether you can afford to become your own cloud provider, but whether you can afford not to.*
>
> — *Reclaiming Margins with Sovereign Cloud*, strategic briefing, February 2026

*Meridian · a Friday in September 2026 · the CFO's office*

The chief financial officer had a single slide on his screen, and he had clearly been waiting all week to show it to someone.

Two columns. *Managed Cloud (5-Year): $12.5M — escalating costs, no equity.* *Sovereign Cloud (5-Year): $8.2M — predictable costs, asset value.* And across the bottom, in green: *Net Savings: $4.3M (34% reduction) + owned infrastructure assets.*

"A consultant sent it," he said. "It's the number I asked you for a year ago. Which parts of the bill are rent. I want it in the board pack."

Anita read it twice. "Whose twelve and a half million?"

"An enterprise like ours, apparently."

"Then it isn't ours." She sat down. "I'm not saying it's wrong. I'm saying I can't defend it, because I can't find any of it on our invoice. Can we take it apart before the board does?"

The CFO looked at the green line for a moment, then closed the slide and opened a blank spreadsheet. "Line by line," he said. "Go on, then."

* * *

## The slide

*Briefing · February 2026*

The slide is the fifth and last chapter of the strategy deck behind this book, and it is the most quoted. It compares five-year total cost of ownership — the full cost of an option over its life, not just its first invoice — for a managed cloud and a self-managed sovereign cloud:

| | Five-year cost | The deck's description |
|---|---|---|
| Managed cloud | **$12.5M** | *"Escalating costs, no equity"* |
| Sovereign cloud | **$8.2M** | *"Predictable costs, asset value"* |
| Net saving | **$4.3M (34%)** | *"+ owned infrastructure assets"* |

It explains the saving with four *"Cost Elimination Factors"*:

| Factor | Saving | The deck's description |
|---|---|---|
| Success Tax elimination | −$1.8M | *"No more exponential scaling fees"* |
| Innovation Tax removal | −$1.2M | *"Stop paying premium for stagnation"* |
| Vendor licensing savings | −$900K | *"Open-source alternatives"* |
| Infrastructure optimization | −$400K | *"Right-sized for actual workloads"* |

Elsewhere, the deck adds the numbers a board will ask about next: *"20–35% Cost Reduction"*, a *"5–7yr Payback Period"*, *"12–18 months to full production readiness"*, an *"Initial Investment: $2–5M for mid-size enterprise deployment"*, and a *"3–5 Year Timeline"* for the whole transformation.

None of these figures has a source. They describe an illustrative enterprise, not a measured one. That doesn't make the slide useless. It means the slide has to be read the way a CFO reads any model: by asking whether it holds together.

## Three questions for any TCO slide

### Do the parts add up?

They do, exactly. $1.8M + $1.2M + $0.9M + $0.4M is $4.3M, which is $12.5M minus $8.2M, which is a 34.4% reduction.

That exactness is the problem. All four lines are *savings*. There is no line for anything owning *adds*. Yet the deck's own previous chapter lists what a self-managed platform requires: hardware; data-centre facilities; a platform engineering team of *"Kubernetes experts, DevOps, SRE specialists"*; automation and tooling; operational processes. The migration itself costs money, and so does the period of paying for both the old estate and the new one. If the four savings add up exactly to the net figure, every one of those costs is either hidden inside the four lines or missing from the model.

### Can you find the lines on an invoice?

Two of the four, yes. Licences are an invoice line, and so is infrastructure you can right-size.

The other two are not. *"Success Tax elimination"* and *"Innovation Tax removal"* are the deck's names for two ideas from Chapter 1: that costs grow with success, and that money spent standing still is money not spent building. Both are real ideas. Neither is an account. Together they are **$3.0M of the $4.3M — about 70% of the saving** — sitting in lines no finance system records.

### Do the slides agree with each other?

A 34% saving over five years, and a payback of five to seven years, are hard to hold at the same time. Payback is how long it takes the savings to repay the initial investment. If the model saves money within five years, it has paid back within five years.

The two agree only under assumptions the deck doesn't state. Take the deck's own initial investment of $2–5 million, and suppose the $8.2 million *leaves it out*:

| Initial investment | Five-year cost of owning | Five-year saving |
|---|---|---|
| $2.0M | $10.2M | **+$2.3M (18%)** |
| $3.5M | $11.7M | **+$0.8M (6%)** |
| $5.0M | $13.2M | **−$0.7M (−6%)** |

Or suppose the $4.3 million is a steady saving of $0.86 million a year: then a $2 million investment pays back in **2.3 years**, and a $5 million one in **5.8 years**. The deck's five-to-seven-year payback fits only at the expensive end of its own range — where the five-year saving shrinks toward nothing, or turns negative.

None of this means the slide is wrong about the direction. It means the slide is a *shape*, not a number. Its real value is the list of lines. The amounts have to come from somewhere else.

## An asset that wears out

*Public record · 2022–2025*

The slide's right-hand column claims *"asset value"*, and an earlier slide lists *"Asset value appreciation"* and gives the asset value as *"∞"*. Servers do not appreciate. They wear out, and they become obsolete, and accounting says how fast.

The clearest evidence comes from the landlords themselves. Microsoft, in its 2022 fiscal year, and Alphabet, in 2023, lengthened the accounting life of their servers and network equipment from four years to six, which reduced their reported depreciation by billions. In February 2025, Amazon went the other way for part of its fleet, shortening it from six years to five from the start of that year, and citing *"the increased pace of technology development, particularly in the area of artificial intelligence and machine learning."*

The three largest owners of servers in the world disagree about how long a server lasts. A TCO for a sovereign platform should not assume they last forever. Plan a hardware refresh inside, or just after, a five-year model — and expect AI hardware to age faster than the rest.

## What the platform can put on the worksheet

*Build log · 17 September 2026*

The platform in this book cannot supply Meridian's numbers. It can supply something the slide lacks: inputs that were measured. Four of them matter for a TCO.

**Speed.** A two-machine Kubernetes cluster is built from its declaration to both machines ready in a median of 33.7 seconds, and torn down in 18.9 (Chapter 7). For steady workloads, "we rent because renting is faster" is no longer a line that has to be paid for.

**Reservation versus use.** Waste is not only a cloud problem. On the management cluster that afternoon:

- Its 59 running pods had **reserved 22.42 GiB** of memory. Of that, 14.57 GiB was held by the two virtual machines of the target cluster.
- The whole management cluster was **actually using 7.45 GiB** — about a third of what it had reserved.
- The target cluster's control-plane machine had been given 4 cores and 8 GiB. It was using **59 millicores — 1% of its processor allowance — and 1,114 MiB of memory.**
- The node had reserved 4.59 processor cores. At the moment it was sampled, it was using well under half of one.

On owned hardware, capacity is set by what is **reserved**, not what is used. On this host, a second target cluster would not fit — its machines could not reserve the memory — even though two-thirds of the memory already reserved sat idle. That is the deck's *"overprovisioning"*, on hardware you own. It is the owner's margin to reclaim or waste, and right-sizing reservations is where it lives.

**The energy cost of AI.** The model most of the platform's agents use, `qwen2.5:7b`, was measured on the laptop's GPU. With the model loaded and idle, the GPU drew **6.4 W**. While generating text it drew **38–42 W**, at **34–37 tokens per second**. That comes to **1.19 joules per generated token — 0.33 kWh per million tokens**, for the GPU alone.

Multiply that by any electricity price between 10 and 50 cents a kilowatt-hour, and the power for a million generated tokens costs roughly **3 to 17 cents**. The lesson is not that local AI is nearly free. It is that for local AI, the electricity is a rounding error. The cost is the hardware — which, on this GPU, holds one model at a time (Chapter 9) — and the people who run and check it.

**The people.** The repository behind this book holds 81 commits, from 11 February to 9 September 2026, from **a single committer, Mahipal**. **63 of those 81 commits** carry an AI coding assistant as co-author. The platform's operating notes run to 612 lines, including 23 entries in a list of pitfalls — most of them a failure that looked like success.

Read that carefully, because it is the easiest number in this book to misuse. It describes a lab: no on-call rota, no service-level agreement, no production users, no auditors. It says nothing about the cost of *operating* a sovereign platform at Meridian's scale. What it does suggest is narrower, and still worth a line in the model: in 2026, the effort to *build* such a platform is not the effort a 2021 estimate would assume. And the cost that never appears on a TCO slide is the one those 23 pitfalls describe: the continuous work of knowing what is true.

One more fact belongs on the worksheet. The platform's cost-analysis agent — the persona written in April to find idle virtual machines and propose stopping them — cannot currently be installed; it was written for a resource type the agent platform no longer ships (Chapter 16). The tool meant to measure the owner's waste is itself waiting to be fixed.

## The worksheet

Put the slide's shape and the platform's measurements together, and the chapter's real deliverable is a worksheet: the lines a sovereign-cloud TCO must contain, and what this book can say about each. The amounts come from your own invoice.

| Line | Renting | Owning | What this book measured |
|---|---|---|---|
| Capacity | On the invoice | Hardware, amortized over its refresh cycle (4–6 years, per the public record) | 22.42 GiB reserved against 7.45 GiB used |
| Speed to capacity | Minutes | The factory's build time | 33.7 s to a two-machine cluster; 18.9 s to remove one |
| Software | Managed-service fees and licences | Open source, plus optional support | The whole stack is open source (Chapters 3–4) |
| Leaving | Switching fees (banned in the EU from 2027) and rebuilding proprietary services | Migration project, and paying for both during it | No migration tooling in the repository (Chapter 4) |
| Power and facilities | Inside the rent | Power, cooling, space | 0.33 kWh per million generated tokens, GPU only |
| AI inference | Per token, hosted | Hardware sized for the models | 34–37 tokens/s; one model at a time on a 6 GB GPU |
| People | The supplier's staff | Platform team, on-call, training | A lab: one committer (Mahipal), 63 of 81 commits AI-co-authored |
| Upgrades | A button and a maintenance window | Yours | A week, for one major upgrade (Chapter 17) |
| Knowing what's true | The supplier's status page | Your own checks | Gauges found wrong in Chapters 4, 5, 11 and 12 |

## The journey

*Briefing · February 2026*

The deck's last recommendations slide is a seven-step *"Sovereign Cloud Journey"*. It holds up better than its TCO slide, because each step is an action, not a number. Here are the steps, with where each one shows up in this book:

1. **Assess current state** — *"Audit cloud spend, identify lock-in points, catalog proprietary service dependencies."* Meridian's workload spreadsheet, and its dependency table (Chapters 1 and 2).
2. **Evaluate workload portability** — which workloads move easily, and which need rework. The steady ones first (Chapter 1).
3. **Start with non-critical workloads** — *"Build expertise on development, testing, or low-risk production systems."* The pilot, and Parts II to IV.
4. **Invest in CAPI & Kubernetes** — the factory (Chapter 4 and Part II).
5. **Consider hybrid approaches** — *"Maintain some managed services during transition to reduce risk."* Meridian is still renting, on purpose.
6. **Build platform engineering** — the blank fourth column of Vikram's table in Chapter 2: who could fix the boiler.
7. **Plan a 3–5 year timeline** — *"Full transformation requires patience but delivers lasting value."*

The deck lists four *"Key Success Factors"*: executive sponsorship, adequate budget, skills development and hiring, and incremental delivery. This book would add a fifth, ahead of the others: **measurement before savings.** Nothing in steps 1 to 7 produces a saving until someone has metered the same workload both ways.

## A cloud owning culture

The campaign flyer promises *"Save $Millions"* and names the means: *"Creating a Cloud Owning Culture."* The book agrees with the second half, and has spent eighteen chapters finding out what it means.

Owning a cloud is not owning servers. It is owning the work a landlord used to do out of sight: knowing what is true about the platform, and being able to show someone else how you know. At Meridian that took the form of rules, each written after a measurement proved an assumption wrong:

- Don't say *ready*; say *working*, and only once something has worked (Chapter 5).
- Anything we keep warm, we exercise (Chapter 9).
- Keep the before picture, and label it (Chapter 10).
- No check goes on a dashboard until someone has watched it fail on purpose (Chapter 11).
- A model gets what every service gets: an identity, a lock, and a meter (Chapter 12).
- An agent may advise; it may not act — until it has earned it, in writing (Chapters 15 and 16).

None of those rules appears on a TCO slide. All of them are part of the cost of owning, and all of them are where the margin is actually kept.

## What to ask your vendors — including the one you become

When a sovereign-cloud programme starts, the organization becomes a supplier to itself. The same questions apply to both.

1. **Price.** How much notice do we get before a price change, and is there a cap?
2. **Leaving.** What does it cost to leave, in fees and in rebuilding, and in what format do we get our data back?
3. **Control.** Which settings we need can we *not* change, and who decides when that list changes?
4. **Jurisdiction.** Where are our data, our logs and our AI prompts processed — and under whose law?
5. **Metering.** Can we see tokens used, by model and by team, every month?
6. **Truth.** When your status page says *healthy*, what did you check, and how would we check it ourselves?

A platform team that cannot answer those six for its own platform has rebuilt the landlord, and moved it indoors.

* * *

*Meridian · the same Friday, two hours later*

The spreadsheet had nine rows, the same nine as the worksheet, and three columns: *renting today*, *owning, estimated*, and *owning, measured*. The first column was nearly full; the finance team had the invoices. The second was full of ranges. The third was empty except for three cells Vikram had sent over: a build time, a reservation figure, and an energy number.

"So what goes in the board pack?" the CFO said. "They asked for a saving."

"They'll get one," Anita said. "Not from a consultant. From us." She pointed at the first row of the workload spreadsheet from January — the steadiest system Meridian had. "We run that on the pilot platform for a quarter, in parallel. We meter both sides — the invoice on one, and hardware, power and hours on the other. People's time goes in the model, not in a footnote. At the end of the quarter we have one number we can defend, for one workload."

"One workload isn't four point three million."

"No. It's the first line of it that's true." She closed the consultant's slide. "The board has been shown a lot of green this year. I'd like the first number we give them about the money to be one we measured."

The CFO typed the board-pack line himself. *Sovereign cloud: no savings claimed. One workload metered in parallel, Q4; first measured result in January.*

He read it back. "It's a very boring sentence."

"Good," Anita said. "Boring sentences are the ones that turn out to be true."

## The ledger

- **The deck's model (briefing):** $12.5M rented against $8.2M owned over five years; a $4.3M (34.4%) saving that is exactly the sum of four savings lines, with no line for anything owning adds. About 70% of the saving ($3.0M) is in two lines no invoice records. The 5–7 year payback agrees with the five-year saving only at the expensive end of the deck's own $2–5M investment range.
- **Depreciation (public record):** Microsoft (FY2022) and Alphabet (2023) moved servers from four- to six-year lives; Amazon moved part of its fleet from six to five years from January 2025, citing AI.
- **Owned waste (build log, 17 September 2026):** 22.42 GiB reserved against 7.45 GiB used on the management cluster; a control-plane VM using 1% of its CPU and 14% of its memory.
- **AI energy (build log):** `qwen2.5:7b` on an RTX 4050 laptop GPU at 6.4 W idle and 38–42 W generating; 34–37 tokens/s; 1.19 J per token; 0.33 kWh per million generated tokens, GPU only.
- **Effort (build log):** 81 commits from one committer, Mahipal, over seven months, 63 of them co-authored with an AI coding assistant — a lab, not an operation.
- **Not claimed:** any saving for Meridian.

## Ask your team

1. **For our biggest workload, what would it cost to meter it both ways, in parallel, for one quarter?**
2. **In any savings model we have been shown, which lines appear on an invoice — and which lines for new costs are missing?**
3. **What do we reserve against what we actually use — in the cloud, and on the hardware we already own?**

## Open the repo

- `kubectl --context kind-cluster2 describe node cluster2-control-plane` — reserved against allocatable, under *Allocated resources*.
- `docker stats --no-stream` — what the clusters actually use.
- `kubectl --kubeconfig target-cluster-kubeconfig top nodes` — what a target-cluster machine uses of what it was given.
- `nvidia-smi --query-gpu=power.draw --format=csv -lms 200`, alongside `ollama`'s `eval_count` and `eval_duration` — energy per token.
- `git log --format='%B' | grep -c 'Co-Authored-By'` and `git shortlog -sn` — how the platform was built.
- `06-sympozium/cost-analyzer.yaml` — the FinOps agent, and why it does not install (Chapter 16).
- `~/marketing/Reclaiming Margins with Sovereign Cloud.pptx`, slides 16, 18 and 19; `~/marketing/SovereignCloud_Flyer_v2.pdf`.

## Draft notes

*For the author — remove before publication.*

- **This chapter has no Meridian figures.** The author was asked for real cost inputs; none were available, so the chapter uses the deck's model, clearly labelled, and proposes the parallel-metering test instead. If real figures become available, the worksheet table is where they go.
- **Deck arithmetic** was computed in a scratch script: 4.3/12.5 = 34.4%; (1.8+1.2)/4.3 = 69.8%; the investment and payback scenarios are as tabled. The deck does not say whether $8.2M includes the initial investment. The chapter tests both readings rather than choosing one.
- **Depreciation sources** are secondary (search results summarizing filings): Microsoft Q4 FY2022; Alphabet January 2023; Amazon's 7 February 2025 disclosure, effective 1 January 2025, quoting "increased pace of technology development, particularly in the area of artificial intelligence and machine learning." Cite the 10-K/10-Q text directly before publication, and confirm the "billions" wording (the coverage cites about $3.7B for Microsoft's FY2023).
- **Reservation figures.** Memory requests were summed over Running/Pending pods from `kubectl get pods -A -o json`. That gives 22.42 GiB; `describe node` reported 24,192,159,232 bytes (≈22.5 GiB). "Used" is `docker stats` for the `cluster2-control-plane` container (7.453 GiB), a single sample. CPU use is the same sample (41.46% of one core). The target VM figures are `kubectl top nodes` inside the target cluster; the worker reported `<unknown>`, consistent with Chapter 5's tainted worker.
- **"A second target cluster would not fit"** is arithmetic on memory requests (about 7.5 GiB unreserved, against 14.57 GiB for a target cluster's VMs). It was not tested by scheduling one. The platform also enforces one target cluster at a time by design.
- **Energy.** Scratchpad `ch18-energy.sh` / `.log`:
  - Five runs of 400 generated tokens, temperature 0, with the model already loaded (0.13–0.17 s load time); `nvidia-smi` sampled every 200 ms.
  - The first run's mean was lower (38.3 W), likely ramp-up. Throughput drifted from 37.1 to 33.9 tokens/s across runs, possibly thermal.
  - GPU-board power only: not CPU, memory, the rest of the laptop, or cooling. The laptop was on AC power.
  - Chapter 15's "11.0 tokens per second" is a different metric: whole agent runs, including prompt processing and tool calls.
  - The 3–17 cents range is illustrative arithmetic at 10–50 cents per kWh, not a measured price.
- **The effort figures** are `git rev-list --count HEAD` (81), `git shortlog -sne` (1 author) and a count of commit messages containing "Co-Authored-By: Claude" (63). The last commit is 9 September. 28 working-tree changes (including this book and the September upgrade) were uncommitted at the time of writing. **Decided:** the committer is named (Mahipal) in the text above; how much further to describe the AI assistance is still open.
- **The Meridian scenes are fiction.** The board-pack sentence sets up the epilogue, where savings are still "not yet measured".
- **Character names.** Anita Rao and Vikram Iyer remain placeholders.
