import csv
import json

def convert_csv_to_runtime_json(csv_filepath, json_filepath):
    # Initialize the base structure shown in 17.1 Recommended Runtime JSON Shape
    runtime_data = {
        "metadata": {
            "crop_count": 0,
            "location_focus": "Rajshahi pilot, Bangladesh"
        },
        "crops": {}
    }

    try:
        with open(csv_filepath, mode='r', encoding='utf-8') as csv_file:
            # Assumes your CSV headers exactly match the dictionary keys below 
            reader = csv.DictReader(csv_file)
            
            crop_count = 0
            for row in reader:
                crop_id = row.get("crop_id")
                if not crop_id:
                    continue 
                    
                crop_count += 1
                
                # Map flat CSV rows into the nested JSON architecture
                runtime_data["crops"][crop_id] = {
                    "identity": {
                        "crop_id": crop_id,
                        "family": row.get("family", "")
                    },
                    "planting_window": {
                        "preferred_start_mmdd": row.get("preferred_start_mmdd", ""),
                        "preferred_end_mmdd": row.get("preferred_end_mmdd", ""),
                        "supported_late_end_mmdd": row.get("supported_late_end_mmdd", ""),
                        # Convert string to boolean to preserve real JSON types
                        "crosses_year": str(row.get("crosses_year", "")).strip().lower() in ["true", "1", "yes"]
                    },
                    "duration": {
                        "variety": {
                            "min_days": int(row.get("min_days", 0) or 0),
                            "max_days": int(row.get("max_days", 0) or 0)
                        }
                    },
                    "environment": {
                        "temperature": {
                            "tolerance_min_c": float(row.get("tolerance_min_c", 0) or 0),
                            "tolerance_max_c": float(row.get("tolerance_max_c", 0) or 0)
                        },
                        "soil": {
                            "ph_optimal_min": float(row.get("ph_optimal_min", 0) or 0),
                            "ph_optimal_max": float(row.get("ph_optimal_max", 0) or 0)
                        }
                    },
                    "water": {
                        "fao_crop_water_need_min_mm": float(row.get("fao_crop_water_need_min_mm", 0) or 0),
                        "fao_crop_water_need_max_mm": float(row.get("fao_crop_water_need_max_mm", 0) or 0)
                    },
                    "decision_support": {
                        "overall_data_confidence": row.get("overall_data_confidence", "UNKNOWN")
                    }
                }
                
            # Update metadata dynamically based on parsed rows
            runtime_data["metadata"]["crop_count"] = crop_count

        # Write to JSON file with indentation for readability
        with open(json_filepath, mode='w', encoding='utf-8') as json_file:
            json.dump(runtime_data, json_file, indent=2)
            
        print(f"Successfully converted {crop_count} crops from {csv_filepath} to {json_filepath}")
        
    except FileNotFoundError:
        print(f"Error: Could not find {csv_filepath}. Please ensure the file exists.")
    except Exception as e:
        print(f"Error during conversion: {e}")

# Execute the pipeline
if __name__ == "__main__":
    csv_file = r"Q:\CycleAlgo\Data\fosol_cycle_rajshahi_crop_dataset.csv"
    json_file = r"Q:\CycleAlgo\Data\fosol_cycle_rajshahi_crop_dataset.json"
    
    convert_csv_to_runtime_json(csv_file, json_file)