# Get the active layer
layer = iface.activeLayer()

# Check if a layer is selected
if not layer:
    print("No active layer selected!")
else:
    # Check if the layer has the 'Bildnummer' field
    field_name = 'Bildnummer'
    fields = layer.fields()
    field_names = [field.name() for field in fields]
    
    if field_name not in field_names:
        print(f"Field '{field_name}' not found in the active layer!")
        print(f"Available fields: {field_names}")
    else:
        # Get all Bildnummer values
        bildnummer_values = []
        for feature in layer.getFeatures():
            value = feature[field_name]
            if value is not None and value != '':
                # Convert to integer if possible
                try:
                    bildnummer_values.append(int(value))
                except (ValueError, TypeError):
                    bildnummer_values.append(value)
        
        # If we have numeric values, find missing numbers in sequence
        if all(isinstance(x, int) for x in bildnummer_values) and bildnummer_values:
            min_num = min(bildnummer_values)
            max_num = max(bildnummer_values)
            existing_numbers = set(bildnummer_values)
            
            # Find all missing numbers
            missing_numbers = [num for num in range(min_num, max_num + 1) if num not in existing_numbers]
            
            # Convert missing numbers to range format
            def find_ranges(numbers):
                if not numbers:
                    return []
                
                ranges = []
                start = numbers[0]
                end = numbers[0]
                
                for num in numbers[1:]:
                    if num == end + 1:
                        end = num
                    else:
                        if start == end:
                            ranges.append(str(start))
                        else:
                            ranges.append(f"{start}-{end}")
                        start = num
                        end = num
                
                # Add the last range
                if start == end:
                    ranges.append(str(start))
                else:
                    ranges.append(f"{start}-{end}")
                
                return ranges
            
            missing_ranges = find_ranges(missing_numbers)
            
            # Print results
            print(f"Bildnummer range: {min_num} to {max_num}")
            print(f"Total records: {len(bildnummer_values)}")
            print(f"Missing numbers: {len(missing_numbers)}")
            print(f"Missing ranges: {', '.join(missing_ranges)}")
            
        else:
            print("Bildnummer values are not all numeric or no values found.")
            if bildnummer_values:
                print("Sample values:", sorted(set(bildnummer_values))[:10])