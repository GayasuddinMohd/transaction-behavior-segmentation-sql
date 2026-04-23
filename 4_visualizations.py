import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
from sqlalchemy import create_engine

# ── Output folder ──────────────────────────────────────────
os.makedirs("charts", exist_ok=True)
# ── Style ──────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({"figure.dpi": 150, "font.size": 11})
# ── DB Connection ──────────────────────────────────────────
engine = create_engine("mysql+mysqlconnector://root:dark%40123_HUM@localhost/transaction_analysis")
print("✅ Connected to MySQL")
def run(sql):
    with engine.connect() as conn:
        return pd.read_sql(sql, conn)

# ============================================================
# CHART 1 : Revenue by Category (Horizontal Bar)
# ============================================================
df1 = run("""
    SELECT p.category,
           ROUND(SUM(ti.quantity * ti.unit_price)/1e6, 2) AS revenue_million
    FROM transactions t
    JOIN transaction_items ti ON t.txn_id  = ti.txn_id
    JOIN products p            ON ti.product_id = p.product_id
    WHERE t.status = 'completed'
    GROUP BY p.category ORDER BY revenue_million DESC
""")

fig, ax = plt.subplots(figsize=(9, 4))
colors = ["#2563EB","#16A34A","#D97706","#DC2626","#7C3AED"]
bars = ax.barh(df1["category"], df1["revenue_million"], color=colors, edgecolor="white")
ax.bar_label(bars, fmt="₹%.1f M", padding=4, fontsize=10)
ax.set_xlabel("Revenue (₹ Millions)")
ax.set_title("Revenue by Product Category", fontweight="bold", fontsize=14)
ax.invert_yaxis()
plt.tight_layout()
plt.savefig("charts/01_revenue_by_category.png")
plt.close()
print("✅ Chart 1 saved")

# ============================================================
# CHART 2 : Revenue by Hour of Day (Bar — highlight evening)
# ============================================================
df2 = run("""
    SELECT HOUR(t.txn_datetime) AS hour_of_day,
           ROUND(SUM(ti.quantity * ti.unit_price)/1e6, 2) AS revenue_million
    FROM transactions t
    JOIN transaction_items ti ON t.txn_id = ti.txn_id
    WHERE t.status = 'completed'
    GROUP BY HOUR(t.txn_datetime) ORDER BY hour_of_day
""")

fig, ax = plt.subplots(figsize=(13, 5))
bar_colors = ["#F97316" if 18 <= h <= 22 else "#93C5FD" for h in df2["hour_of_day"]]
ax.bar(df2["hour_of_day"], df2["revenue_million"], color=bar_colors, edgecolor="white", width=0.8)
ax.set_xticks(range(0, 24))
ax.set_xlabel("Hour of Day (24h)")
ax.set_ylabel("Revenue (₹ Millions)")
ax.set_title("Revenue by Hour of Day  |  🟠 Evening Window (6 PM – 10 PM)", fontweight="bold", fontsize=13)

# Annotation band
ax.axvspan(17.5, 22.5, alpha=0.08, color="orange", label="Evening window")
total_rev = df2["revenue_million"].sum()
eve_rev   = df2[df2["hour_of_day"].between(18, 22)]["revenue_million"].sum()
ax.annotate(f"Evening = {eve_rev/total_rev*100:.1f}% of revenue",
            xy=(20, df2["revenue_million"].max()*0.92),
            fontsize=11, color="#C2410C", fontweight="bold")
plt.tight_layout()
plt.savefig("charts/02_revenue_by_hour.png")
plt.close()
print("✅ Chart 2 saved")

# ============================================================
# CHART 3 : Evening vs Other Hours (Donut)
# ============================================================
df3 = run("""
    SELECT
        CASE WHEN HOUR(t.txn_datetime) BETWEEN 18 AND 22
             THEN 'Evening (6-10 PM)' ELSE 'Other Hours' END AS time_window,
        ROUND(SUM(ti.quantity * ti.unit_price)/1e6, 2) AS revenue_million
    FROM transactions t
    JOIN transaction_items ti ON t.txn_id = ti.txn_id
    WHERE t.status = 'completed'
    GROUP BY time_window
""")

fig, ax = plt.subplots(figsize=(6, 6))
wedge_colors = ["#F97316","#93C5FD"]
wedges, texts, autotexts = ax.pie(
    df3["revenue_million"], labels=df3["time_window"],
    autopct="%1.1f%%", colors=wedge_colors,
    startangle=90, wedgeprops=dict(width=0.55),
    textprops={"fontsize": 12}
)
autotexts[0].set_fontweight("bold")
ax.set_title("Evening vs Other Hours — Revenue Share", fontweight="bold", fontsize=13)
plt.tight_layout()
plt.savefig("charts/03_evening_donut.png")
plt.close()
print("✅ Chart 3 saved")

# ============================================================
# CHART 4 : Revenue by Day of Week
# ============================================================
df4 = run("""
    SELECT DAYNAME(txn_datetime) AS day_name,
           DAYOFWEEK(txn_datetime) AS day_num,
           ROUND(SUM(ti.quantity * ti.unit_price)/1e6, 2) AS revenue_million
    FROM transactions t
    JOIN transaction_items ti ON t.txn_id = ti.txn_id
    WHERE t.status = 'completed'
    GROUP BY day_name, day_num ORDER BY day_num
""")

fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(df4["day_name"], df4["revenue_million"], color="#6366F1", edgecolor="white")
ax.set_ylabel("Revenue (₹ Millions)")
ax.set_title("Revenue by Day of Week", fontweight="bold", fontsize=13)
for bar, val in zip(ax.patches, df4["revenue_million"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"₹{val:.1f}M", ha="center", fontsize=9)
plt.tight_layout()
plt.savefig("charts/04_revenue_by_day.png")
plt.close()
print("✅ Chart 4 saved")

# ============================================================
# CHART 5 : User Segmentation Heatmap
# ============================================================
df5 = run("""
    WITH user_stats AS (
        SELECT t.user_id,
               COUNT(DISTINCT t.txn_id) AS order_count,
               AVG(t.total_amount)      AS avg_order_value
        FROM transactions t WHERE t.status='completed' GROUP BY t.user_id
    )
    SELECT
        CASE WHEN order_count>=20 THEN 'High Frequency'
             WHEN order_count>=10 THEN 'Mid Frequency'
             ELSE 'Low Frequency' END AS freq_seg,
        CASE WHEN avg_order_value>=15000 THEN 'High Value'
             WHEN avg_order_value>=5000  THEN 'Mid Value'
             ELSE 'Low Value' END AS val_seg,
        COUNT(user_id) AS user_count
    FROM user_stats
    GROUP BY freq_seg, val_seg
""")

pivot = df5.pivot(index="freq_seg", columns="val_seg", values="user_count").fillna(0)
freq_order = ["High Frequency","Mid Frequency","Low Frequency"]
val_order  = ["High Value","Mid Value","Low Value"]
pivot = pivot.reindex(index=freq_order, columns=val_order)

fig, ax = plt.subplots(figsize=(7, 4))
sns.heatmap(pivot, annot=True, fmt=".0f", cmap="YlOrRd",
            linewidths=0.5, ax=ax, cbar_kws={"label":"Users"})
ax.set_title("User Segmentation Matrix\n(Frequency × Order Value)", fontweight="bold", fontsize=13)
ax.set_xlabel("Order Value Segment")
ax.set_ylabel("Frequency Segment")
plt.tight_layout()
plt.savefig("charts/05_user_segmentation_heatmap.png")
plt.close()
print("✅ Chart 5 saved")

# ============================================================
# CHART 6 : Top 10 Products by Revenue
# ============================================================
df6 = run("""
    SELECT p.product_name, p.category,
           ROUND(SUM(ti.quantity * ti.unit_price)/1e6, 2) AS revenue_million
    FROM transaction_items ti
    JOIN products p     ON ti.product_id = p.product_id
    JOIN transactions t ON ti.txn_id = t.txn_id
    WHERE t.status='completed'
    GROUP BY p.product_id, p.product_name, p.category
    ORDER BY revenue_million DESC LIMIT 10
""")

cat_colors = {"Electronics":"#2563EB","Home":"#16A34A",
              "Fashion":"#D97706","Food":"#DC2626","Books":"#7C3AED"}
colors6 = [cat_colors.get(c,"#6B7280") for c in df6["category"]]

fig, ax = plt.subplots(figsize=(10, 5))
bars6 = ax.barh(df6["product_name"], df6["revenue_million"], color=colors6, edgecolor="white")
ax.bar_label(bars6, fmt="₹%.1f M", padding=4, fontsize=9)
ax.set_xlabel("Revenue (₹ Millions)")
ax.set_title("Top 10 Products by Revenue", fontweight="bold", fontsize=13)
ax.invert_yaxis()

from matplotlib.patches import Patch
legend_elements = [Patch(facecolor=v, label=k) for k, v in cat_colors.items()]
ax.legend(handles=legend_elements, loc="lower right", fontsize=9)
plt.tight_layout()
plt.savefig("charts/06_top10_products.png")
plt.close()
print("✅ Chart 6 saved")

# ============================================================
# CHART 7 : Revenue by City
# ============================================================
df7 = run("""
    SELECT u.city,
           ROUND(SUM(ti.quantity * ti.unit_price)/1e6, 2) AS revenue_million
    FROM transactions t
    JOIN transaction_items ti ON t.txn_id = ti.txn_id
    JOIN users u               ON t.user_id = u.user_id
    WHERE t.status='completed'
    GROUP BY u.city ORDER BY revenue_million DESC
""")

fig, ax = plt.subplots(figsize=(9, 4))
ax.bar(df7["city"], df7["revenue_million"], color="#0EA5E9", edgecolor="white")
ax.set_ylabel("Revenue (₹ Millions)")
ax.set_title("Revenue by City", fontweight="bold", fontsize=13)
for bar, val in zip(ax.patches, df7["revenue_million"]):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
            f"₹{val:.1f}M", ha="center", fontsize=8.5)
plt.tight_layout()
plt.savefig("charts/07_revenue_by_city.png")
plt.close()
print("✅ Chart 7 saved")


print("\n🎉 All 7 charts saved in the 'charts/' folder!")
print("📁 Location: charts/")
print("   01_revenue_by_category.png")
print("   02_revenue_by_hour.png")
print("   03_evening_donut.png")
print("   04_revenue_by_day.png")
print("   05_user_segmentation_heatmap.png")
print("   06_top10_products.png")
print("   07_revenue_by_city.png")
