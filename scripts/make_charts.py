#!/usr/bin/env python3
"""
make_charts.py -- builds the seven required figures from the MapReduce output.

Every chart is drawn from output/*.tsv, i.e. from the actual reducer output
pulled out of HDFS - nothing here re-computes a statistic.

Design rules applied (kept deliberately consistent across all seven):
  * form follows the data's job - magnitude comparisons are bars, the
    distance/revenue relationship is a scatter;
  * ONE measure per axis, never a second y-scale;
  * a single hue where the bars are one series (colour would carry no
    information); the validated categorical slots 1 and 2 only where an actual
    grouping exists (weekday vs weekend), where a legend is also present;
  * recessive grid and axes, thin marks, direct value labels rather than a
    label on every gridline.
"""
import sys, os, csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, os.path.dirname(__file__))
import zones

OUT = os.path.join(os.path.dirname(__file__), "..", "charts")
RES = os.path.join(os.path.dirname(__file__), "..", "output")
os.makedirs(OUT, exist_ok=True)

SURFACE   = "#fcfcfb"
INK       = "#0b0b0b"
INK2      = "#52514e"
MUTED     = "#8a8880"
SERIES1   = "#2a78d6"   # validated categorical slot 1
SERIES2   = "#eb6834"   # validated categorical slot 2
GRID      = "#e4e3de"

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE, "font.size": 10,
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "font.family": "DejaVu Sans",
})

def rows(name):
    p = os.path.join(RES, name + ".tsv")
    with open(p) as fh:
        return [l.rstrip("\n").split("\t") for l in fh if l.strip()]

def style(ax, title, sub=None, xlabel=None, ylabel=None, xgrid=False, fig=None):
    if fig is not None:
        # horizontal-bar charts have wide y labels, so the axes left edge sits
        # far to the right; anchor the title to the FIGURE instead.
        fig.text(0.012, 0.975, title, fontsize=13, fontweight="bold", color=INK,
                 ha="left", va="top")
        if sub:
            fig.text(0.012, 0.928, sub, fontsize=9, color=MUTED, ha="left", va="top")
    else:
        ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK, pad=16 if sub else 10)
        if sub:
            ax.text(0, 1.02, sub, transform=ax.transAxes, fontsize=9, color=MUTED, va="bottom")
    if xlabel: ax.set_xlabel(xlabel, fontsize=9)
    if ylabel: ax.set_ylabel(ylabel, fontsize=9)
    ax.grid(axis="x" if xgrid else "y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)

def save(fig, name, top=None, tight=True):
    if tight:
        fig.tight_layout(rect=(0, 0, 1, top) if top else None)
    p = os.path.join(OUT, name + ".png")
    fig.savefig(p, dpi=170)
    plt.close(fig)
    print("wrote", p)

thousands = FuncFormatter(lambda v, p: f"{v:,.0f}")

# ---------------------------------------------------------------- 1. by hour
def chart_hourly():
    d = [(r[0], int(r[1])) for r in rows("hourly")]
    d.sort()
    hrs = [x[0] for x in d]; v = [x[1] for x in d]
    peak = max(range(len(v)), key=lambda i: v[i]); low = min(range(len(v)), key=lambda i: v[i])
    fig, ax = plt.subplots(figsize=(9, 4.4))
    bars = ax.bar(hrs, v, color=SERIES1, width=0.68)
    bars[peak].set_color("#1a4f92"); bars[low].set_color("#a9c6ea")
    ax.yaxis.set_major_formatter(thousands)
    for i in (peak, low):
        ax.annotate(f"{v[i]:,}", (i, v[i]), textcoords="offset points", xytext=(0, 5),
                    ha="center", fontsize=9, color=INK, fontweight="bold")
    style(ax, "Taxi demand by hour of day",
          f"{sum(v):,} cleaned trips, NYC yellow taxi, Jan-Mar 2026 - busiest hour {hrs[peak]}:00, quietest {hrs[low]}:00",
          "Hour of pickup (24h)", "Trips")
    save(fig, "01_trips_by_hour")

# ------------------------------------------------------------- 2. day of week
def chart_daily():
    d = []
    for r in rows("daily"):
        n, day, kind = r[0].split("_")
        d.append((int(n), day, kind, int(r[1])))
    d.sort()
    lab = [x[1][:3] for x in d]; v = [x[3] for x in d]
    col = [SERIES2 if x[2] == "WEEKEND" else SERIES1 for x in d]
    fig, ax = plt.subplots(figsize=(8, 4.9))
    ax.bar(lab, v, color=col, width=0.62)
    ax.yaxis.set_major_formatter(thousands)
    for i, val in enumerate(v):
        ax.annotate(f"{val:,}", (i, val), textcoords="offset points", xytext=(0, 4),
                    ha="center", fontsize=8.5, color=INK2)
    wd = sum(x[3] for x in d if x[2] == "WEEKDAY"); we = sum(x[3] for x in d if x[2] == "WEEKEND")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=SERIES1, label=f"Weekday - {wd:,} trips ({wd/(wd+we)*100:.1f}%)"),
                       Patch(color=SERIES2, label=f"Weekend - {we:,} trips ({we/(wd+we)*100:.1f}%)")],
              frameon=False, fontsize=9.5, ncol=2, loc="upper center",
              bbox_to_anchor=(0.5, -0.09))   # below the axis: never over a bar
    style(ax, "Taxi demand by day of week",
          "Weekday and weekend are also separated by position and by label, not colour alone",
          None, "Trips")
    fig.subplots_adjust(bottom=0.20, top=0.86, left=0.13, right=0.97)
    save(fig, "02_trips_by_day", tight=False)

