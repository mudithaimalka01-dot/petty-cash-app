# config.py — default settings (edit these to match your actual rates)

ROOM_RATE_DEFAULT = 3000        # LKR per night per driver
BUFFER_PCT_DEFAULT = 10         # % buffer on top of calculated total

# Provinces treated as in-station (no toll, no overnight)
INSTATION_PROVINCES = {
    "Colombo-Central",
    "Colombo-North",
    "Colombo-South",
}

# Default toll estimates by province (LKR)
# These are starting estimates — users can override per-order in the app
PROVINCE_TOLL_DEFAULTS = {
    "Central-L":        350,
    "Central-S":        300,
    "Ce-Nuwara Eliya":  450,
    "Chilaw R":         200,
    "Eastern":          800,
    "North":            700,
    "North Central-A":  600,
    "North West-K":     280,
    "Sabaragamuwa-R":   350,
    "Southern-D":       500,
    "Southern-S":       400,
    "Trinco":           650,
}
