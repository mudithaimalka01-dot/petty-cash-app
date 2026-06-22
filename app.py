# app.py — CCS Petty Cash Estimator (Streamlit)
# Run:  streamlit run app.py

import io
import pandas as pd
import streamlit as st

from parser import parse_schedule
from calculator import calc_per_truck, calc_summary
from config import ROOM_RATE_DEFAULT, BUFFER_PCT_DEFAULT

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CCS Petty Cash Estimator",
    page_icon="🚛",
    layout="wide",
)

st.title("CCS Petty Cash Estimator")
st.caption("Upload tomorrow's truck schedule → get the petty cash requirement instantly.")

# ── Sidebar config ────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Settings")
    room_rate = st.number_input(
        "Room charge per night (LKR)",
        min_value=0,
        value=ROOM_RATE_DEFAULT,
        step=500,
    )
    buffer_pct = st.slider(
        "Buffer %",
        min_value=0,
        max_value=30,
        value=BUFFER_PCT_DEFAULT,
    )
    st.divider()
    st.markdown("**Toll rates** are editable in the order table below.")

# ── File upload ───────────────────────────────────────────────────────────────
uploaded = st.file_uploader(
    "Upload schedule Excel (.xlsx)",
    type=["xlsx"],
    help="Use the CCS truck schedule format — one sheet, Customer No in col A.",
)

if uploaded is None:
    st.info("Upload a schedule file to get started.")
    st.stop()

# ── Parse ─────────────────────────────────────────────────────────────────────
try:
    df = parse_schedule(uploaded)
except Exception as e:
    st.error(f"Could not read the file: {e}")
    st.stop()

st.success(f"Loaded {len(df)} orders across {df['vehicle_no'].nunique()} trucks.")

# ── Order editor (toll + overnight adjustments) ───────────────────────────────
st.subheader("Order detail — adjust tolls & overnight")
st.caption("Edit the Toll (LKR) column and tick the Overnight column for any driver staying out.")

edited = st.data_editor(
    df,
    column_config={
        "vehicle_no":  st.column_config.TextColumn("Truck",       disabled=True),
        "customer":    st.column_config.TextColumn("Customer",    disabled=True),
        "area":        st.column_config.TextColumn("Area",        disabled=True),
        "province":    st.column_config.TextColumn("Province",    disabled=True),
        "outstation":  st.column_config.CheckboxColumn("Outstation", disabled=True),
        "toll":        st.column_config.NumberColumn("Toll (LKR)", min_value=0, step=50),
        "overnight":   st.column_config.CheckboxColumn("Overnight?"),
    },
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    key="order_editor",
)

# ── Calculate ─────────────────────────────────────────────────────────────────
trucks = calc_per_truck(edited, room_rate=room_rate)
summary = calc_summary(trucks, buffer_pct=buffer_pct)

# ── Summary metrics ───────────────────────────────────────────────────────────
st.divider()
st.subheader("Summary")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total trucks",      summary["total_trucks"])
c2.metric("Outstation trucks", summary["outstation_trucks"])
c3.metric("Overnight stays",   summary["overnight_stays"])
c4.metric("Petty cash needed", f"LKR {summary['grand_total']:,}")

# ── Breakdown ─────────────────────────────────────────────────────────────────
st.subheader("Breakdown")
col_l, col_r = st.columns([1, 1])

with col_l:
    breakdown = pd.DataFrame({
        "Component": [
            "Highway tolls",
            "Room charges",
            "Subtotal",
            f"Buffer ({buffer_pct}%)",
            "Total petty cash",
        ],
        "LKR": [
            summary["total_tolls"],
            summary["total_rooms"],
            summary["subtotal"],
            summary["buffer"],
            summary["grand_total"],
        ],
    })
    st.dataframe(
        breakdown,
        use_container_width=True,
        hide_index=True,
        column_config={
            "LKR": st.column_config.NumberColumn(format="LKR %d")
        },
    )

with col_r:
    st.subheader("Per-truck summary")
    truck_display = trucks.rename(columns={
        "vehicle_no":       "Truck",
        "is_outstation":    "Outstation",
        "total_toll":       "Toll (LKR)",
        "overnight":        "Overnight",
        "room_charge":      "Room (LKR)",
        "truck_total":      "Total (LKR)",
    })
    st.dataframe(
        truck_display,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Toll (LKR)":  st.column_config.NumberColumn(format="LKR %d"),
            "Room (LKR)":  st.column_config.NumberColumn(format="LKR %d"),
            "Total (LKR)": st.column_config.NumberColumn(format="LKR %d"),
        },
    )

# ── Excel export ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("Download report")


def build_excel(trucks_df: pd.DataFrame, summary_dict: dict, buffer: float) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
        # Per-truck sheet
        trucks_df.rename(columns={
            "vehicle_no":    "Truck",
            "is_outstation": "Outstation",
            "total_toll":    "Toll (LKR)",
            "overnight":     "Overnight",
            "room_charge":   "Room (LKR)",
            "truck_total":   "Total (LKR)",
        }).to_excel(writer, sheet_name="Per-Truck", index=False)

        # Summary sheet
        summary_rows = [
            ["Highway tolls",         summary_dict["total_tolls"]],
            ["Room charges",          summary_dict["total_rooms"]],
            ["Subtotal",              summary_dict["subtotal"]],
            [f"Buffer ({buffer:.0f}%)", summary_dict["buffer"]],
            ["Total petty cash",      summary_dict["grand_total"]],
        ]
        pd.DataFrame(summary_rows, columns=["Component", "LKR"]).to_excel(
            writer, sheet_name="Summary", index=False
        )
    return buf.getvalue()


excel_bytes = build_excel(trucks, summary, buffer_pct)
st.download_button(
    label="⬇ Download Excel report",
    data=excel_bytes,
    file_name="petty_cash_estimate.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
