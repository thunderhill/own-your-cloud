# Chapter 9 — Warmth Is Mandatory

> *Warmth is mandatory. No persona may enter the fleet without a warm-path guarantee.*
>
> — Architecture Constraint 5, `Sovereign_Cloud_Agentic_Strategy.md`

*Meridian · a Thursday in September · the CTO's office*

The prospect had asked the AI console a simple question, and for thirty seconds the answer did not come. Then the request timed out, on the big screen, in front of their head of infrastructure. Vikram asked again. The second answer arrived in four seconds and was correct.

"Why was the first one slow and the second one fast?" Anita asked afterwards.

"The first question had to wake the model up. It loads into memory on first use. After that it stays loaded, and everything is quick."

"Like the clusters," she said. "Build one from nothing, it takes half a minute. Hand over one that's already running, it's instant."

"Same idea."

"Then it has the same economics." She pulled a pad toward her. "Keeping things warm costs hardware that sits idle. Being cold costs moments like that one. I want both prices, for both things, on one page. And I want to know who is keeping them warm right now."

* * *

*Build log · June–September 2026*

## Two kinds of cold

This platform has two things that are slow to start and fast once running, and the whole of this chapter is about the difference.

The first is a **cluster**. Chapter 7 measured a cold build — from `kubectl apply` to both nodes `Ready` — at 33.7 seconds after the September upgrade, and Chapter 8 tells how it came down from fifty, and then, by 30 September, to 18.1. Every one of those seconds is intrinsic to building a cluster from nothing: controllers creating virtual machines, the machines booting, k3s starting, a worker joining. Chapter 8's lesson was that a smarter golden image cannot remove them. Only one thing can: doing the work *before anyone asks*.

The second is a **model**. An agent's first request loads its language model into memory. The strategy document wrote the cost into its fifth architecture constraint, as measured when the platform's model ran on the CPU: *"Cold-start for llama3.2 on CPU is ~28–30s; unwarmed agents time out the first real request."*

Different machinery, same trade: capacity held in reserve against time lost to a cold start.

## A standby, not a pool

The design for warm clusters is in `docs/warm-pool-strategy.md`, and it begins by rejecting the obvious answer. A classic pool keeps several pre-built machines and hands them out. This platform runs exactly one target cluster at a time, so the document asks for something smaller: a *size-1 pre-deployed standby*. Keep one cluster built and idle. "Deploy" means *claim* it. "Delete" means tear it down and build the next standby in the background, off the user's clock.

The lifecycle is a label on the cluster object, `pool.local/state`:

```
   (none) ──build in background──▶ WARM ──user clicks Deploy──▶ CLAIMED
      ▲                                                             │
      └──────────── rebuild in background ◀── user clicks Delete ◀──┘
```

One constraint makes it tractable, and it is easy to miss. A KubeVirt VM's pod address is assigned when its launcher pod starts, and the document records that a changing address was what broke the datastore in the warm-image experiment. *"A pooled VM that stays alive keeps its pod IP"* — so its datastore identity and its certificates stay valid. That is also why the document rejects the other obvious answer, snapshot and restore: a restore *"re-provisions the PVC and **reboots**, so you pay the 17s boot again and get a new IP."*

A second level is described and deliberately deferred: a pool of *paused* VMs, frozen by KubeVirt with their memory and addresses intact, resumable in under a second. It would allow more than one warm cluster, at the price of a real controller and, in the document's words, *"ongoing maintenance."*

## One hundred ninety-four milliseconds

*Build log · June 2026*

The standby was built on 27 June as a background loop inside the UI's Go backend. Every few seconds it looks for a target cluster. If none exists, it builds one through the same Cluster API path as any other deploy and labels it `WARM` once it is ready. When a user clicks Deploy and a warm standby exists, the handler relabels it `CLAIMED`, refreshes the credentials the agents use to reach it, and streams a short progress report.

Measured end to end, with a warm standby in place: **194 to 195 milliseconds** from the click to done, with both nodes already `Ready`. The background rebuild after a delete took about 60 seconds, and the cycle — claim, delete, rebuild, claim — repeated cleanly. The acceptance gate had been under forty seconds; the claim beat it by a factor of about two hundred.

