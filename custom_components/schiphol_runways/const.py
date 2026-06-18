"""Constants for Schiphol Runway Monitor integration."""

DOMAIN = "schiphol_runways"
DEFAULT_SCAN_INTERVAL = 5  # minutes

# Runway sensor states
STATE_NOT_IN_USE = "not_in_use"
STATE_INBOUND    = "inbound"
STATE_OUTBOUND   = "outbound"

# Combined peak sensor state (kept for the combined sensor)
STATE_PEAK_INBOUND  = "inbound_peak"
STATE_PEAK_OUTBOUND = "outbound_peak"
STATE_PEAK_BOTH     = "inbound_and_outbound_peak"
STATE_NO_PEAK       = "no_peak"

# All Schiphol runways.
# "headings" lists all possible designators for that physical runway strip.
# "bearing" is the magnetic bearing of the lower-number end (for SVG drawing).
RUNWAYS: dict[str, dict] = {
    "06/24":   {"name": "Kaagbaan",         "headings": ["06", "24"],             "bearing": 58},
    "09/27":   {"name": "Oostbaan",          "headings": ["09", "27"],             "bearing": 87},
    "18C/36C": {"name": "Zwanenburgbaan",    "headings": ["18C", "36C", "18", "36"], "bearing": 183},
    "18L/36R": {"name": "Aalsmeerbaan",      "headings": ["18L", "36R"],           "bearing": 183},
    "18R/36L": {"name": "Polderbaan",        "headings": ["18R", "36L"],           "bearing": 183},
    "04/22":   {"name": "Buitenveldertbaan", "headings": ["04", "22"],             "bearing": 41},
}
