"""Day 14, part 3: cProfile + in-process latency distribution (no HTTP).

1. 2,000 UNPROFILED calls to route_query -> p50 / p90 / p95 / p99 (profiling overhead would distort them).
2. 2,000 PROFILED calls -> where the time goes (cProfile, top functions by cumulative time).

Run from the repo root:
    python api/modules/intent_router/profiling/profile_cprofile.py
Output: reports/cprofile_top.txt, reports/cprofile.prof, reports/latency_percentiles.json,
        reports/figures/latency_histogram.png and cprofile_top.png (the PNGs need `pip install matplotlib`)
"""
import cProfile
import io
import json
import pstats
import time

from common import FIGURES, REPORTS, hardware, percentiles, query_pool
from modules.intent_router.service import SemanticRouter

N = 2000


def main():
    router = SemanticRouter()
    router.load()
    pool = query_pool()
    queries = [pool[i % len(pool)] for i in range(N)]

    lat = []
    for q in queries:                                    # 1. unprofiled distribution (service-internal time)
        t = time.perf_counter()
        router.route_query(q)
        lat.append((time.perf_counter() - t) * 1000)
    pc = percentiles(lat)

    prof = cProfile.Profile()                            # 2. profiled pass
    prof.enable()
    for q in queries:
        router.route_query(q)
    prof.disable()
    prof.dump_stats(str(REPORTS / "cprofile.prof"))
    buf = io.StringIO()
    pstats.Stats(prof, stream=buf).sort_stats("cumulative").print_stats(15)
    (REPORTS / "cprofile_top.txt").write_text(buf.getvalue(), encoding="utf-8")
    (REPORTS / "latency_percentiles.json").write_text(json.dumps({"hardware": hardware(), "calls": N, "ms": pc}, indent=2), encoding="utf-8")

    print(f"route_query over {N} calls (in-process, unprofiled), ms:")
    print("  " + " | ".join(f"{k} {pc[k]:.2f}" for k in ("p50", "p90", "p95", "p99", "max")))
    print(buf.getvalue())

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed: skipping PNG figures (pip install matplotlib)")
        return

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(lat, bins=60)
    for k, c in (("p50", "g"), ("p95", "orange"), ("p99", "r")):
        ax.axvline(pc[k], color=c, linestyle="--", label=f"{k} {pc[k]:.2f} ms")
    ax.set_xlabel("route_query latency (ms)")
    ax.set_ylabel("calls")
    ax.set_title(f"Latency distribution ({N} calls, CPU)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "latency_histogram.png", dpi=150)

    rows = sorted(pstats.Stats(prof).stats.items(), key=lambda kv: kv[1][3], reverse=True)[:10]
    names = [f"{fn[2]} ({fn[0].replace(chr(92), '/').split('/')[-1]}:{fn[1]})" for fn, _ in rows]
    per_call = [v[3] / N * 1000 for _, v in rows]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(names[::-1], per_call[::-1])
    ax.set_xlabel("cumulative ms per route_query call (profiled run)")
    ax.set_title("cProfile: where the time goes")
    fig.tight_layout()
    fig.savefig(FIGURES / "cprofile_top.png", dpi=150)
    print("figures saved to", FIGURES)


if __name__ == "__main__":
    main()