One bug is worth recording, because it is Chapter 7's lesson in miniature. The first version reset the progress log from a background thread while the user's browser was already subscribing to it. The browser received the *previous* build's log and an immediate "done": a fast, confident, false success. Only an end-to-end test caught it.

Then came the price. The standby uses the full profile: four cores and 8 GiB of memory for the control plane, four cores and 6 GiB for the worker. That is **eight cores and fourteen gigabytes held idle, all day, on purpose**, on a host that had about 21 GiB free. The document says it plainly: *"Idle resource cost. One cluster always running."*

Within a week, that cost produced a decision. The pool had started out enabled, which meant a standby cluster was built every time the UI started and rebuilt after every cleanup — whether or not anyone intended to deploy. That surprised its own user. On 1 July it became opt-in, and the start script now says so: *"Opt-in: export POOL_ENABLED=true before running this script to have the backend auto-build/rebuild a standby cluster in the background."* Warmth that nobody asked for is not a feature. It is a machine working when no one is watching.

## The standby today

*Build log · 17 September 2026*

Checked against the running platform on 17 September, the fastest path in the platform turns out to be the least exercised one.

The UI backend reports no standby: `{"state":"none"}`. The pool is opt-in, and the script that starts the UI leaves it off by default. It also lives only as long as that backend process runs, so the command-line deploy path has never benefited from it.

Its standby manifest still points at the image tagged `ubuntu-noble-k3s:latest`, and that image was built on **3 March**. It was not rebuilt during the September upgrade in Chapter 19. Turning the pool on today would build its standby from a six-month-old image, under a manifest that now declares a much newer k3s. Nobody has tried it.

Its readiness check counts *two Ready nodes*, the same pattern that fooled the stopwatch in Chapter 7. A standby built from the warm image would be declared ready while its worker was still booting, because that image carries the ghost node. Whether the March image carries anything similar has not been checked.

And the 194-millisecond claim has not been measured since June.

None of this means the design is wrong. It means a warm path is only as good as the last time someone used it. The image aged, the platform moved underneath it, and a number from June stayed on the page.

## Warming the model

*Build log · April–September 2026*

The model's warmth has a history of its own, told in three tools.

The first was a script, `06-sympozium/ollama-warm.sh`: send a one-token request and ask the model server to keep the model loaded for twenty-four hours. The second was the Phase 0 deliverable from Chapter 16: a heartbeat schedule that pings `cluster2-agent` every four minutes. Its comment explains why: *"Cold-start on CPU is ~28-30s; this schedule removes that latency from the first real KubeUI chat request."* Chapter 14 found that schedule had fired twice and stopped. The third tool is the one actually doing the job: the host's Ollama service runs with `OLLAMA_KEEP_ALIVE=-1`, which keeps a loaded model loaded indefinitely. That setting lives in the host's service configuration, not in the repository.

## The GPU changed the price

*Build log · 17 September 2026*

The constraint's thirty seconds was a CPU number. The host now has an NVIDIA RTX 4050 GPU with 6 GB of memory, and Ollama places each of the fleet's models entirely on it. So the cold start was measured again on 17 September, using the load time Ollama reports for each request — first with a model unloaded, then with it loaded:

| Model | Cold load | Warm load |
|---|---:|---:|
| `qwen2.5:7b` | 2.57 s, and 2.38 s on a second cold start | 0.14 s, 0.17 s |
| `llama3.2` | 2.33 s | 0.17 s |

**About two and a half seconds cold, under two-tenths of a second warm.** The difference is still roughly fifteen-fold, and still visible in an interactive chat. But a two-and-a-half-second load no longer times out a request by itself. The hardware changed under the rule, and the rule's number went stale.

The same measurement showed something the rule never anticipated. **The GPU holds one of these models at a time.** Every cold load evicted the other model. `OLLAMA_KEEP_ALIVE=-1` does not mean *forever*. It means *until something else needs the room*.

