# parser.py — reads the CCS truck schedule Excel and returns a clean DataFrame

import pandas as pd
from config import INSTATION_PROVINCES, PROVINCE_TOLL_DEFAULTS


def parse_schedule(file) -> pd.DataFrame:
    """
    Accepts a file path or file-like object (from st.file_uploader).
    Returns a DataFrame with one row per order, columns:
        vehicle, customer, area, province, outstation, toll, overnight
    """
    df = pd.read_excel(file, sheet_name=0, header=None, engine="openpyxl")

    # Keep rows that have both a customer number and a sales order number
    data = df[
        df[0].notna() &
        df[2].notna() &
        (~df[2].astype(str).str.contains("Sales Order", na=False))
    ].copy()

    data.columns = [
        "customer_no", "customer", "sales_order",
        "volume", "area", "province", "vehicle_no", "remarks"
    ]

    # Drop header row if it slipped through
    data = data[data["province"] != "Province"].copy()

    # Forward-fill vehicle number (only the first row of each truck group has it)
    data["vehicle_no"] = data["vehicle_no"].replace("", pd.NA)
    data["vehicle_no"] = data["vehicle_no"].fillna(method="ffill")

    # Classify outstation
    data["province"] = data["province"].astype(str).str.strip()
    data["outstation"] = ~data["province"].isin(INSTATION_PROVINCES)

    # Assign default toll per province; 0 for in-station
    data["toll"] = data.apply(
        lambda r: PROVINCE_TOLL_DEFAULTS.get(r["province"], 0) if r["outstation"] else 0,
        axis=1
    )

    # Overnight defaults to False — user sets this in the UI
    data["overnight"] = False

    # Clean up
    data["area"] = data["area"].astype(str).str.strip()
    data["customer"] = data["customer"].astype(str).str.strip()
    data["vehicle_no"] = data["vehicle_no"].astype(str).str.strip()

    return data[[
        "vehicle_no", "customer", "area", "province",
        "outstation", "toll", "overnight"
    ]].reset_index(drop=True)
