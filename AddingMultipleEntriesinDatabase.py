import os
from qgis.core import QgsVectorLayerUtils
from qgis.utils import iface

# ---- SETTINGS ----
folder_path = r"W:\1945_01_14#00634#US34_3297\Neuer Ordner"
sortie_value = "US34_3297"
# ------------------

layer = iface.activeLayer()

if not layer:
    raise Exception("No active layer selected")

if not layer.isEditable():
    layer.startEditing()

# Get all files in directory
files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

added = 0

for filename in files:

    # Remove file extension if present
    name_without_ext = os.path.splitext(filename)[0]

    # Split by '#'
    parts = name_without_ext.split("#")

    if len(parts) < 1:
        continue

    image_number = parts[0]   # First element (e.g. 2187)

    # Create feature respecting Postgres defaults
    feature = QgsVectorLayerUtils.createFeature(layer)

    # Set required attributes
    feature["sortie_ori"] = sortie_value
    feature["Bildnummer"] = image_number

    layer.addFeature(feature)
    added += 1

layer.commitChanges()

print(f"{added} rows inserted successfully.")