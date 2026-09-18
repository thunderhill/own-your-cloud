# Measurements

Raw data behind the book's measured claims, kept so that a reader can check the arithmetic rather than trust it.

## `ch19-parallel-metering-20260918.tsv`

The parallel-metering experiment in Chapter 19. Produced by `ch19-meter.sh`.

**Date:** 18 September 2026, 09:14:22–09:24:17 UTC.
**Workload:** one `nginx:alpine` deployment on the target cluster, served continuously through a ClusterIP Service, probed once per sample.
**Host:** the single laptop described in the prologue — AMD Ryzen AI 9 HX 370, 24 threads, 29.96 GiB, NVIDIA RTX 4050 laptop GPU, on AC power.
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
| Host capital cost | $1,500–$3,000 | assumption; a laptop of this class. Substitute your own |
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
