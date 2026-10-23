from qgis.core import QgsProject, QgsRasterLayer

# Define the name of the group layer
group_layer_name = "CORRECTED"

# Get the root layer tree
root = QgsProject.instance().layerTreeRoot()

# Find the group layer
group = root.findGroup(group_layer_name)

if group:
    for child in group.children():
        if hasattr(child, "layer"):  # Check if it's a layer node
            raster_layer = child.layer()
            if isinstance(raster_layer, QgsRasterLayer):  # Ensure it's a raster layer
                provider = raster_layer.dataProvider()
                
                # Set NoData value to 0 for all bands
                for band in range(1, raster_layer.bandCount() + 1):
                    provider.setNoDataValue(band, 0)
                
                raster_layer.triggerRepaint()  # Refresh the layer
                print(f"Updated NoData value for: {raster_layer.name()}")
else:
    print("Group layer not found.")
