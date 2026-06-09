import requests
import pandas as pd 
import matplotlib.pyplot as plt # plotting map
import geopandas as gpd
import zipfile, io
from shapely.geometry import Point
import matplotlib.cm as cm
import numpy as np


#section 1

#API key
EMAIL = "naina.ghiware@gmail.com"
API_KEY = "indigowolf76"

url = (
    f"https://aqs.epa.gov/data/api/monitors/byState?"
    f"email={EMAIL}&key={API_KEY}"
    f"&param=88101" #pm2.5 pollutant
    f"&bdate=20150101" #jan 1, 2015
    f"&edate=20251231" #dec 31,2025
    f"&state=06" #california state code
)
response = requests.get(url, timeout=10)
print("status code:", response.status_code) 

data = response.json()

df = pd.DataFrame(data["Data"])
print(df.head())
print("rows:", len(df))

df.to_csv("california_aqs_monitors.csv", index=False)

#section 2

#clean data
#convert lat and long into numeric
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

#convert to datetime
df["open_date"] = pd.to_datetime(df["open_date"], errors="coerce")
df["close_date"] = pd.to_datetime(df["close_date"], errors="coerce")

df_map = df[
    (df["open_date"] <= "2025-12-31") &
    ((df["close_date"].isna()) | (df["close_date"] >= "2015-01-01"))
]

df_map = df_map.dropna(subset=["latitude", "longitude"])

#section 3

#plot
#real outline of california from online GeoJSON
ca_url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
ca_geojson = requests.get(ca_url).json()

#find california in the file
california = None
for feature in ca_geojson["features"]:
    if feature["properties"]["name"] == "California":
        california = feature
        break

plt.figure(figsize=(8, 10))

#california outline (handle both Polygon and MultiPolygon)
coords = california["geometry"]["coordinates"]

if california["geometry"]["type"] == "Polygon":
    for ring in coords:
        ca_lon = [point[0] for point in ring]
        ca_lat = [point[1] for point in ring]
        plt.plot(ca_lon, ca_lat, color="black", linewidth=1)

elif california["geometry"]["type"] == "MultiPolygon":
    for polygon in coords:
        for ring in polygon:
            ca_lon = [point[0] for point in ring]
            ca_lat = [point[1] for point in ring]
            plt.plot(ca_lon, ca_lat, color="black", linewidth=1)

#plotting monitoring stations
plt.scatter(df_map["longitude"], df_map["latitude"], s=20, alpha=0.75)

plt.title("EPA AQS PM2.5 Monitors in California, 2015–2025")
plt.xlabel("Longitude")
plt.ylabel("Latitude")

plt.xlim(-125, -113.5)
plt.ylim(32, 42.5)

plt.tight_layout()
plt.savefig("california_aqs_monitor_map.png", dpi=300)
plt.show()

#section 4

#load msa
msa = gpd.read_file("cbsa_2024.gdb")
msa = msa.to_crs("EPSG:4326")

# only true msa 

#combine counties into MSAs 
msa_dissolved = msa.dissolve(by="CBSAFP").reset_index()

#only california
ca_bbox_url = "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json"
ca_geojson2 = requests.get(ca_bbox_url).json()
ca_feature2 = next(f for f in ca_geojson2["features"] if f["properties"]["name"] == "California")
gdf_ca = gpd.GeoDataFrame.from_features([ca_feature2], crs="EPSG:4326")

msa_ca = msa_dissolved[msa_dissolved.intersects(gdf_ca.union_all())].copy()
msa_ca = msa_ca.reset_index(drop=True)

# dif msa color
n = len(msa_ca)
colors = cm.get_cmap("tab20", n)(np.linspace(0, 1, n))

fig, ax = plt.subplots(figsize=(10, 12))
gdf_ca.plot(ax=ax, facecolor="#f5f5f0", edgecolor="black", linewidth=1.2, zorder=1)
for i, (_, row) in enumerate(msa_ca.iterrows()):
    gpd.GeoDataFrame([row], geometry="geometry", crs="EPSG:4326").plot(
        ax=ax,
        facecolor=(*colors[i][:3], 0.45),   # color with alpha
        edgecolor="black",
        linewidth=0.8,
        zorder=2
    )