That matters because the fleet uses both. `cluster2-agent` and `mesh-sre-agent` run on `qwen2.5:7b`; `target-cluster-agent` runs on `llama3.2`. And it had already happened that morning, unnoticed. At 00:55 UTC, `qwen2.5:7b` was the loaded model. At 01:06, the two-agent pipeline lab from Chapter 16 ran its reviewer on `llama3.2`. By the time anyone checked, `llama3.2` was loaded and `qwen2.5:7b` — the model two of the three agents depend on — was not. A test run had quietly cooled the production agents. (It was restored for this chapter.)

Warmth on shared hardware is not a property of a model. It is a queue.

## Two inventories, both one deep

Put the two kinds of warmth side by side and they turn out to have the same shape:

| | A cluster | A model |
|---|---|---|
| Cold | 18.1 s, both nodes (30 Sept; 33.7 s on 17 Sept) | 2.3–2.6 s on the GPU (28–30 s on CPU) |
| Warm | 467 ms median (18 Sept, 3 runs; was 194 ms in June) | 0.14–0.17 s |
| What warmth holds | 8 cores and 14 GiB of memory, idle | most of a 6 GB GPU |
| How deep | one standby | one model at a time |
| What keeps it warm today | a background loop, on by default since 30 Sept (since 13 Oct, nothing by default: see below) | a host setting outside the repository |

For a CxO, warmth is inventory. It trades capacity you pay for up front against time you lose later, and it has the same three failure modes as any inventory.

**It can be the wrong size.** One standby covers the first request in a minute, not the second. One model slot covers one model, not a fleet that uses two.

**It can spoil.** A standby built from a March image, and a heartbeat that stopped in September, look like warmth on paper and are not.

**It can be taken by someone else.** A test run that loads a different model empties the shelf the production agents were counting on.

* * *

*Meridian · the following Monday*

Vikram's page had two columns, one for clusters and one for models, and a price at the bottom of each.

Anita read it twice. "The model costs two and a half seconds cold now, not thirty."

"On this GPU. And only if it's the model that was already loaded. The GPU holds one at a time, and our agents use two."

"Then we use one," she said. "The one that uses its tools properly. One model for the whole fleet, until the hardware says otherwise." She moved to the other column. "And the cluster standby?"

"Built from a March image, and switched off."

"Then it isn't warm. It's a cold path with a design document." She wrote across the bottom of the page. "Rebuild the image. Turn it on. And every week, someone claims it, deletes it, and times the rebuild — naming both nodes."

"Every week?"

"Anything we keep warm, we exercise," Anita said. "Otherwise we are paying for idle hardware to hold a promise nobody has checked."

## Turned on, and timed

*Build log · 18 September 2026*

The mandate was carried out the next day, and it found the same ghost that Chapter 7 found in the timing scripts, waiting in the same shape.

`targetNodesReady`, the function both the Deploy button's build path and the pool controller use to decide "are both nodes up," counted Ready nodes without checking their names. A standby built from the `:warm` image would have been declared ready on the control plane plus the leftover bake-VM ghost node, before the real worker ever joined — exactly the bug that made Chapter 7's stopwatch stop early, now confirmed live in `ui/backend/handlers/pool.go`, not just in the standalone scripts. Fixed the same way Chapter 7 recommends: count only nodes named `<cluster>-cp-*` or `<cluster>-workers-*`.

With that fixed, `POOL_STANDBY_MANIFEST` moved from `target-cluster-parallel.yaml` (the March image, k3s v1.31.4) to the warm manifest — and the pool's build function gained the one step it was missing to use it safely: seeding the fixed CA and token secrets before applying, the same order the Deploy button's build path already used, so KThrees adopts the baked material instead of falling back to a slower path.

Then the cycle Anita asked for — claim, delete, rebuild, claim — ran three times, timed from the `POST /api/v1/cluster/deploy` request to the stream's closing `done` event:

| Run | Time |
|---|---:|
| 1 | 1.059 s |
| 2 | 0.467 s |
| 3 | 0.465 s |

**Median: 467 milliseconds.** Not 194. The first run is reported rather than discarded — an unexplained outlier, kept on the same principle this book applies to every other number in it. Runs 2 and 3 agree closely, and the time is not free: of the roughly 465 milliseconds, about 265 is `clusterctl get kubeconfig` alone; relabeling the cluster and syncing the in-cluster kubeconfig Secret split most of the rest.

