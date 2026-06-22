# calculator.py — petty cash calculation logic

import pandas as pd
from config import ROOM_RATE_DEFAULT


def calc_per_truck(df: pd.DataFrame, room_rate: int = ROOM_RATE_DEFAULT) -> pd.DataFrame:
    """
    Groups orders by vehicle and computes per-truck petty cash.

    Input df must have columns:
        vehicle_no, outstation, toll, overnight

    Returns a DataFrame with one row per truck:
        vehicle_no, is_outstation, total_toll, overnight, room_charge, truck_total
    """
    trucks = (
        df.groupby("vehicle_no", sort=False)
        .agg(
            is_outstation=("outstation", "any"),
            total_toll=("toll", "sum"),
            overnight=("overnight", "any"),
        )
        .reset_index()
    )

    trucks["room_charge"] = trucks.apply(
        lambda r: room_rate if r["overnight"] and r["is_outstation"] else 0,
        axis=1
    )
    trucks["truck_total"] = trucks["total_toll"] + trucks["room_charge"]
    return trucks


def calc_summary(trucks: pd.DataFrame, buffer_pct: float) -> dict:
    """
    Rolls up truck-level data into a single summary dict.
    """
    total_tolls = trucks["total_toll"].sum()
    total_rooms = trucks["room_charge"].sum()
    subtotal = total_tolls + total_rooms
    buffer = subtotal * buffer_pct / 100
    grand_total = subtotal + buffer

    return {
        "total_trucks":    len(trucks),
        "outstation_trucks": trucks["is_outstation"].sum(),
        "overnight_stays": trucks["overnight"].sum(),
        "total_tolls":     round(total_tolls),
        "total_rooms":     round(total_rooms),
        "subtotal":        round(subtotal),
        "buffer":          round(buffer),
        "grand_total":     round(grand_total),
    }