#labelling
for _, row in msa_ca.iterrows():
    centroid = row.geometry.centroid
    if -125 <= centroid.x <= -113.5 and 32 <= centroid.y <= 42.5:
        short_name = row["NAME"].split(",")[0].strip()
        ax.text(
            centroid.x, centroid.y,
            short_name,
            fontsize=6.5,
            ha="center", va="center",
            fontweight="bold",
            color="black",
            zorder=4,
            bbox=dict(facecolor="white", alpha=0.55, edgecolor="none", pad=1.2)
        )

ax.set_title("California Metropolitan Statistical Areas (MSAs)", fontsize=14, fontweight="bold")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_xlim(-125, -113.5)
ax.set_ylim(32, 42.5)
ax.set_aspect("equal")
plt.tight_layout()
plt.savefig("california_msa_map.png", dpi=300)
plt.show()

#section 5

#create geodataframe from df_map
gdf_stations = gpd.GeoDataFrame(
    df_map.copy(),
    geometry=[Point(lon, lat) for lon, lat in zip(df_map["longitude"], df_map["latitude"])],
    crs="EPSG:4326"
)

# spatial join( each station gets msa_id + msa_name if it falls inside an MSA)
# msa_ca already exists from your code above
gdf_joined = gpd.sjoin(
    gdf_stations,
    msa_ca[["CBSAFP", "NAME", "geometry"]],
    how="left",
    predicate="within"
)
gdf_joined = gdf_joined.rename(columns={"CBSAFP": "msa_id", "NAME": "msa_name"})
gdf_joined.to_csv("california_stations_with_msa.csv", index=False)
fig, ax = plt.subplots(figsize=(10, 12))

#ca
gdf_ca.plot(ax=ax, facecolor="#f5f5f0", edgecolor="black", linewidth=1.2, zorder=1)

#msa
msa_ca.plot(ax=ax, facecolor="none", edgecolor="#888888", linewidth=0.8, zorder=2)

# stations: blue = inside MSA, red = outside
inside  = gdf_joined[gdf_joined["msa_id"].notna()]
outside = gdf_joined[gdf_joined["msa_id"].isna()]

inside.plot(ax=ax,  color="steelblue", markersize=18, alpha=0.8, zorder=3, label=f"Inside MSA ({len(inside)})")
outside.plot(ax=ax, color="red",       markersize=18, alpha=0.8, zorder=3, label=f"Outside MSA ({len(outside)})")

ax.set_title("EPA PM2.5 Stations — Inside vs. Outside California MSAs", fontsize=13, fontweight="bold")
ax.set_xlabel("Longitude")
ax.set_ylabel("Latitude")
ax.set_xlim(-125, -113.5)
ax.set_ylim(32, 42.5)
ax.set_aspect("equal")
ax.legend(fontsize=10)
plt.tight_layout()
plt.savefig("california_stations_msa_join.png", dpi=300)
plt.show()
print("Saved california_stations_msa_join.png")

#section 6

ej_path = "/Users/nainaghiware/Downloads/2024/2.32_August_UseMe/EJScreen_2024_Tract_with_AS_CNMI_GU_VI.csv"

ej_df = pd.read_csv(ej_path, dtype=str, low_memory=False)

# filter ca
ej_ca = ej_df[ej_df["ST_ABBREV"] == "CA"].copy()
print(f"California census tracts: {len(ej_ca)}")

ej_ca = ej_ca[[
    "ID",           # census tract GEOID
    "CNTY_NAME",    # county name
    "ACSTOTPOP",    # total population
    "PEOPCOLORPCT", # % people of color
    "LOWINCPCT",    # % low income
    "UNEMPPCT",     # % unemployed
    "LESSHSPCT",    # % less than high school education
    "LINGISOPCT",   # % linguistically isolated
    "PM25",         # PM2.5 exposure level
]].copy()

#socioeconomic to numeric
for col in ["PEOPCOLORPCT", "LOWINCPCT", "UNEMPPCT", "LESSHSPCT", "LINGISOPCT", "PM25"]:
    ej_ca[col] = pd.to_numeric(ej_ca[col], errors="coerce")

print(ej_ca.head())

#section 7

#shapefile
tiger_url = "https://www2.census.gov/geo/tiger/TIGER2024/TRACT/tl_2024_06_tract.zip"
r = requests.get(tiger_url, verify=False)  # verify=False bypasses SSL issue on Mac
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall("ca_tracts_2024")

tracts = gpd.read_file("ca_tracts_2024/tl_2024_06_tract.shp")
tracts = tracts.to_crs("EPSG:4326")
print(f"Census tracts loaded: {len(tracts)}")
print(tracts[["GEOID", "NAME"]].head())

