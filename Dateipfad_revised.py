import os
import re
from qgis.core import QgsProject
from PyQt5.QtCore import QDateTime
from time import time

base_directory = "W:/"
start_time = time()

# Configuration
ignored_folders = {
    "_#_#31TRS_2015", "_Scans Luftis", "_Vorbereitung Digitalisierung", "Casey_Jones",
    "LGL BW digitale Bilder", "Nicht lokalisierbar, unbekannt", "Original Images to be moved on external hard drive",
    "Thüringen Bilder (nicht eingepflegt)", "Bibliothek (Basecamp) (V) - Verknüpfung (2)",
    "Bibliothek (Basecamp) (V) - Verknüpfung"
}

# Supported image extensions (case insensitive)
IMAGE_EXTENSIONS = {'.tif', '.tiff', '.ecw'}

# Cache folder structure upfront
print("Building folder cache...")
folder_cache = {}
for root, dirs, files in os.walk(base_directory):
    dirs[:] = [d for d in dirs if d not in ignored_folders]
    # Only cache image files with supported extensions
    image_files = [f for f in files if os.path.splitext(f)[1].lower() in IMAGE_EXTENSIONS]
    folder_cache[root] = {'subdirs': dirs.copy(), 'files': image_files.copy()}
print(f"Folder cache built in {time()-start_time:.2f} seconds")

layer = iface.activeLayer()

def find_matching_folders(target_date, target_sortie):
    """Find folders matching date and sortie pattern using cached structure"""
    date_pattern = target_date.replace('_', '[_-]')
    sortie_pattern = target_sortie.replace('_', '[_-]')
    pattern = re.compile(fr'^{date_pattern}#.*#{sortie_pattern}$', re.IGNORECASE)
    
    return [folder for folder in folder_cache if pattern.match(os.path.basename(folder))]

def construct_image_pattern(bildnummer, sortie, datum):
    """Create efficient pattern matching for image files (supports multiple extensions)"""
    # Match the base filename pattern with any supported extension
    return re.compile(
        fr'.*{bildnummer}.*{sortie}.*{datum}\.(?:tif|tiff|ecw)$', 
        re.IGNORECASE
    )

def find_image_in_cached_folders(folders, pattern):
    """Search for image in cached folder structure"""
    for folder in folders:
        # Check files in main folder
        for f in folder_cache[folder]['files']:
            if pattern.match(f):
                return os.path.join(folder, f)
        
        # Check subfolders
        for subdir in folder_cache[folder]['subdirs']:
            subpath = os.path.join(folder, subdir)
            if subpath in folder_cache:
                for f in folder_cache[subpath]['files']:
                    if pattern.match(f):
                        return os.path.join(subpath, f)
    return None

# Precompile patterns for better performance
date_pattern = re.compile(r'^\d{4}_\d{2}_\d{2}')
sortie_clean_pattern = re.compile(r'[^a-zA-Z0-9_-]')

layer.startEditing()
processed = 0
found = 0

for feature in layer.getFeatures():
    processed += 1
    
    # Date handling
    datum_object = feature['Datum']
    if not datum_object or datum_object.isNull():
        continue
    
    datum_for_folder = datum_object.toString("yyyy_MM_dd")
    datum_for_image = datum_object.toString("dd_MM_yyyy")

    # Sortie cleaning
    sortie_value = feature['Sortie_ori']
    if not sortie_value or sortie_value == 'NULL':
        sortie = "_"
    else:
        sortie = sortie_clean_pattern.sub('_', str(sortie_value).upper())

    # Bildnummer handling
    bildnummer_value = feature['Bildnummer']
    if bildnummer_value in ['NULL', 'NAN', None]:
        bildnummer = "_"
    else:
        bildnummer = str(int(bildnummer_value)).zfill(4)

    # Find matching folders
    matched_folders = find_matching_folders(datum_for_folder, sortie)
    if not matched_folders:
        continue

    # Create image pattern (now includes ECW)
    image_pattern = construct_image_pattern(bildnummer, sortie, datum_for_image)
    
    # Search for image
    matched_image = find_image_in_cached_folders(matched_folders, image_pattern)
    if matched_image:
        feature['Dateipfad'] = 'file:///' + matched_image.replace('\\', '/')
        layer.updateFeature(feature)
        found += 1

if layer.isEditable():
    layer.commitChanges()

print(f"Processed {processed} features in {time()-start_time:.2f} seconds")
print(f"Found matches for {found} features ({found/processed*100:.1f}% success rate)")