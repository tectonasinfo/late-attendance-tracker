import streamlit as st
import pandas as pd
from datetime import time
import io

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Late Attendance Tracker",
    page_icon="🕙",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif;
}

.stApp {
    background: #0f0f0f;
    color: #f0ede6;
}

h1, h2, h3 {
    font-family: 'Syne', sans-serif !important;
    font-weight: 800;
}

.header-box {
    background: linear-gradient(135deg, #1a1a1a 0%, #111 100%);
    border: 1px solid #2a2a2a;
    border-left: 4px solid #f5a623;
    border-radius: 8px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
}

.header-box h1 {
    font-size: 2.4rem;
    color: #f0ede6;
    margin: 0 0 0.3rem 0;
    letter-spacing: -1px;
}

.header-box p {
    color: #888;
    font-size: 0.95rem;
    margin: 0;
    font-family: 'DM Mono', monospace;
}

.metric-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 1.2rem 1.5rem;
    text-align: center;
}

.metric-card .value {
    font-size: 2rem;
    font-weight: 800;
    color: #f5a623;
    font-family: 'DM Mono', monospace;
}

.metric-card .label {
    font-size: 0.8rem;
    color: #666;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 0.3rem;
}

.fine-badge-0    { background: #1a2a1a; color: #4caf50; border: 1px solid #2d4a2d; }
.fine-badge-low  { background: #2a2a1a; color: #ffc107; border: 1px solid #4a4a2d; }
.fine-badge-high { background: #2a1a1a; color: #f44336; border: 1px solid #4a2d2d; }

.fine-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
}

.slab-table {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 1rem 1.5rem;
    font-family: 'DM Mono', monospace;
    font-size: 0.85rem;
}

.slab-row {
    display: flex;
    justify-content: space-between;
    padding: 0.4rem 0;
    border-bottom: 1px solid #222;
    color: #ccc;
}

.slab-row:last-child { border-bottom: none; }
.slab-row .amt { color: #f5a623; font-weight: 500; }

div[data-testid="stFileUploader"] {
    background: #1a1a1a;
    border: 2px dashed #333;
    border-radius: 8px;
    padding: 1rem;
}

div[data-testid="stDataFrame"] {
    border-radius: 8px;
    overflow: hidden;
}

.stDownloadButton > button {
    background: #f5a623 !important;
    color: #0f0f0f !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 0.5rem 1.5rem !important;
}

.section-label {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: #555;
    margin-bottom: 0.5rem;
    font-family: 'DM Mono', monospace;
}
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
    <h1>🕙 Late Attendance Tracker</h1>
    <p>Upload the Daily Details Report → Get late arrivals + fine summary instantly</p>
</div>
""", unsafe_allow_html=True)

# ── Fine slab reference ───────────────────────────────────────────────────────
with st.expander("📋 Fine Slab Reference", expanded=False):
    st.markdown("""
<div class="slab-table">
    <div class="slab-row"><span>Day 1–3 &nbsp;(₹0 each)</span><span class="amt">Cumulative: ₹0</span></div>
    <div class="slab-row"><span>Day 4–6 &nbsp;(₹50 each)</span><span class="amt">Cumulative: ₹150</span></div>
    <div class="slab-row"><span>Day 7–9 &nbsp;(₹100 each)</span><span class="amt">Cumulative: ₹450</span></div>
    <div class="slab-row"><span>Day 10–12 (₹150 each)</span><span class="amt">Cumulative: ₹900</span></div>
    <div class="slab-row"><span>Day 13–15 (₹200 each)</span><span class="amt">Cumulative: ₹1,500</span></div>
    <div class="slab-row"><span>Every +3 days after</span><span class="amt">+₹50 per day in that slab</span></div>
</div>
<br><small style="color:#555;font-family:'DM Mono',monospace;">
Late = Punch 1 between 09:31 and 09:59 · Saturdays are ignored
</small>
""", unsafe_allow_html=True)

# ── Fine calculation helper ───────────────────────────────────────────────────
def calculate_fine(late_count: int) -> int:
    """
    Cumulative fine across all late days:
    - Day 1–3  : ₹0 each   (grace period)
    - Day 4–6  : ₹50 each
    - Day 7–9  : ₹100 each
    - Day 10–12: ₹150 each
    - ... +₹50 per slab of 3
    """
    total = 0
    for day in range(1, late_count + 1):
        if day <= 3:
            total += 0
        else:
            # Which slab after grace? slab 1 = days 4-6, slab 2 = days 7-9, ...
            slab = (day - 4) // 3 + 1
            total += slab * 50
    return total

# ── Parse & process CSV ───────────────────────────────────────────────────────
def parse_and_process(file) -> pd.DataFrame:
    # Read raw CSV, skip blank lines, drop trailing empty column
    df = pd.read_csv(file, dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.dropna(subset=["EmpID"])
    df = df[df["EmpID"].str.strip() != ""]

    # Strip whitespace from all cells
    df = df.apply(lambda col: col.str.strip() if col.dtype == object else col)

    # Rename punch columns safely
    punch_col = "1 Punch"
    if punch_col not in df.columns:
        raise ValueError(f"Column '{punch_col}' not found. Columns: {list(df.columns)}")

    LATE_START = time(9, 31)
    LATE_END   = time(10, 0)

    results = []

    for (emp_id, emp_name), group in df.groupby(["EmpID", "EmpName"]):
        late_days = []
        for _, row in group.iterrows():
            # Skip Saturdays
            import datetime
            date_raw = str(row.get("Date", "")).strip()
            try:
                date_obj = datetime.datetime.strptime(date_raw, "%d-%b-%Y").date()
                if date_obj.weekday() == 5:  # 5 = Saturday
                    continue
            except Exception:
                pass  # If date can't be parsed, don't skip

            punch1_raw = str(row.get(punch_col, "")).strip()
            if not punch1_raw or punch1_raw in ("", "nan"):
                continue
            try:
                # Parse HH:MM:SS or HH:MM
                parts = punch1_raw.replace(" ", "").split(":")
                h, m = int(parts[0]), int(parts[1])
                punch_time = time(h, m)
            except Exception:
                continue

            if LATE_START <= punch_time < LATE_END:
                late_days.append({
                    "date": row.get("Date", ""),
                    "punch1": punch1_raw
                })

        if late_days:
            late_count = len(late_days)
            fine = calculate_fine(late_count)
            results.append({
                "Emp ID": emp_id,
                "Employee Name": emp_name,
                "Late Days": late_count,
                "Fine (₹)": fine,
                "Late Dates": ", ".join(d["date"] for d in late_days),
                "Punch Times": ", ".join(d["punch1"] for d in late_days),
            })

    if not results:
        return pd.DataFrame()

    out = pd.DataFrame(results).sort_values("Late Days", ascending=False).reset_index(drop=True)
    return out

# ── File upload ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-label">Upload Report</div>', unsafe_allow_html=True)
uploaded = st.file_uploader(
    "Drop your Daily Details Report here",
    type=["csv", "xlsx"],
    label_visibility="collapsed"
)

if uploaded:
    try:
        result_df = parse_and_process(uploaded)

        if result_df.empty:
            st.warning("No late arrivals found between 09:30 and 09:59 in the uploaded file.")
        else:
            # ── Summary metrics ───────────────────────────────────────────
            total_employees   = len(result_df)
            fined_employees   = len(result_df[result_df["Fine (₹)"] > 0])
            total_fine        = result_df["Fine (₹)"].sum()
            most_late         = result_df["Late Days"].max()

            c1, c2, c3, c4 = st.columns(4)
            for col, val, label in [
                (c1, total_employees, "Employees Late"),
                (c2, fined_employees, "With a Fine"),
                (c3, f"₹{total_fine}", "Total Fines"),
                (c4, most_late, "Max Late Days"),
            ]:
                col.markdown(f"""
                <div class="metric-card">
                    <div class="value">{val}</div>
                    <div class="label">{label}</div>
                </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # ── Display table ─────────────────────────────────────────────
            st.markdown('<div class="section-label">Results</div>', unsafe_allow_html=True)

            # Style the Fine column
            def style_fine(val):
                if val == 0:
                    return "color: #4caf50; font-weight: 600;"
                elif val <= 100:
                    return "color: #ffc107; font-weight: 600;"
                else:
                    return "color: #f44336; font-weight: 600;"

            styled = (
                result_df
                .style
                .applymap(style_fine, subset=["Fine (₹)"])
                .format({"Fine (₹)": "₹{:,.0f}"})
                .set_properties(**{"font-family": "DM Mono, monospace", "font-size": "13px"})
            )

            st.dataframe(styled, use_container_width=True, hide_index=True)

            # ── Download button ───────────────────────────────────────────
            st.markdown("<br>", unsafe_allow_html=True)
            csv_out = result_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="⬇ Download Report as CSV",
                data=csv_out,
                file_name="late_attendance_fines.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.exception(e)

else:
    st.markdown("""
    <div style="text-align:center; padding: 3rem; color: #444; font-family: 'DM Mono', monospace; font-size:0.9rem;">
        ↑ Upload a CSV file to get started
    </div>
    """, unsafe_allow_html=True)