#section 8

#station to census tract join
gdf_stations2 = gdf_joined[gdf_joined["msa_id"].notna()].copy()
gdf_stations2 = gdf_stations2.drop(columns=["index_right"], errors="ignore")
gdf_stations2 = gdf_stations2.reset_index(drop=True)

gdf_with_tracts = gpd.sjoin(
    gdf_stations2,
    tracts[["GEOID", "geometry"]],
    how="left",
    predicate="within"
)
gdf_with_tracts = gdf_with_tracts.rename(columns={"GEOID": "tract_geoid"})

#section 9

#merge ej screen attributes
gdf_final = gdf_with_tracts.merge(
    ej_ca.rename(columns={"ID": "tract_geoid"}),
    on="tract_geoid",
    how="left"
)
gdf_final.to_csv("california_stations_final.csv", index=False)

#section 10

#cleaned csv with only relevant columns
cleaned = gdf_final[[
    'site_number',     
    'local_site_name',  
    'PM25',            
    'msa_id',          
    'msa_name',      
    'tract_geoid',      
    'CNTY_NAME',      
    'PEOPCOLORPCT',     
    'LOWINCPCT',       
    'UNEMPPCT',       
]].copy()

#rename to match 
cleaned = cleaned.rename(columns={
    'site_number':    'station_id',
    'local_site_name':'station_name',
    'tract_geoid':    'census_id',
    'CNTY_NAME':      'census_tract',
    'PEOPCOLORPCT':   'pct_people_of_color',
    'LOWINCPCT':      'pct_low_income',
    'UNEMPPCT':       'pct_unemployed',
})

cleaned.to_csv("california_stations_cleaned.csv", index=False)

#section 11

#purple air
#load purpleAir sensor data
pa_df = pd.read_csv("california_Purple_Air_sensors.csv")

#clear missing data
pa_df = pa_df = pa_df.dropna(subset=["latitude", "longitude", "pm2.5"])

#convert to geodataframe (lat/long coordinates)
gdf_pa = gpd.GeoDataFrame(
    pa_df.copy(),
    geometry=[Point(lon, lat) for lon, lat in zip(pa_df["longitude"], pa_df["latitude"])],
    crs="EPSG:4326"
)

#section 12

#spatial join: purple air sensors to MSAs
gdf_pa_to_msas = gpd.sjoin(
    gdf_pa,
    msa_ca[["CBSAFP", "NAME", "geometry"]],
    how="left",
    predicate="within"
)
gdf_pa_to_msas = gdf_pa_to_msas.rename(columns={"CBSAFP": "msa_id", "NAME": "msa_name"})

#section 13
#spation join: purple air sensors to census tracts
gdf_pa2 = gdf_pa_to_msas[gdf_pa_to_msas["msa_id"].notna()].copy()
gdf_pa2 = gdf_pa2.drop(columns=["index_right"], errors="ignore")
gdf_pa2 = gdf_pa2.reset_index(drop=True)
gdf_pa_tracts = gpd.sjoin(
    gdf_pa2,
    tracts[["GEOID", "geometry"]],
    how="left",
    predicate="within"
)
gdf_pa_tracts = gdf_pa_tracts.rename(columns={"GEOID": "tract_geoid"})

#section 14

#merge with EJ screen attributes
gdf_pa_final = gdf_pa_tracts.merge(
    ej_ca.rename(columns={"ID": "tract_geoid"}),
    on="tract_geoid",
    how="left"
)
gdf_pa_final.to_csv("california_purple_air_final.csv", index=False)

#section 15

#clean columns
pa_cleaned = gdf_pa_final[[
    'sensor_index',  
    'name',         
    'pm2.5',       
    'msa_id',
    'msa_name',    
    'tract_geoid',   
    'CNTY_NAME',    
    'PEOPCOLORPCT', 
    'LOWINCPCT',     
    'UNEMPPCT',      
]].copy()
#rename 
pa_cleaned = pa_cleaned.rename(columns={
    'sensor_index': 'station_id',
    'name':         'station_name',
    'pm2.5':        'PM25',
    'tract_geoid':  'census_id',
    'CNTY_NAME':    'census_tract',
    'PEOPCOLORPCT': 'pct_people_of_color',
    'LOWINCPCT':    'pct_low_income',
    'UNEMPPCT':     'pct_unemployed',
})
#cleaned 
pa_cleaned.to_csv("purpleair_stations_cleaned.csv", index=False)