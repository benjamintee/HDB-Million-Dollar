"""
HDB Resale Transactions Geocoder (2026)

End-to-end script to:
1. Download HDB resale data
2. Clean and deduplicate addresses
3. Geocode via OneMap
4. Remove non-residential matches
5. Spatially enrich results
6. Output final CSV
"""

# =====================================================
# Imports
# =====================================================
from functools import wraps
from pathlib import Path
from datetime import datetime, UTC
import os
import time
import re
import requests
import concurrent.futures

import pandas as pd
import geopandas as gpd
from tqdm import tqdm

# =====================================================
# Configuration
# =====================================================
DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(exist_ok=True)

DATASET_ID = "d_8b84c4ee58e3cfc0ece0d773c8ca6abc"
RAW_CSV = DATA_DIR / "hdb_resale_transactions.csv"

SUBZONE_SHP = Path(r"C:\Users\benja\OneDrive\Documents\R\Geocoder\URA_MP19_SUBZONE_NO_SEA_PL.shp")
ELD_SHP = Path(r"C:\Users\benja\OneDrive\Documents\R\Geocoder\ELD2025.shp")
TC_SHP = Path(r"C:\Users\benja\OneDrive\Documents\R\Geocoder\TOWN_COUNCIL_BDY_2025.shp")

ONEMAP_EMAIL = os.getenv("ONEMAP_EMAIL")
ONEMAP_PASSWORD = os.getenv("ONEMAP_PASSWORD")

if not ONEMAP_EMAIL or not ONEMAP_PASSWORD:
    raise RuntimeError("❌ OneMap credentials not set in environment variables")


# =====================================================
# Address cleaning
# =====================================================
ADDRESS_REPLACEMENTS = {
    "ST.%20GEORGE'S%20RD": "SAINT%20GEORGE'S%20RD",
    "ST.%20GEORGE'S%20LANE": "SAINT%20GEORGE'S%20LANE",
    "926%20HOUGANG%20ST%2091": "926%20HOUGANG%20STREET%2091",
    "11%20HOLLAND%20DR": "11%20HOLLAND%20VISTA",
    "52%20KENT%20RD": "52%20KENT%20RD%20KENT%20VILLE",
    "54%20KENT%20RD": "54%20KENT%20RD%20KENT%20VILLE",
    "2%20BEACH%20RD": "2%20BEACH%20RD%20GARDENS",
    "39%20JLN%20TIGA": "39%20JLN%20TIGA%20PINE%20GREEN",
    "3%20QUEEN'S%20RD": "3%20QUEEN'S%20ROAD%20FARRER%20GARDENS",
    "2%20QUEEN'S%20RD": "2%20QUEEN'S%20ROAD%20FARRER%20GARDENS",
    "6%20JLN%20BATU": "6%20JALAN%20BATU%20DI%20TANJONG%20RHU",
    "602%20CLEMENTI%20WEST%20ST%201": "120602",
    "610%20JURONG%20WEST%20ST%2065": "640610",
    "511%20JURONG%20WEST%20ST%2052": "640511",
    "703%20TAMPINES%20ST%2071": "520703",
    "350%20TAMPINES%20ST%2033": "520350",
    "351%20TAMPINES%20ST%2033": "520351",
    "101%20TAMPINES%20ST%2011": "521101",
    "327%20JURONG%20EAST%20ST%2031": "600327",
    "215%20CHOA%20CHU%20KANG%20CTRL": "680215",
    "216%20CHOA%20CHU%20KANG%20CTRL": "680216",
}

ADDRESS_EXCLUDE = {
    "1A%20WOODLANDS%20CTR%20RD",
    "2A%20WOODLANDS%20CTR%20RD",
}


# =====================================================
# Utilities
# =====================================================
def check_csv_cache(min_size=100):
    def decorator(f):
        @wraps(f)
        def wrapper(dataset_id: str, dst: Path) -> Path:
            if dst.exists() and dst.stat().st_size > min_size:
                print(f"✔ {dst} found locally — skipping download")
                return dst.resolve()
            print(f"⬇ Downloading dataset {dataset_id}")
            return f(dataset_id, dst)
        return wrapper
    return decorator


@check_csv_cache()
def cache_data(dataset_id: str, dst: Path) -> Path:
    session = requests.Session()
    base = "https://api-open.data.gov.sg/v1/public/api/datasets"

    session.get(f"{base}/{dataset_id}/initiate-download", timeout=30).raise_for_status()

    for _ in range(10):
        poll = session.get(f"{base}/{dataset_id}/poll-download", timeout=30)
        poll.raise_for_status()
        data = poll.json()["data"]

        if data.get("url"):
            df = pd.read_csv(data["url"])
            df.to_csv(dst, index=False)
            print(f"✔ CSV saved: {dst} ({len(df):,} rows)")
            return dst.resolve()

        time.sleep(3)

    raise TimeoutError("Dataset download timed out")