Two and a half times the June figure, and still far faster than building from nothing: the claim now beats the 33.7-second cold build by a factor of about 72 — not the factor of two hundred the June number implied, but still the same conclusion Anita drew from the wrong number: handing over something already running beats building it, by nearly two orders of magnitude. The design held. The number on the page had simply gone stale, in exactly the way this chapter's own middle section warned that warmth does.

It went stale again within two weeks, from the other side. By 30 September the cold build was 18.1 seconds (Chapter 8), and the same 467-millisecond claim beats it by a factor of about 39, not 72. The standby still costs eight cores and 14 GiB, idle, all day. Warmth pays less than it did a fortnight earlier, for the same price. That does not make it a bad trade, but it is a different trade from the one priced on 18 September, and the ratio deserves a date like any other number.

## Since then: asleep until asked

*Build log · 13–15 October 2026*

Carried one step further, that shrinking ratio raises a question this chapter had never asked. If a cluster can be built from nothing in eighteen seconds, why keep one at all while nobody is using it?

On 13 October the platform's default changed to an answer. In **on-demand mode** no target cluster exists while nobody is using it. The first access builds one. After an hour without use, the platform deletes it again. The standby is still there for anyone who wants it, by exporting `POOL_MODE=standby`, but it is no longer what `run-ui.sh` starts.

```
   (none) ──first access──▶ building ──API answers──▶ IN USE
      ▲                                                  │
      └──── delete ◀── one hour with no access ◀─────────┘
```

The hard part was not the build or the delete. Both already existed. The hard part was knowing what counts as *use*.

The cluster's API lives at `172.18.255.215`, and that address is never quiet. The cluster's own nodes talk to it constantly, and so do the Cluster API controllers that manage it. Traffic there says nothing about whether a person or an agent wants the cluster. So users and agents are now handed a kubeconfig that points somewhere else: a **front door** at `172.18.255.223`, which the console's backend serves. Everything that arrives at the front door is someone's work, by construction.

What it does depends on whether the cluster is up.

- **The cluster is up.** The front door copies bytes in both directions to the real API server, and never sees inside. Encryption and client-certificate authentication run end to end, as before. Every byte that the client sends resets the idle clock.
- **The cluster is not there.** The front door answers the encrypted connection itself, with a certificate minted from the warm path's fixed server CA. It requires a client certificate signed by the cluster's client CA, so only someone already holding valid credentials can start a build. Then it starts the build and holds the request until the new API server is ready. Finally it answers `503 Service Unavailable` with `Retry-After: 1`. `kubectl`'s client library retries that by itself, reconnects, and this time is passed straight through to the new cluster.

The user types an ordinary `kubectl get nodes` and waits. The design comment explains why the front door does not simply hold the raw connection open until the cluster arrives: *"client-go gives up on a TLS handshake after 10s and a cold build takes longer."*

Two other things count as use: clicking Deploy in the console, and opening a chat with `target-cluster-agent`. The chat starts the build when the conversation opens, not when the agent first calls a tool, so the model's thinking time overlaps the build.

### The numbers

Measured from no cluster at all, through the front door, with plain `kubectl`:

| Boundary | Time |
|---|---:|
| First `kubectl get nodes` answered | **15.3 / 15.3 / 15.7 s** |
| Both nodes `Ready` | about 20.5 s |
| Idle delete, once the hour has passed | about 14 s |

**Fifteen seconds from nothing to a cluster that answers.** That is the number a user of this platform now feels on the first command after a quiet hour, and it is the new headline. It needs the same care as every other headline in this book.

**It does not beat the 18.1 seconds.** It stops the clock at a different line. The 18.1 is *both nodes Ready*. The 15.3 is *the API answered*, which needs only the control plane, and Chapter 8's runs had the control plane ready at 14.3 seconds. The same wake reaches both nodes `Ready` at about 20.5 seconds, roughly two seconds *slower* than the 18.1-second build. The front door's hold, the client's retry and the console's once-a-second polling are all candidates. Nobody has split those two seconds, and the book does not claim a breakdown.

