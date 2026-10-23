# Import necessary modules
from qgis.core import QgsProject, QgsProcessing, QgsMapLayer, QgsRasterLayer, QgsVectorLayer
from qgis.PyQt.QtWidgets import QInputDialog, QMessageBox, QFileDialog
from qgis import processing

def clip_rasters_with_partial_name_matching():
    """
    Clip raster layers from a specified group based on partial name matching 
    with polygon layers in a specified vector layer.
    The output clipped raster will have the name: InputRasterName_Clipped
    """
    
    # Get the current project instance
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    
    # Get available groups in the project
    groups = []
    def get_groups(group_node):
        for child in group_node.children():
            if isinstance(child, QgsLayerTreeGroup):
                groups.append(child.name())
                get_groups(child)  # Recursively get subgroups
    
    get_groups(root)
    
    if not groups:
        QMessageBox.warning(None, "No Groups Found", "No groups found in the project!")
        return
    
    # Ask user for the raster group name using QInputDialog
    raster_group_name, ok = QInputDialog.getItem(
        None, 
        "Select Raster Group", 
        "Select the group containing raster layers:", 
        groups, 
        0, 
        False
    )
    
    if not ok or not raster_group_name:
        print("Operation cancelled by user")
        return
    
    # Get available vector layers
    vector_layers = []
    for layer_id, layer in project.mapLayers().items():
        if isinstance(layer, QgsVectorLayer) and layer.geometryType() == QgsWkbTypes.PolygonGeometry:
            vector_layers.append(layer.name())
    
    if not vector_layers:
        QMessageBox.warning(None, "No Polygon Layers", "No polygon vector layers found in the project!")
        return
    
    # Ask user for the vector layer name
    vector_layer_name, ok = QInputDialog.getItem(
        None,
        "Select Vector Layer",
        "Select the vector layer containing polygon data:",
        vector_layers,
        0,
        False
    )
    
    if not ok or not vector_layer_name:
        print("Operation cancelled by user")
        return
    
    # Find the raster group
    raster_group = root.findGroup(raster_group_name)
    
    if not raster_group:
        QMessageBox.warning(None, "Group Not Found", f"Group '{raster_group_name}' not found!")
        return
    
    # Find the vector layer
    vector_layer = None
    for layer_id, layer in project.mapLayers().items():
        if layer.name() == vector_layer_name and isinstance(layer, QgsVectorLayer):
            vector_layer = layer
            break
    
    if not vector_layer:
        QMessageBox.warning(None, "Layer Not Found", f"Vector layer '{vector_layer_name}' not found!")
        return
    
    print(f"Found raster group: {raster_group_name}")
    print(f"Found vector layer: {vector_layer_name}")
    
    # Get all raster layers from the specified group
    raster_layers = {}
    
    def get_layers_from_group(group_node):
        """Recursively get all raster layers from a group"""
        layers = {}
        for child in group_node.children():
            if isinstance(child, QgsLayerTreeLayer):
                layer = child.layer()
                if layer and layer.type() == QgsMapLayer.RasterLayer:
                    layers[layer.name()] = layer
            elif isinstance(child, QgsLayerTreeGroup):
                # Recursively get layers from subgroups
                layers.update(get_layers_from_group(child))
        return layers
    
    raster_layers = get_layers_from_group(raster_group)
    
    if not raster_layers:
        QMessageBox.warning(None, "No Raster Layers", f"No raster layers found in group '{raster_group_name}'!")
        return
    
    print(f"Found {len(raster_layers)} raster layer(s) in group '{raster_group_name}':")
    for raster_name in raster_layers.keys():
        print(f"  - {raster_name}")
    
    # Get polygon layer name from vector layer attributes
    fields = vector_layer.fields()
    field_names = [field.name() for field in fields]
    
    if not field_names:
        QMessageBox.warning(None, "No Fields", f"No fields found in vector layer '{vector_layer_name}'!")
        return
    
    # Ask user which field contains the polygon layer names
    field_name, ok = QInputDialog.getItem(
        None,
        "Select Field",
        f"Select the field that contains polygon layer names in '{vector_layer_name}':",
        field_names,
        0,
        False
    )
    
    if not ok or not field_name:
        print("Operation cancelled by user")
        return
    
    print(f"Selected field: {field_name}")
    
    # Get unique polygon layer names from the vector layer
    polygon_names = set()
    for feature in vector_layer.getFeatures():
        polygon_name = feature[field_name]
        if polygon_name:
            polygon_names.add(str(polygon_name))
    
    print(f"\nFound {len(polygon_names)} unique polygon names in '{vector_layer_name}':")
    for polygon_name in sorted(polygon_names):
        print(f"  - {polygon_name}")
    
    # Function to find best match between raster name and polygon name
    def find_best_match(raster_name, polygon_names):
        """
        Find the best matching polygon name for a given raster name.
        This function checks for partial matches and substring matches.
        """
        raster_lower = raster_name.lower()
        
        # First, check for exact substring matches
        for polygon_name in polygon_names:
            polygon_lower = polygon_name.lower()
            
            # Check if polygon name is a substring of raster name
            if polygon_lower in raster_lower:
                return polygon_name
            
            # Check if raster name is a substring of polygon name
            if raster_lower in polygon_lower:
                return polygon_name
        
        # If no substring match, check for partial matches
        # Split by common delimiters and compare parts
        delimiters = ['_', '-', ' ', '.', ',']
        
        # Try to split raster name
        raster_parts = []
        temp_name = raster_name
        for delimiter in delimiters:
            if delimiter in temp_name:
                parts = [p for p in temp_name.split(delimiter) if p]
                raster_parts.extend(parts)
        
        if not raster_parts:
            raster_parts = [raster_name]
        
        # Check each part against polygon names
        for part in raster_parts:
            part_lower = part.lower()
            for polygon_name in polygon_names:
                polygon_lower = polygon_name.lower()
                if part_lower in polygon_lower or polygon_lower in part_lower:
                    return polygon_name
        
        return None
    
    # Find matches between raster layers and polygon names
    matches = {}
    unmatched_rasters = []
    
    for raster_name in raster_layers.keys():
        matched_polygon = find_best_match(raster_name, polygon_names)
        if matched_polygon:
            matches[raster_name] = matched_polygon
        else:
            unmatched_rasters.append(raster_name)
    
    print(f"\nMatched {len(matches)} raster layer(s):")
    for raster_name, polygon_name in matches.items():
        print(f"  - {raster_name} -> {polygon_name}")
    
    if unmatched_rasters:
        print(f"\n{len(unmatched_rasters)} raster layer(s) could not be matched:")
        for raster_name in unmatched_rasters:
            print(f"  - {raster_name}")
        
        # Ask user if they want to proceed with unmatched layers
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Proceed with Unmatched Layers?")
        msg_box.setText(f"{len(unmatched_rasters)} raster layer(s) could not be matched.\n\nProceed with clipping only matched layers?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.Yes)
        
        if msg_box.exec_() != QMessageBox.Yes:
            print("Operation cancelled.")
            return
    
    # Ask for output directory using QFileDialog
    output_dir = QFileDialog.getExistingDirectory(
        None,
        "Select Output Directory for Clipped Rasters",
        "",
        QFileDialog.ShowDirsOnly
    )
    
    if not output_dir:
        print("Operation cancelled by user")
        return
    
    # Create parameters for clip processing
    clipped_count = 0
    failed_clips = []
    
    for raster_name, polygon_name in matches.items():
        raster_layer = raster_layers[raster_name]
        
        # Filter vector layer to get only features with this polygon name
        expression = f'"{field_name}" = \'{polygon_name}\''
        vector_layer.selectByExpression(expression)
        
        if vector_layer.selectedFeatureCount() == 0:
            print(f"Warning: No features found for polygon name '{polygon_name}'")
            failed_clips.append((raster_name, f"No features found for '{polygon_name}'"))
            continue
        
        # Create a temporary layer with only the selected feature
        temp_layer = processing.run("native:saveselectedfeatures", {
            'INPUT': vector_layer,
            'OUTPUT': 'memory:'
        })['OUTPUT']
        
        # Prepare output name and path
        output_name = f"{raster_name}_Clipped"
        output_path = f"{output_dir}/{output_name}.tif"
        
        print(f"\nClipping: {raster_name}")
        print(f"Using polygon: {polygon_name}")
        print(f"Output: {output_name}")
        
        try:
            # Define parameters for clip raster by mask layer
            params = {
                'INPUT': raster_layer,
                'MASK': temp_layer,
                'SOURCE_CRS': None,
                'TARGET_CRS': None,
                'TARGET_EXTENT': None,
                'NODATA': None,
                'ALPHA_BAND': False,
                'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': True,
                'OPTIONS': '',
                'DATA_TYPE': 0,
                'OUTPUT': output_path
            }
            
            # Execute the clip raster by mask layer algorithm
            result = processing.run("gdal:cliprasterbymasklayer", params)
            
            if result['OUTPUT']:
                # Add the clipped raster to the project
                clipped_raster = QgsRasterLayer(result['OUTPUT'], output_name)
                
                if clipped_raster.isValid():
                    project.addMapLayer(clipped_raster)
                    print(f"✓ Successfully clipped '{raster_name}'")
                    clipped_count += 1
                else:
                    print(f"✗ Failed to load clipped raster for '{raster_name}'")
                    failed_clips.append((raster_name, "Failed to load clipped raster"))
            else:
                print(f"✗ Failed to clip '{raster_name}'")
                failed_clips.append((raster_name, "Processing failed"))
                
        except Exception as e:
            print(f"✗ Error clipping '{raster_name}': {str(e)}")
            failed_clips.append((raster_name, str(e)))
    
    # Show summary message
    summary_msg = f"Clipping completed!\n\nSuccessfully clipped: {clipped_count} of {len(matches)} matched raster layer(s)"
    
    if failed_clips:
        summary_msg += f"\n\nFailed to clip {len(failed_clips)} layer(s):"
        for raster_name, error in failed_clips:
            summary_msg += f"\n  • {raster_name}: {error}"
    
    if clipped_count > 0:
        summary_msg += f"\n\nClipped rasters have been added to the project with suffix '_Clipped'"
        summary_msg += f"\nOutput directory: {output_dir}"
    
    QMessageBox.information(None, "Clipping Complete", summary_msg)
    
    print(f"\n{'='*50}")
    print(f"Clipping completed!")
    print(f"Successfully clipped: {clipped_count} of {len(matches)} matched raster layer(s)")

# Alternative: Simplified version with hardcoded parameters for quick testing
def clip_rasters_simple():
    """
    Simplified version with hardcoded parameters for testing
    """
    # Set your parameters here
    RASTER_GROUP = "IMAGES"
    VECTOR_LAYER = "VectorLayerToClip"
    NAME_FIELD = "layer_name"  # Change to your field name
    OUTPUT_DIR = "C:/RasterOutput/"  # Change to your output directory
    
    project = QgsProject.instance()
    root = project.layerTreeRoot()
    
    # Find the raster group
    raster_group = root.findGroup(RASTER_GROUP)
    if not raster_group:
        print(f"Error: Group '{RASTER_GROUP}' not found!")
        return
    
    # Find the vector layer
    vector_layer = None
    for layer_id, layer in project.mapLayers().items():
        if layer.name() == VECTOR_LAYER and isinstance(layer, QgsVectorLayer):
            vector_layer = layer
            break
    
    if not vector_layer:
        print(f"Error: Vector layer '{VECTOR_LAYER}' not found!")
        return
    
    # Get all raster layers from the group
    raster_layers = {}
    for child in raster_group.children():
        if isinstance(child, QgsLayerTreeLayer):
            layer = child.layer()
            if layer and layer.type() == QgsMapLayer.RasterLayer:
                raster_layers[layer.name()] = layer
    
    if not raster_layers:
        print(f"No raster layers found in group '{RASTER_GROUP}'!")
        return
    
    # Get polygon names from vector layer
    polygon_names = set()
    for feature in vector_layer.getFeatures():
        polygon_name = feature[NAME_FIELD]
        if polygon_name:
            polygon_names.add(str(polygon_name))
    
    # Simple matching: check if polygon name is substring of raster name
    for raster_name, raster_layer in raster_layers.items():
        matched_polygon = None
        raster_lower = raster_name.lower()
        
        for polygon_name in polygon_names:
            polygon_lower = polygon_name.lower()
            if polygon_lower in raster_lower:
                matched_polygon = polygon_name
                break
        
        if matched_polygon:
            # Filter and clip
            expression = f'"{NAME_FIELD}" = \'{matched_polygon}\''
            vector_layer.selectByExpression(expression)
            
            if vector_layer.selectedFeatureCount() > 0:
                temp_layer = processing.run("native:saveselectedfeatures", {
                    'INPUT': vector_layer,
                    'OUTPUT': 'memory:'
                })['OUTPUT']
                
                output_name = f"{raster_name}_Clipped"
                output_path = f"{OUTPUT_DIR}/{output_name}.tif"
                
                try:
                    result = processing.run("gdal:cliprasterbymasklayer", {
                        'INPUT': raster_layer,
                        'MASK': temp_layer,
                        'CROP_TO_CUTLINE': True,
                        'OUTPUT': output_path
                    })
                    
                    if result['OUTPUT']:
                        clipped_raster = QgsRasterLayer(result['OUTPUT'], output_name)
                        if clipped_raster.isValid():
                            project.addMapLayer(clipped_raster)
                            print(f"✓ Clipped: {raster_name}")
                except Exception as e:
                    print(f"✗ Error: {raster_name} - {str(e)}")

# Run the function
print("Starting raster clipping tool...")
print("Select option:")
print("1. Interactive mode (with dialogs)")
print("2. Simple mode (hardcoded parameters)")

# In QGIS Python Console, you can't use input(), so we'll default to interactive mode
clip_rasters_with_partial_name_matching()