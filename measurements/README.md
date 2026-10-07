# Measurements

Raw data behind the book's measured claims, kept so that a reader can check the arithmetic rather than trust it.

## `ch19-parallel-metering-20260918.tsv`

The parallel-metering experiment in Chapter 19. Produced by `ch19-meter.sh`.

**Date:** 18 September 2026, 09:14:22–09:24:17 UTC.
**Workload:** one `nginx:alpine` deployment on the target cluster, served continuously through a ClusterIP Service, probed once per sample.
**Host:** the single workstation described in the prologue — AMD Ryzen AI 9 HX 370, 24 threads, 29.96 GiB, NVIDIA RTX 4050 GPU, on AC power.
**Sampling:** 30 samples at 20-second intervals.

| Column | Meaning |
|---|---|
| `ts` | sample time, UTC |
| `docker_cpu_pct` | `docker stats` CPU for `cluster2-control-plane` — the container that hosts the entire platform. 100% = one of 24 threads |
| `docker_mem` | the same container's memory, against host total |
| `gpu_w` | `nvidia-smi` power draw. The GPU is idle throughout; this workload does not use it |
| `cp_cpu_m` | `kubectl top` — the target cluster's control-plane node, millicores |
| `cp_mem_mi` | the same node's memory, MiB |
| `http_code` | `200` if the nginx Service answered this sample, `ERR` otherwise |

**Result:** 30 of 30 samples returned `200`. Medians: 0.549 cores (2.29% of host CPU), 8.71 GiB (29.1% of host memory) for the whole platform; 67 millicores and 1,142 MiB for the target control-plane node; GPU 5.22 W idle.

**Separately measured, not in the file** (`kubectl get pods -o jsonpath` on cluster2, same date): the two virt-launcher pods reserve `400m` CPU and `8484Mi` + `6436Mi` = 14,920 MiB. Against the node's 30,680 MiB that is **48.6% of host memory reserved** and 3.3% of host CPU. Memory is the binding constraint, and the manifest's `cores: 4` per VM is a guest topology setting, not a host CPU reservation.

### What could not be measured

- **CPU package power.** `/sys/class/powercap/intel-rapl:0/energy_uj` exists but is not readable without root on this kernel. So whole-host power is an *assumption* in Chapter 19, not a measurement, and is given as a range.
- **Whole-system power via the battery.** The host was on AC; `/sys/class/power_supply/BAT*/power_now` reads `0`.

### Assumptions used in Chapter 19

None of these is a measurement. Each is stated so a reader can substitute their own.

| Input | Value used | Basis |
|---|---|---|
| Host capital cost | $1,500–$3,000 | assumption; a workstation of this class. Substitute your own |
| Amortization | 4 years (35,040 h) | the conservative end of the public record in Chapter 19: Microsoft and Alphabet moved servers 4→6 years, Amazon 6→5 |
| Host power under this load | 25–65 W | assumption; RAPL unreadable (above) |
| Electricity | $0.10–$0.50 / kWh | the same illustrative range Chapter 19 uses for the energy-per-token figure |
| Engineer day rate | $400–$1,200 / day | assumption |
| Build effort | 18 days | **measured proxy**: distinct calendar days carrying a commit, `git log --format=%ad --date=short \| sort -u \| wc -l`, 11 Feb – 18 Sept 2026. A lower bound: work happens on days without commits, and a commit day is not a full day |

### Rented-side prices

List prices, no committed-use discount, accessed **18 September 2026**.

| Item | Price | Source |
|---|---|---|
| DigitalOcean CPU-Optimized Droplet, 4 vCPU / 8 GB | $0.125 / hour ($84 / month) | https://www.digitalocean.com/pricing/droplets |
| DigitalOcean Kubernetes (DOKS) standard control plane | free | https://www.digitalocean.com/pricing/kubernetes |
| DOKS high-availability control plane | $40 / month | https://www.digitalocean.com/pricing/kubernetes |
| Amazon EKS control plane, standard support | $0.10 / cluster-hour | https://aws.amazon.com/eks/pricing/ |

EC2 instance prices are not quoted: the AWS on-demand pricing tables are rendered by script and could not be read directly, so no EC2 figure is asserted. The EKS line is quoted only to show that a managed control plane is not always free.


---

## Chapter 17 — the recovery drill (boundaries pre-registered)

**This section was written and committed BEFORE the first measured run.**