**It is three runs.** The book's own rule asks for five, against a spread it can see. The three agree to within 0.4 seconds, which is encouraging, not conclusive.

**The 14 seconds is not Chapter 17's 40.** The idle-delete figure is the platform notes' *"~14s"*, with no run count and no stated boundary. Chapter 17's drill stops its clock when every object and machine is gone, by boundaries written down in advance, and measured 40.0 seconds on 8 October. The two have not been run side by side, and the book does not reconcile them. What is recorded is a cost that falls on users: a request that arrives during a teardown waits for the teardown to finish. The demo script says that turns the fifteen-second wake into about thirty.

The same change found one stale instrument, which by now should surprise nobody. The console's deploy log had polled for progress every 10 to 15 seconds, a setting chosen when a build took minutes. Against a build that is ready in under twenty seconds, the console had been reporting builds as finished *"tens of seconds late"*, in the words of the commit. Its polls are now one second. The stopwatch this time was the dashboard.

It also fixed a quieter bug. The backend kept its copy of the cluster's credentials in `/tmp`, which does not survive a reboot. Without that file, a healthy cluster read as *not ready*, and the pool controller would tear it down to rebuild it.

### The price, again

Put the two modes side by side and the trade this chapter has priced all along is visible in one table:

| | Standby (`POOL_MODE=standby`) | On demand (default since 13 October) |
|---|---|---|
| First access | 467 ms claim (18 September) | 15.3 s to first answer; about 20.5 s to both nodes |
| Held while nobody is using it | 8 cores and 14 GiB, all day | nothing, once the idle hour has passed |
| Held after the last use | a fresh standby, rebuilt in the background | the cluster, for up to an hour (`POOL_IDLE_TTL`, default `1h`) |
| Who keeps it honest | the weekly claim-and-rebuild drill | every first command of the day |

The last row matters most. This chapter's complaint about warmth was that a warm path decays when nobody exercises it: a March image, a June number, a heartbeat that stopped. A cold path that runs every time someone starts work cannot decay quietly. If the wake breaks, the first person to type `kubectl` that morning finds out.

### What it depends on

None of this is free, and the conditions belong next to the fifteen seconds rather than in a footnote.

- **It is built on the trade Chapter 17 warned about.** The kubeconfig survives the delete, and the next cluster accepts it, because every cluster is built with the same fixed certificate authorities. That is the property that let a credential from five rebuilds earlier open a brand-new cluster with full rights. Chapter 17 recorded it as a cost. On-demand mode depends on it. Per-cluster identity would break wake-with-the-same-file, and would cost the hundred-second build on top.
- **The front door holds the server CA's private key.** To answer while the cluster is absent, the backend mints a server certificate from `warm-ca/server-ca.key`. The process that serves the console can now present itself as the cluster's API server. On a lab with committed, demo-only CAs, that changes little. Anywhere else it would be a finding.
- **It needs the backend running.** Stop `run-ui.sh` and the front door stops answering, so nothing wakes. The idle reaper stops too, so nothing is deleted either: a cluster left running when the backend stops stays running.
- **The idle clock lives in memory.** It restarts with the backend, so a restart can postpone a delete but never bring one forward. Only clusters the backend itself labelled are reaped. One built by hand is left alone.
- **The direct address bypasses all of it.** `kubectl` pointed straight at `.215` neither wakes the cluster nor keeps it alive. `make verify` rewrites the repository's kubeconfig to `.215`, so the standard verification step quietly opts its user out of the mode.
- **Clients other than `kubectl` see the 503.** A client that does not retry on `Retry-After` gets one refusal on a cold wake, and has to try again itself.
- **One wake path was not demonstrated.** When the demo script was written (15 October), `target-cluster-agent`'s serving pod was crash-looping, so the chat path starts a build but could not be shown end to end. The demo script says to skip it.

Constraint 5 is called *"Warmth is mandatory."* For clusters, as of October, the platform no longer keeps one warm by default. That does not break the rule. It is what the rule's trade looks like once a cold build costs fifteen seconds instead of fifty. For models, nothing changed: a model still has to be loaded before the agent can answer, and the GPU still holds one at a time.

