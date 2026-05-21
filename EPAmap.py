import requests
import pandas as pd 
import matplotlib.pyplot as plt # plotting map
import geopandas as gpd
from shapely.geometry import Point

print("script started")

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
print("saved california_aqs_monitors.csv")


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

#plot
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

print("saved california_aqs_monitor_map.png")

import matplotlib.cm as cm
import numpy as np

msa = gpd.read_file("cbsa_2024.gdb")
msa = msa.to_crs("EPSG:4326")

# only true msa 
msa = msa[msa["LSAD"] == "M1"].copy()

#combin counties into MSAs 
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
plt.savefig("california_msa_colored_labeled.png", dpi=300)
plt.show()

print("saved california_msa_colored_labeled.png")