# Get the active layer
layer = iface.activeLayer()

if not layer:
    print("No active layer selected")
else:
    # Ask user where to save the file
    from qgis.core import QgsProject
    import os
    from datetime import datetime
    
    # Create output filename
    output_file = os.path.join(os.path.expanduser("~"), "Desktop", f"geometry_check_{layer.name()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Geometry Check Report for Layer: {layer.name()}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total features: {layer.featureCount()}\n")
        f.write("=" * 100 + "\n")
        
        # Check if the required fields exist
        fields = layer.fields()
        field_names = [field.name() for field in fields]
        
        has_id = 'ID' in field_names
        has_sortie = 'sortie_ori' in field_names
        has_bild = 'Bildnummer' in field_names
        
        f.write(f"Fields found: ID={has_id}, sortie_ori={has_sortie}, Bildnummer={has_bild}\n")
        f.write("=" * 100 + "\n")
        f.write(f"{'FID':<6} {'ID':<10} {'sortie_ori':<15} {'Bildnummer':<15} {'Geometry Status':<20} {'Details':<30}\n")
        f.write("-" * 100 + "\n")
        
        # Statistics
        stats = {'total': 0, 'valid': 0, 'null': 0, 'empty': 0, 'invalid': 0, 'zero_area': 0}
        problem_features = []
        
        # Check all features
        for feature in layer.getFeatures():
            stats['total'] += 1
            fid = feature.id()
            
            # Get attribute values
            id_val = feature['ID'] if has_id else 'N/A'
            sortie_val = feature['sortie_ori'] if has_sortie else 'N/A'
            bild_val = feature['Bildnummer'] if has_bild else 'N/A'
            
            # Check geometry
            geom = feature.geometry()
            
            if geom is None:
                status = "NO GEOMETRY"
                details = "None"
                stats['null'] += 1
                problem_features.append((fid, id_val, sortie_val, bild_val, "No geometry"))
            elif geom.isEmpty():
                status = "EMPTY"
                details = "Empty geometry"
                stats['empty'] += 1
                problem_features.append((fid, id_val, sortie_val, bild_val, "Empty geometry"))
            elif not geom.isGeosValid():
                status = "INVALID"
                details = f"Invalid: {geom.lastError() if hasattr(geom, 'lastError') else 'Validation failed'}"
                stats['invalid'] += 1
                problem_features.append((fid, id_val, sortie_val, bild_val, "Invalid geometry"))
            elif geom.area() == 0 and geom.length() == 0 and geom.type() != 0:
                status = "ZERO AREA"
                details = f"Type: {geom.type()}, Area/Length: 0"
                stats['zero_area'] += 1
                problem_features.append((fid, id_val, sortie_val, bild_val, "Zero area/length"))
            else:
                status = "VALID"
                details = f"Type: {geom.type()}, Area: {geom.area():.2f}, Length: {geom.length():.2f}"
                stats['valid'] += 1
            
            f.write(f"{fid:<6} {str(id_val)[:10]:<10} {str(sortie_val)[:15]:<15} {str(bild_val)[:15]:<15} {status:<20} {details[:30]:<30}\n")
        
        # Write summary
        f.write("\n" + "=" * 100 + "\n")
        f.write("SUMMARY STATISTICS:\n")
        f.write("=" * 50 + "\n")
        f.write(f"Total features checked: {stats['total']}\n")
        f.write(f"Valid geometry: {stats['valid']}\n")
        f.write(f"Null geometry: {stats['null']}\n")
        f.write(f"Empty geometry: {stats['empty']}\n")
        f.write(f"Invalid geometry: {stats['invalid']}\n")
        f.write(f"Zero area/length (non-point): {stats['zero_area']}\n")
        
        valid_total = stats['valid']
        problem_total = stats['total'] - valid_total
        
        f.write(f"\nFeatures with issues: {problem_total}\n")
        if problem_total > 0:
            f.write(f"Percentage with issues: {(problem_total/stats['total'])*100:.2f}%\n")
    
    print(f"\n✅ Report saved to: {output_file}")
    
    # Also show quick summary in console
    print(f"\nQuick Summary for {layer.name()}:")
    print(f"Total: {stats['total']}, Valid: {stats['valid']}, Issues: {stats['total'] - stats['valid']}")
    if stats['total'] - stats['valid'] > 0:
        print(f"Check the detailed report at: {output_file}")