The drill times the full "replace instead of repair" cycle: destroy → infrastructure gone → seed → rebuild → workload → first HTTP 200. The book has never timed this. It also re-measures teardown, previously published from a single run.

The estimate straddles one minute. Moving a boundary after seeing the data — starting the clock at the rebuild instead of the destroy, or stopping at "pod Ready" instead of "served a request" — would land a prettier number and would be exactly the failure this book exists to catch. So the marks are fixed here, in advance:

| Mark | Established by |
|---|---|
| **T0** | the destroy command is issued |
| **T1** | that command returns |
| **T2** | no `target-cluster` API object remains **and** no `qemu-kvm -name guest=default_target-cluster*` process remains, polled at 0.25 s |
| **T3** | `scripts/seed-cluster-secrets.sh` returns and all four of `target-cluster-{ca,cca,etcd,token}` are confirmed present |
| **T4** | immediately before `kubectl apply -f 03-target-cluster/target-cluster-warm.yaml` |
| **T5** | a node whose name contains `-cp-` first reports `Ready=True` |
| **T6** | a node whose name contains `-workers-` first reports `Ready=True` |
| **T7** | immediately before the workload is applied, with the negative control already having failed |
| **T9** | the first request through the Service to return HTTP 200, judged by exit code, never piped |

**Published figures:** headline **MTTR = T9 − T0**; plus T1−T0, T2−T0 (teardown, now N>1), T6−T4 (comparable to the 33.7 s build), T5−T4, T9−T7.

### Why not the existing scripts

`scripts/time-to-ready-by-name.sh` is correct about the ghost node and its by-name matching is copied here. It cannot serve as the engine: it discards the delete, starts its build clock while VMs may still be terminating, has no workload phase, and captures host load once per invocation rather than per run. `time-to-ready.sh` and `phase-timings.sh` wait by node *count* and are subject to the ghost bug. `make target-cluster` would drag `ensure-warm-image` — and a possible 5–8 minute bake — inside the clock.

### Workload choice

`rancher/mirrored-library-busybox:1.37.0` with `imagePullPolicy: IfNotPresent`, because it is **baked into the `:warm` golden image** and present on both nodes of every freshly built cluster. Verified on 19 September: the rehearsal produced **zero `Pulling` events**. An `nginx:alpine` workload would have put a ~26 MB Docker Hub pull inside the recovery clock and measured the internet instead of the platform.

### Pre-flight gates — abort, never adjust

Context is `kind-cluster2`; `supportContainerResources` present with `cpu: "1"` (worth ~8 s per VM start, and it is cluster state, not manifest state); the `:warm` image cached, recording its image **ID** rather than trusting the tag; no UI backend or warm-pool controller running, which would rebuild a standby mid-drill; MemAvailable recorded; the `ollama-warm` schedule's `lastRunTime` recorded before and after each run, since it has a four-minute cadence and a run is shorter than that.

### What this drill cannot claim

- **It is not a production MTTR.** No detection, no decision, no data recovery, no HA, no storage re-attach, no DNS or ingress reprogramming, no other tenants. It is a lower bound on mechanical rebuild time.
- **It is not provisioning from scratch.** The `:warm` image carries a pre-initialised k3s datastore, which is why each run records `kube-system`'s `creationTimestamp` next to the nodes'. They differ: the namespace carries the *bake* date, the nodes the *build* date. This is restore-from-image.
- **"Both nodes Ready" is not two nodes of capacity.** The worker carries `node.cloudprovider.kubernetes.io/uninitialized:NoSchedule` and nothing removes it, so the drill's workload lands on the control plane.
- **No data survived, because there is none.**
- **It does not generalise to two concurrent clusters** — the fixed CA and token make exactly one `target-cluster` safe at a time.

### Results — 19 September 2026

`ch17-recovery-drill-20260919-163611.tsv`, N=5 after one discarded rehearsal. Host load 1.45–2.81 before runs; MemAvailable 13.1–13.6 GiB; the `ollama-warm` schedule did not fire during any run.

