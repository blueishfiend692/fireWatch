import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import gaussian_kde
from shapely.geometry import Polygon

california_data = gpd.read_file("./testData/CA_Counties_TIGER2016.geojson")
wildfire_data = gpd.read_file("./testData/California_Fire_Perimeters_(all).geojson")

wildfire_data = wildfire_data.to_crs(california_data.crs)

print("starting gaussian kernel density estimation ...")

wildfire_data['centroid'] = wildfire_data.geometry.centroid
wildfire_coords = np.column_stack((wildfire_data['centroid'].x, wildfire_data['centroid'].y))
kde = gaussian_kde(wildfire_coords.T)

print("checking fishnet")

bbox = california_data.total_bounds
cell_size = 5000
rows = int((bbox[3] - bbox[1]) / cell_size)
cols = int((bbox[2] - bbox[0]) / cell_size)

grid_polygons = []
for x in range(cols):
    for y in range(rows):
        xmin = bbox[0] + x * cell_size
        xmax = bbox[0] + (x + 1) * cell_size
        ymin = bbox[1] + y * cell_size
        ymax = bbox[1] + (y + 1) * cell_size

        clipped_polygon = Polygon([(max(xmin, bbox[0]), max(ymin, bbox[1])),
                                   (min(xmax, bbox[2]), max(ymin, bbox[1])),
                                   (min(xmax, bbox[2]), min(ymax, bbox[3])),
                                   (max(xmin, bbox[0]), min(ymax, bbox[3]))])
        interscting_california = california_data[california_data.intersects(clipped_polygon)]
        if not interscting_california.empty:
            grid_polygons.append(clipped_polygon)

fishnet = gpd.GeoDataFrame({'geometry': grid_polygons}, crs=california_data.crs)

print("getting fishnet colors ...")
fishnet_colors = []
for cell_polygon in grid_polygons:
    centroid_x, centroid_y = cell_polygon.centroid.x, cell_polygon.centroid.y
    density_value = kde([centroid_x, centroid_y])[0]
    fishnet_colors.append(density_value)

cmap = plt.get_cmap('inferno')
norm = plt.Normalize(vmin=np.min(fishnet_colors), vmax=np.max(fishnet_colors))

fishnet['color'] = fishnet_colors

print("plotting")

fig, ax = plt.subplots(figsize=(10, 10))
california_data.plot(ax=ax, color='lightgrey', edgecolor='black', linewidth=1.5, alpha=1, zorder=1)
fishnet.boundary.plot(ax=ax, facecolor=cmap(norm(fishnet['color'])), edgecolor='black', linewidth=0.5)

ax.set_title("Kernel Density Estimation Heatmap of Wildfires in California with Fishnet")
plt.show()