# ------------------------------------------------------- 3. top 10 pickup zones
def chart_top_zones():
    d = [(zones.short(int(r[1])), int(r[2])) for r in rows("top10_zones_trips")]
    d.reverse()
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh([x[0] for x in d], [x[1] for x in d], color=SERIES1, height=0.66)
    ax.xaxis.set_major_formatter(thousands)
    for i, (_, val) in enumerate(d):
        ax.annotate(f"{val:,}", (val, i), textcoords="offset points", xytext=(6, 0),
                    va="center", fontsize=9, color=INK2)
    ax.set_xlim(0, max(x[1] for x in d) * 1.14)
    style(ax, "Top 10 pickup zones by trip count",
          "Ranked by MapReduce job 12 (Top-N pattern) over all 262 zones present in the cleaned data",
          "Trips", None, xgrid=True, fig=fig)
    save(fig, "03_top10_pickup_zones", top=0.90)

# ------------------------------------------------- 4. revenue by payment method
def chart_payment():
    d = []
    for r in rows("payment"):
        code, label = r[0].split("_", 1)
        d.append((label, int(r[1]), float(r[2])))
    d = [x for x in d if x[2] > 0]
    d.sort(key=lambda x: x[2])
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.barh([x[0] for x in d], [x[2] / 1e6 for x in d], color=SERIES1, height=0.62)
    tot = sum(x[2] for x in d)
    for i, x in enumerate(d):
        ax.annotate(f"${x[2]/1e6:,.1f}M  ({x[2]/tot*100:.1f}%)", (x[2] / 1e6, i),
                    textcoords="offset points", xytext=(6, 0), va="center",
                    fontsize=9, color=INK2)
    ax.set_xlim(0, max(x[2] for x in d) / 1e6 * 1.35)
    style(ax, "Total revenue by payment method",
          f"Total fare revenue ${tot/1e6:,.1f}M across {sum(x[1] for x in d):,} cleaned trips",
          "Total revenue (USD, millions)", None, xgrid=True, fig=fig)
    save(fig, "04_revenue_by_payment", top=0.89)

# --------------------------------------------------- 5. trips by distance band
def chart_distance():
    d = []
    for r in rows("distance"):
        _, band = r[0].split("_", 1)
        d.append((band, int(r[1]), float(r[3])))   # band, trips, avg_fare
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.bar([x[0] for x in d], [x[1] for x in d], color=SERIES1, width=0.6)
    ax.yaxis.set_major_formatter(thousands)
    tot = sum(x[1] for x in d)
    for i, x in enumerate(d):
        ax.annotate(f"{x[1]:,}\n{x[1]/tot*100:.1f}%\navg ${x[2]:,.2f}", (i, x[1]),
                    textcoords="offset points", xytext=(0, 5), ha="center",
                    fontsize=8.5, color=INK2)
    ax.set_ylim(0, max(x[1] for x in d) * 1.22)
    style(ax, "Trips by distance band",
          "Bar height is trip count; the average fare for each band is printed on the bar",
          "Trip distance band", "Trips")
    save(fig, "05_trips_by_distance")

# ---------------------------------------------------------- 6. top 10 routes
def chart_routes():
    d = []
    for r in rows("top20_routes_trips")[:10]:
        pu, do = r[1].split("->")
        d.append((f"{zones.short(int(pu))}  ->  {zones.short(int(do))}", int(r[2])))
    d.reverse()
    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.barh([x[0] for x in d], [x[1] for x in d], color=SERIES1, height=0.66)
    ax.xaxis.set_major_formatter(thousands)
    for i, (_, val) in enumerate(d):
        ax.annotate(f"{val:,}", (val, i), textcoords="offset points", xytext=(6, 0),
                    va="center", fontsize=9, color=INK2)
    ax.set_xlim(0, max(x[1] for x in d) * 1.16)
    style(ax, "Top 10 pickup -> drop-off routes by trip count",
          "Composite key PULocationID->DOLocationID; ranked from ~70k distinct routes",
          "Trips", None, xgrid=True, fig=fig)
    save(fig, "06_top10_routes", top=0.90)

# ------------------------------------------------------ 7. revenue vs distance
def chart_revenue_distance():
    pts = []
    for r in rows("revenue"):
        trips = int(r[1]); avg_dist = float(r[7]); avg_rev = float(r[4]) / trips
        if trips >= 500:
            pts.append((int(r[0]), trips, avg_dist, avg_rev))
    fig, ax = plt.subplots(figsize=(9, 5.2))
    sizes = [max(12, min(420, t / 900)) for _, t, _, _ in pts]
    ax.scatter([p[2] for p in pts], [p[3] for p in pts], s=sizes,
               color=SERIES1, alpha=0.55, edgecolors=SURFACE, linewidths=1.4)
    for zid in (132, 138, 230, 161, 237):
        for p in pts:
            if p[0] == zid:
                ax.annotate(zones.short(zid), (p[2], p[3]), textcoords="offset points",
                            xytext=(8, 6), fontsize=9, color=INK, fontweight="bold")
    ax.margins(x=0.14)
    style(ax, "Revenue versus distance, by pickup zone",
          "One dot per pickup zone with >=500 trips; dot area is trip volume. Both axes are per-trip averages.",
          "Average trip distance from the zone (miles)", "Average revenue per trip (USD)")
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    save(fig, "07_revenue_vs_distance")

if __name__ == "__main__":
    for fn in (chart_hourly, chart_daily, chart_top_zones, chart_payment,
               chart_distance, chart_routes, chart_revenue_distance):
        try:
            fn()
        except Exception as e:
            print("FAILED", fn.__name__, type(e).__name__, e)
