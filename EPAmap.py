import requests
import pandas as pd 
import matplotlib.pyplot as plt # plotting map

print("script started")

#API key
EMAIL = "naina.ghiware@gmail.com"
API_KEY = "API KEY HERE"

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