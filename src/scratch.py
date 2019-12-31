# 36525, 36528 - Dauphin Island ZCTA

agg = rcp2_6.earliest_encountered_slr[["SLR_ft", "ZCTA", "idx"]].groupby(by=["SLR_ft", "ZCTA"]).count()
agg.reset_index(inplace=True)
x = agg.merge(rcp2_6.census_geo.gdf, on="ZCTA")
x = gpd.GeoDataFrame(x)
x = x.rename(columns={"idx": "home_count"})
x["value"] = x["Zhvi"] * x["home_count"]

# Marginal Building Counts at Risk
fig, axes = plt.subplots(2, 4, sharex=True, sharey=True)
fig.suptitle("Buildings inundated per SLR")
for i in range(7):
	print(i//4, i%4)
	y = x[x["SLR_ft"]==i]
	x.plot(ax=axes[i//4, i%4], color="white", edgecolor='grey', linewidth=0.1)
	y.plot(ax=axes[i//4, i%4], column='home_count', legend=True)
	axes[i//4, i%4].set_title("{} ft SLR".format(str(i)))


plt.show()

# Marginal Value at Risk
fig, axes = plt.subplots(2, 4, sharex=True, sharey=True)
fig.suptitle("Value inundated per SLR (no EMV)")
for i in range(7):
	y = x[x["SLR_ft"]==i]
	x.plot(ax=axes[i//4, i%4], color="white", edgecolor='grey', linewidth=0.1)
	y.plot(ax=axes[i//4, i%4], column='value', legend=True)
	axes[i//4, i%4].set_title("{} ft SLR".format(str(i)))

plt.show()

ax = rcp2_6.marginal_value_at_risk.plot(title="Marginal Value and EMV at Risk, RCP2.6")
ax.set_xlabel("SLR scenarios")
ax.set_ylabel("$")
plt.show()

ax = rcp4_5.marginal_value_at_risk.plot(title="Marginal Value and EMV at Risk, RCP4.5")
ax.set_xlabel("SLR scenarios")
ax.set_ylabel("$")
plt.show()

ax = rcp8_5.marginal_value_at_risk.plot(title="Marginal Value and EMV at Risk, RCP8.5")
ax.set_xlabel("SLR scenarios")
ax.set_ylabel("$")
plt.show()

agg = rcp4_5.earliest_encountered_slr[rcp4_5.earliest_encountered_slr["ZCTA"] == 36528][["SLR_ft", "idx"]].groupby(by="SLR_ft")
x = agg.count()
y = x.cumsum()
x["Total buildings exposed"] = y
x = x.rename(columns={"idx": "Marginal buildings exposed"})
ax = x.plot(title="Dauphin Island: Building Base Heights")
ax.set_xlabel("Ft Above Sea Level")
ax.set_ylabel("Buildings at Risk")
plt.show()


agg = rcp4_5.earliest_encountered_slr[["ZCTA", "idx"]].groupby(by="ZCTA")
x = agg.count()
x = x.rename(columns={"idx": "Exposure by Zip Code"})
x = x.sort_values(by="Exposure by Zip Code", ascending=False)
ax = x.plot.bar(title="Exposure by Zip Code", rot=0)
ax.set_xlabel("Zip Code")
ax.set_ylabel("Buildings at Risk")
plt.show()


x = gpd.sjoin(gpd.GeoDataFrame(rcp4_5.earliest_encountered_slr), alabama_census_tract_sovi.gdf, how="left", op="intersects")
y = x[["ZCTA", "RPL_THEME1"]].drop_duplicates()
y["SoVI_Rank"] = y["RPL_THEME1"].rank()

dauphin_island = gpd.GeoDataFrame(rcp4_5.earliest_encountered_slr[rcp4_5.earliest_encountered_slr["ZCTA"] == 36528])
mapping_2050 = {
	0: 1,
	1: 1,
	2: 1,
	3: 1,
	4: .99,
	5: .82,
	6: .6
}

def func(row):
    return mapping_2050[row["SLR_ft"]]

dauphin_island["Likelihood"] = dauphin_island.apply(func, axis=1)
dauphin_island["EMV"] = dauphin_island["Likelihood"] * dauphin_island["Zhvi"]
dauphin_island["EMV"].sum()

ax = a.plot(column="UWHomes_TotalValue_AllTiers", legend=True)
ax.set_title("Total Home Value within 6 ft of Sea Level")
plt.show()