| Figure | Median | All five runs | Spread |
|---|---:|---|---:|
| **MTTR — destroy to first HTTP 200** | **81.96 s** | 80.40 / 81.20 / 81.96 / 82.59 / 84.03 | 3.63 s |
| Delete command returns | 10.13 s | 9.16 / 10.13 / 10.13 / 10.13 / 10.14 | 0.98 s |
| Teardown — last API object gone | 45.73 s | 44.76 / 45.58 / 45.73 / 45.97 / 46.00 | 1.24 s |
| Build — both nodes Ready | 34.39 s | 32.15 / 33.89 / 34.39 / 34.49 / 36.39 | 4.24 s |
| Build — control plane alone | 25.60 s | 25.30 / 25.46 / 25.60 / 25.67 / 26.08 | 0.78 s |
| Workload applied to first HTTP 200 | 1.34 s | 1.07 / 1.08 / 1.34 / 1.41 / 1.65 | 0.58 s |

**The build reproduces; the teardown does not.** 34.39 s against the published 33.7 s is well within the spread. But teardown, published at **18.9 s from a single run**, re-measures at **45.73 s** — more than twice the published figure, with a spread of only 1.24 s across five runs.

A separate run (N=1) split the two possible definitions of "gone", because the published figure counted API objects only:

| Boundary | Time |
|---|---:|
| Delete command returns | 9.11 s |
| qemu processes gone — the machines have actually stopped | 35.60 s |
| Last API object gone — what 18.9 s was measuring | 45.33 s |

So the objects outlive the machines by about ten seconds, and **neither definition reproduces 18.9 s.** The old figure was a single run and the book labelled it as such; it is superseded here.

### Every run, the same four observations

- **Zero `Pulling` events.** Nothing was fetched from the internet inside the clock.
- **The ghost node was excluded by name**, every run: `ubuntu-bake-vm-warm`, `Ready`, never counted.
- **The workload landed on the control plane**, every run — the worker's taint holds.
- **`kube-system` reports `creationTimestamp: 2026-09-16T07:10:33Z`** while the nodes were created that day. The namespace carries the *bake* date. This is restore-from-image, not provision-from-scratch.

### The shared-identity test

Run 1's admin kubeconfig, issued for `target-cluster-cp-ptkvc`, was kept. After five further destroy-rebuild cycles, it was presented to `target-cluster-cp-lmrt2` — a different cluster, 32 seconds old:

```
$ kubectl --kubeconfig /tmp/drill-kubeconfig-run1 get nodes
target-cluster-cp-lmrt2              Ready   control-plane   32s   v1.37.0+k3s1
target-cluster-workers-xq7mb-vbjr2   Ready   <none>          23s   v1.37.0+k3s1

$ kubectl --kubeconfig /tmp/drill-kubeconfig-run1 auth can-i '*' '*'
yes
```

**It authenticates, with full cluster-admin.** Chapter 5 observed this by accident; this is the deliberate test. The fixed CA set that removes the certificate work from the boot path — and buys the 34-second build — also means every cluster built from the `:warm` image is cryptographically the same cluster.

### One correction to Chapter 5

Chapter 5 records the worker as having *"been given nothing to do."* A pod that tolerates `node.cloudprovider.kubernetes.io/uninitialized` and pins to the worker by hostname **runs there normally** (verified 19 September, `drill-workload-worker.yaml`). The worker is not broken hardware; it is excluded by a scheduling gate. Nothing ordinary will land on it, which is the operative fact, but the machine works.

## Chapter 17 drill, re-run after the 18-second build (pre-registered)

**This section was written and committed BEFORE the first measured run of the re-run.**

Between 23 and 30 September the platform repository cut the build from 33.7 s to a reported 18.1 s (median of 5, `scripts/time-to-ready-by-name.sh`, 30 September; `docs/sub-60s-cluster-strategy.md` §7–§11). Every Chapter 17 figure was measured on the older platform. This re-run measures the same cycle on the new one.

**Nothing about the drill changes.** Same script (`ch-recovery-drill.sh`, unmodified), same boundaries T0–T9 as the table above, same workload (`drill-workload.yaml`), same pre-flight gates, N=5 after one discarded rehearsal, same headline (MTTR = T9 − T0).

**Platform state, recorded 8 October 2026 before any run:**

- `capi-controller-manager` runs with `--feature-gates=…ReconcilerRateLimiting=false…`
- CAPK image `172.18.0.2:5000/capk-manager:v0.11.2-kubeui2` (the patched build from `02-capi-init/patch-capk.sh`)
- `:warm` digest `sha256:0342dd8898bb…`, identical to `:warm-b1` (the image with `k3s-early.service` and the guest boot trims)
- KubeVirt v1.9.0, `supportContainerResources` cpu `1`; cluster2 server v1.37.0
- Manifest: `03-target-cluster/target-cluster-warm.yaml` at platform commit `f0f74a2`. Worker taint removed, worker gated on `/v1-k3s/readyz`, VM-to-VM routes on both VMs.

