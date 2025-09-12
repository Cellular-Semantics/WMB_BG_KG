import requests
import sys
from pathlib import Path

# Google Sheet ID and GID
SHEET_ID = "1NwO-_BQumtfVYcTNP--vRa5434Elvj5me1oEKV1Q-gE"
GID = "1470945829"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

# Output path
OUT_PATH = Path(__file__).parent.parent.parent / "resources" / "MWB_consensus_homology.csv"

def main():
    try:
        resp = requests.get(CSV_URL)
        resp.raise_for_status()
        OUT_PATH.write_bytes(resp.content)
        print(f"Downloaded and saved to {OUT_PATH}")
    except Exception as e:
        print(f"Error downloading sheet: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