## The ledger

- **Built (June):** a one-deep cluster standby, claimed in 194–195 ms instead of built from scratch, rebuilt in about 60 seconds in the background.
- **Cost of that warmth:** one full cluster idle — eight cores and 14 GiB of memory.
- **Today (17 September):** no standby running; the pool is opt-in and off by default; its manifest points at an image built on 3 March; the claim time has not been re-measured since June.
- **Fixed and re-measured (18 September):** the pool's node-readiness check now counts by name, not by count (the same ghost-node bug Chapter 7 found, confirmed live in `pool.go`); its standby manifest switched to the warm image, with CA/token seeding added to the build path. Three claim-delete-rebuild-claim cycles: 1.059 s, 0.467 s, 0.465 s — **median 467 ms**, not 194. Still about 72x faster than a cold build. The pool remains opt-in — this fixes what happens when it's on, not the default.
- **Since (30 September):** the pool is on by default (`run-ui.sh` now sets `POOL_ENABLED=true`), and the cold build it competes with is 18.1 s, so a claim is about 39× faster rather than 72× for the same idle cost. Not re-measured: the claim time itself, and whether the pool's rebuild-after-delete waits on the previous VMs' memory, as Chapter 8's stopwatch once did.
- **Changed again (13–15 October):** the default is now on-demand mode, with no cluster while nobody uses it. A front door at `172.18.255.223` builds one on first access and the backend deletes it after an hour unused. **Cold wake to first `kubectl` answer: 15.3 / 15.3 / 15.7 s** (N=3); both nodes `Ready` at about 20.5 s, about two seconds slower than the 18.1-second build; idle delete about 14 s (one unrecorded measurement), not reconciled with Chapter 17's 40 s. Idle cost: nothing, after up to an hour. Depends on the fixed CAs Chapter 17 priced, on the backend running, and on clients that retry a 503.
- **Model warmth, measured on the GPU (17 September):** 2.3–2.6 s cold, 0.14–0.17 s warm — against the 28–30 s CPU figure in the rule.
- **Found:** the GPU holds one model at a time, and a lab run evicted the model two of the three agents use.
- **Held by:** a host setting outside the repository, not the heartbeat the rule names, which stopped after two runs.

## Ask your team

1. **What do we keep warm, what does that capacity cost us, and what would being cold cost instead?**
2. **When did we last actually use our fast path — not measure it once, but use it?**
3. **What shared resource do our warm things compete for, and whose work gets evicted first?**

## Open the repo

- `docs/warm-pool-strategy.md` — the three design levels, and the stable-IP constraint.
- `ui/backend/handlers/pool.go` — the standby controller; `POOL_ENABLED`, `POOL_STANDBY_MANIFEST`, and `GET /api/v1/cluster/pool-status`.
- `docs/superpowers/specs/2026-06-26-warm-pool-standby-design.md` — the acceptance gate.
- `06-sympozium/ollama-warm.sh` and `06-sympozium/schedules/ollama-warm.yaml` — the first two ways the model was kept warm.
- `curl -s localhost:11434/api/ps` on the host — which model is warm right now; the `load_duration` field of any `/api/generate` response shows whether a request paid for a cold start.
- `POOL_ENABLED=true POOL_STANDBY_MANIFEST=03-target-cluster/target-cluster-warm.yaml` — the corrected pool config (18 September); `git log --oneline -- ui/backend/handlers/pool.go run-ui.sh` for the fix commits.
- `ui/backend/handlers/activator.go` — the front door; its header comment explains the splice, the held request and the 503. `ui/backend/handlers/activity.go` — what counts as use, and the idle decision. `ui/k8s/target-frontdoor.yaml` — the `.223` Service pointing at the host.
- `POOL_IDLE_TTL=3m ./run-ui.sh` — on-demand mode with a three-minute idle limit; `docs/demo/ondemand-speaker-script.md` walks through a sleep, a wake and an idle delete, and lists what breaks the demo. `POOL_MODE=standby` restores the always-built standby. `git show e08cc9c` for the commit.