# =====================================================
# Step 1–2: Load & Prepare Data
# =====================================================
def clean_address_strings(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["x"] = df["x"].replace(ADDRESS_REPLACEMENTS, regex=True)
    df = df[~df["x"].isin(ADDRESS_EXCLUDE)]
    return df


def prepare_addresses(csv_path: Path):
    df = pd.read_csv(csv_path)

    df["Year"] = df["month"].str[:4].astype(int)
    df["Month"] = df["month"].str[5:7].astype(int)
    df["Lease.Remain"] = df["remaining_lease"].str[:2]
    df["Lease.Remain.Month"] = df["remaining_lease"].str[9:11].replace("", "00")

    df = df.rename(columns={
        "town": "Town",
        "flat_type": "Flat_Type",
        "block": "Block",
        "street_name": "Street",
        "storey_range": "Storey_Range",
        "floor_area_sqm": "Floor_Area_Sqm",
        "flat_model": "Flat_Model",
        "lease_commence_date": "Lease_Commence",
        "resale_price": "Resale_Price",
    })

    df = df[[
        "Year", "Month", "Town", "Flat_Type", "Block", "Street",
        "Storey_Range", "Floor_Area_Sqm", "Flat_Model",
        "Lease_Commence", "Resale_Price",
        "Lease.Remain", "Lease.Remain.Month",
    ]]

    # 1. Construct x
    df["x"] = (
        df["Block"].astype(str) + " " + df["Street"]
    ).str.replace(" ", "%20", regex=False)

    # 2. Apply cleaning to FULL dataframe (this is the missing step)
    df = clean_address_strings(df)

    # 3. Build unique geocoding table from already-cleaned x
    unique = (
        df[["Block", "Street", "x"]]
        .drop_duplicates()
        .reset_index(drop=True)
    )

    unique["POSTALX"] = unique.index + 1

    return df, unique

# =====================================================
# Step 3: OneMap API
# =====================================================
def get_onemap_token():
    res = requests.post(
        "https://www.onemap.gov.sg/api/auth/post/getToken",
        json={"email": ONEMAP_EMAIL, "password": ONEMAP_PASSWORD},
        timeout=15,
    )
    res.raise_for_status()
    return res.json()["access_token"]


def call_geocode(search_val, token, session):
    url = (
        "https://www.onemap.gov.sg/api/common/elastic/search"
        f"?searchVal={search_val}&returnGeom=Y&getAddrDetails=Y&pageNum=1"
    )
    headers = {"Authorization": f"Bearer {token}"}

    try:
        r = session.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        if data.get("results"):
            df = pd.DataFrame(data["results"])
            df["search_input"] = search_val
            return df
    except Exception:
        pass

    return pd.DataFrame({"search_input": [search_val]})


def geocode_addresses(addresses):
    token = get_onemap_token()
    session = requests.Session()
    results = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as ex:
        futures = [ex.submit(call_geocode, a, token, session) for a in addresses]
        for f in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            results.append(f.result())

    return pd.concat(results, ignore_index=True)


# =====================================================
# Step 4: Filter non-residential matches
# =====================================================
exclude_patterns = [
    # commercial / private entities
    r"PTE\.?\s*LTD", r"PRIVATE\s+LIMITED", r"LLP", r"VILLAGE HOTEL",
    r"SEMBCORP MARINE", r"ZERO HOSTEL", r"LIMITED",
    r"CONSERVATION AREA", r"POND", r"AL-NASRY",
    r"DORMITORY", r"RAFFLES HOTEL", r"MKT",
    r"BUS TERMINAL", r"BUS DEPOT", r"INDUSTRIAL ESTATE",

    # educational / childcare
    r"SCHOOL", r"SCHOOLHOUSE", r"KINDERGARTEN", r"PRESCHOOL",
    r"CHILD\s*CARE", r"DEERLAND", r"GLORY CENTRE",
    r"CHILDCARE", r"INFANT", r"NURSERY", r"MONTESSORI",
    r"EDUCATION", r"EDUCATIONAL", r"KINDERCARE",
    r"EDUCARE", r"LEARNING", r"TUITION", r"STUDENT",
    r"KID", r"CHAMPS", r"PRO-TEACH", r"CHILDREN'S PLACE",
    r"STAR\s*KID", r"STARLAND", r"KIDDY", r"THOTH",
    r"MY\s*WORLD", r"SKOOL4KIDZ", r"EDULEARN", r"EDUCENTRE",
    r"PCF", r"FULL MARKS", r"FRIENDS", r"SMARTIE COTTAGE",
    r"HAMPTON PRE-SCHOOL", r"GENIUS SCHOOL HOUSE",
    r"SGM MURNI", r"OOSH", r"MUSTARD SEED",
    r"CHILD", r"BRAIN BOOSTER",

    # community / eldercare / welfare
    r"CLUB", r"COMMUNITY", r"FAMILY", r"ELDERCARE",
    r"AGED HOME", r"CHILD DEVELOPMENT", r"BUSY BEES",
    r"NURTURE CENTRE", r"STAMFORD SCHOLARS", r"BASC",
    r"PRAISE HOLISTIC", r"PRECIOUS ANGELS", r"FSC",
    r"FAMILY SERVICE", r"FAMILY SEVICE", r"MULTI-SERVICE",
    r"ACTIVITY", r"HCA", r"REHABILITATION",
    r"DAY CARE", r"SENIOR", r"THE SALVATION ARMY",
    r"ANANIAS", r"CARING HUT", r"ST LUKE", r"PERTAPIS",
    r"HOME", r"TRANS CENTRE", r"NEW HORIZON",
    r"LITTLE", r"NURTURE CARE", r"GROW & GLOW",
    r"ELDERLY LODGE", r"NKF DIALYSIS", r"MINDS",
    r"DIVINITY ESPECIAL NEEDS INTERVENTION CENTRE",

    # private properties
    r"URBAN EDGE @ HOLLAND V", r"MULTI STOREY CAR PARK",
    r"FARRER SQUARE", r"CHONG PANG 165 HARD COURT",
    r"KAI FOOK MANSION",

    # animal / veterinary / clinic
    r"VETERINARY", r"CLINIC", r"ANIMAL", r"P\.?A\.?W",
    r"THE ANIMAL", r"ANIMAL DOCTORS", r"VET",
    r"VETERINARY SURGERY", r"MONSTER", r"CLNIC",

    # others / institutional
    r"POLICE POST", r"FIRE POST", r"POST OFFICE",
    r"TOWN COUNCIL", r"PCS", r"MY FIRST SKOOL",
    r"HDB PUBLIC SHELTERS", r"MEDICAL INSTITUTION",
]

def filter_unwanted_buildings(df):
    df = df.copy()
    df["rownumbers"] = range(1, len(df) + 1)

    pattern = "|".join(exclude_patterns)

    return df[
        ~df["BUILDING"].str.contains(pattern, flags=re.IGNORECASE, na=False)
    ]


# =====================================================
# Step 5: Spatial enrichment (FIXED)
# =====================================================
def spatial_enrichment(df):
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["LONGITUDE"], df["LATITUDE"]),
        crs="EPSG:4326"
    )

    subzone = gpd.read_file(SUBZONE_SHP)
    eld = gpd.read_file(ELD_SHP)
    tc = gpd.read_file(TC_SHP)

    # Reproject points to match polygon CRS
    gdf = gdf.to_crs(subzone.crs)

    # --- Subzone ---
    gdf = gpd.sjoin(
        gdf,
        subzone,
        how="left",
        predicate="within"
    )
    gdf = gdf.drop(columns=["index_right"], errors="ignore")

    # --- Electoral Division ---
    gdf = gpd.sjoin(
        gdf,
        eld[["ED_DESC", "geometry"]],
        how="left",
        predicate="within"
    )
    gdf = gdf.drop(columns=["index_right"], errors="ignore")

    # --- Town Council ---
    gdf = gpd.sjoin(
        gdf,
        tc[["TOWN_COUNC", "geometry"]],
        how="left",
        predicate="within"
    )
    gdf = gdf.drop(columns=["index_right"], errors="ignore")

    return pd.DataFrame(gdf.drop(columns="geometry"))

