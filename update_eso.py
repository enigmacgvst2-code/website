import json
import urllib.parse
import urllib.request

PROGRAM_ID = "114.27U3.001"
clean_id = PROGRAM_ID.lstrip("0")

# ADQL Query requesting target, instrument, start time, airmass, and seeing
query = f"""
SELECT target, instrument, dp_start, tel_airm_start, tel_ambi_fwhm_start 
FROM dbo.raw 
WHERE (prog_id LIKE '%{clean_id}%' OR prog_id LIKE '%{PROGRAM_ID}%')
  AND dp_cat = 'SCIENCE' 
ORDER BY dp_start ASC
"""

eso_url = f"https://archive.eso.org/tap_obs/sync?REQUEST=doQuery&LANG=ADQL&FORMAT=json&QUERY={urllib.parse.quote(query)}"

print(f"Fetching observation records from ESO for program {PROGRAM_ID}...")
req = urllib.request.Request(eso_url, headers={"User-Agent": "Mozilla/5.0"})

try:
    with urllib.request.urlopen(req, timeout=30) as response:
        raw_data = response.read().decode()
        data = json.loads(raw_data)

        # Write output to data.json
        with open("data.json", "w") as f:
            json.dump(data, f, indent=2)

        record_count = len(data.get("data", []))
        print(
            f"Successfully updated data.json! Saved {record_count} observations."
        )

except Exception as e:
    print(f"Error fetching data from ESO: {e}")
    exit(1)