**Stated in advance, so the result can contradict them:**

1. **Build (T6 − T4) near 18 s.** The repository reports 18.1 s from a different script. A median outside 16–21 s would mean the two instruments disagree, and the book would report that disagreement instead of picking one.
2. **The workload may now land on the worker.** The taint that kept every pod on the control plane is gone. Record the node either way. If the pod lands on the worker, T9 also shows that the control plane can reach a pod on the worker, which was impossible before the VM-to-VM fix.
3. **Teardown (T2 − T0) is expected to be roughly unchanged, around 45 s.** None of the September work targeted deletion. If teardown is still about 45 s, it is now more than twice the build and the largest share of the MTTR.
4. **No prediction is made for the headline MTTR.** Arithmetic from expectations 1 and 3 would suggest about 66 s. It is not a target, and the result is reported whatever it is.

### Results — 8 October 2026

`ch17-recovery-drill-20261008-011322.tsv`, N=5 after one discarded rehearsal (`ch17-recovery-drill-20261008-011221.tsv`). Host load 2.98–3.68 before runs (higher than on 19 September); MemAvailable 14.2 GiB; the `ollama-warm` schedule did not fire during any run (`lastRunTime` 29 September throughout).

| Figure | Median | All five runs | Spread | 19 September |
|---|---:|---|---:|---:|
| **MTTR — destroy to first HTTP 200** | **59.97 s** | 59.06 / 59.43 / 59.97 / 60.21 / 60.46 | 1.40 s | 81.96 s |
| Delete command returns | 0.83 s | 0.66 / 0.69 / 0.83 / 0.91 / 0.95 | 0.29 s | 10.13 s |
| Teardown — last API object and qemu gone | 40.02 s | 39.92 / 39.99 / 40.02 / 40.11 / 40.31 | 0.39 s | 45.73 s |
| Seed secrets | 0.73 s | 0.72 / 0.72 / 0.73 / 0.73 / 0.77 | 0.05 s | — |
| Build — both nodes Ready | 17.95 s | 16.91 / 17.93 / 17.95 / 17.98 / 18.24 | 1.33 s | 34.39 s |
| Build — control plane alone | 14.11 s | 13.50 / 14.11 / 14.11 / 14.18 / 14.40 | 0.90 s | 25.60 s |
| Workload applied to first HTTP 200 | 1.09 s | 0.74 / 1.04 / 1.09 / 1.35 / 1.36 | 0.62 s | 1.34 s |

**Against the pre-registered expectations:**

1. **Build near 18 s — held.** 17.95 s against the repository's 18.1 s from a different script. The two instruments agree.
2. **Workload on the worker — did not happen, for a different reason than before.** The pod landed on the control plane in all five runs. The worker carried no taint (checked on the run-5 cluster: both nodes untainted, with system pods on each), so this was ordinary scheduling, not exclusion. A pod pinned to the worker on that cluster served through the API server's proxy (HTTP 200), and a pod on the control plane reached it directly across nodes. Both paths were impossible before 23 September.
3. **Teardown roughly unchanged at ~45 s — wrong.** It fell to **40.02 s**, and the delete command now returns in under a second instead of ten. This was not predicted and **not investigated**. The September controller changes (the patched CAPK and Cluster API's rate limiter, both of which act during deletion too) are the obvious candidates, but nothing here separates them. The qemu-versus-objects split from 19 September was not re-run. Teardown is now 2.2× the build and two-thirds of the MTTR.
4. **No MTTR prediction was made.** The arithmetic in the pre-registration suggested about 66 s. The measured value is 59.97 s, and two of the five runs were above 60.

**Every run:** zero `Pulling` events; the ghost node `ubuntu-bake-vm-warm` was excluded by name; `kube-system` reports `creationTimestamp: 2026-09-29T21:06:16Z`, the bake date of the current `:warm` image (it was 16 September in the earlier drill). The image changed and the restore-from-image property did not.

The shared-identity test was not repeated. The CA set and join token are unchanged, so nothing here bears on it.