# =====================================================
# Main
# =====================================================
def main():
    cache_data(DATASET_ID, RAW_CSV)

    batch_df, unique_df = prepare_addresses(RAW_CSV)

    print("🔎 Geocoding unique addresses")
    geocoded = geocode_addresses(unique_df["x"].tolist())
    geocoded = filter_unwanted_buildings(geocoded)

    print("🗺 Spatial enrichment")
    enriched = spatial_enrichment(geocoded)

    final = batch_df.merge(
        enriched,
        left_on="x",
        right_on="search_input",
        how="left",
    )

    cols_to_drop = [
    "x", "SEARCHVAL", "search_input", "rownumbers",
    "SUBZONE_NO", "SUBZONE_C", "CA_IND", "PLN_AREA_C",
    "REGION_C", "INC_CRC", "FMEL_UPD_D"
    ]

    final = final.drop(columns=cols_to_drop, errors="ignore")

    run_date = datetime.now(UTC).strftime("%Y%m%d")
    out = Path("data/clean") / f"HDB_Resale_Transactions_Merged_{run_date}.csv.gz"
    out.parent.mkdir(parents=True, exist_ok=True)
    final.to_csv(
        out,
        index=False,
        compression="gzip"
    )

    print(f"✅ Completed — output saved to {out}")

if __name__ == "__main__":
    main()