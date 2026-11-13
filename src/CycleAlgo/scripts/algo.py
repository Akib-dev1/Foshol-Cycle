import json
from datetime import date, timedelta

dfile_path = r"Q:\CycleAlgo\Data\fosol_cycle_rajshahi_crop_dataset.json"
ifile_path = r"Q:\CycleAlgo\Data\input.json"
cfile_path = r"Q:\CycleAlgo\Data\rajshahi_nasa_project_ready.json"


with open(dfile_path,"r",encoding="utf-8") as file:
    crops = json.load(file)

with open(ifile_path, 'r', encoding='utf-8') as file:
    input = json.load(file)  

with open(cfile_path, "r", encoding="utf-8") as file:
    climate = json.load(file)


#3 Timeline and Window Guard Engine

def is_valid_iso_date(date_string):
    # Check if the string is empty or None first
    if not date_string:
        return False
        
    try:
        # Attempts to parse strictly ISO 8601 format (YYYY-MM-DD)
        date.fromisoformat(date_string)
        return True
    except ValueError:
        # Returns False if the format is wrong or the date doesn't exist (e.g., Feb 30)
        return False

def validateInput(input,crops):
    if "location" not in input or "current_crop" not in input or "field" not in input:
        print("Missing require core information")
        return False
    currentCrop = input["current_crop"]
    if currentCrop.get("crop_id") not in crops["crops"]:
        print("Invalid current crop ID")
        return False
    if not is_valid_iso_date(currentCrop.get("planting_date")):
        print("Invalid planting date format.")
        return False
    harvestDate=currentCrop.get("actual_harvest_date")
    if harvestDate is not None and not is_valid_iso_date(harvestDate):
        return False;
    
    nextCropBlock = input.get("next_crop") or {}
    nextCropid=nextCropBlock.get("crop_id")
    
    if nextCropid is not None:
        if nextCropid not in crops.get("crops"):
            print("Invalid next Crop ID")
            return False
        
    field = input.get("field")
    validIrrigation=["none","limited","adequate"]
    
    if field.get("irrigation","").lower() not in validIrrigation:
        print("Invalid Irrigation")
        return False
    soilPh=field.get("soil_ph")
    if soilPh is not None and not isinstance(soilPh, (int,float)):
        return False
    
    priorities = input.get("priorities") or {}
    for key, value in priorities.items():
        if value is not None:
            if not isinstance(value, int) or not (1 <= value <= 5):
                print(f"Priority {key} must be an integer between 1 and 5.")
                return False
            
    return True

def add_days(date_string, dayss):
    d =date.fromisoformat(date_string)
    new_d = d + timedelta(days=dayss)
    return new_d.isoformat()

def calculate_harvest_range(input, crops):
    current_crop = input["current_crop"]
    crop_id = current_crop["crop_id"]          # Grabs "aman_br11"
    crop_profile = crops["crops"][crop_id]     # Looks up crops["crops"]["aman_br11"]
    if current_crop.get("actual_harvest_date") is not None:
        actualDate= current_crop["actual_harvest_date"]
        return {
            "earliest": actualDate,
            "latest": actualDate
        }
    plantingDate = current_crop.get("planting_date")
    min_days = crop_profile["duration"]["variety"]["min_days"]
    max_days = crop_profile["duration"]["variety"]["max_days"]
    return{
        "earliest": add_days(plantingDate,min_days),
        "latest": add_days(plantingDate,max_days)
    }


def calculate_field_ready_range(harvest_range,turnaround_days):
    return{
        "earliest":add_days(harvest_range.get("earliest"),turnaround_days),
        "latest": add_days(harvest_range.get("latest"),turnaround_days)
    }
    ##some work needs to be done here as this has some risks
    

def adder(mmdd,year,crosses_year,is_end):
    if mmdd is None:
        return None
    if crosses_year is True and is_end is True:
        year = year+1
    return f"{year}-{mmdd}"
def build_planting_window(candidate_crop_profile, season_start_year):
    w = candidate_crop_profile["planting_window"]
    crosses = w.get("crosses_year", False)
    
    return {
        "preferredStart": adder(w.get("preferred_start_mmdd"), season_start_year, crosses, False),
        "preferredEnd": adder(w.get("preferred_end_mmdd"), season_start_year, crosses, True),
        "lateEnd": adder(w.get("supported_late_end_mmdd"), season_start_year, crosses, True)
    }

def evaluate_window(field_ready_range, window):
    ready= field_ready_range["latest"]
    if ready <= window["preferredEnd"]:
        if ready<window["preferredStart"]:
            plant_date = window["preferredStart"]
        else:
            plant_date = ready
        return{
            "status":"SAFE",
            "possiblePlantingDate": plant_date
        }
    elif window["lateEnd"] is not None and ready <= window["lateEnd"] :
        return{
            "status":"COMPRESSED",
            "possiblePlantingDate": ready
        }
    else:
        return{
            "status":"OUTSIDE_SUPPORTED_WINDOW",
            "possiblePlantingDate":ready
        }
        
#4 Biophysical Checks

def evaluate_soil_ph(soil_ph,candidate_crop_profile):
    opt_min = candidate_crop_profile["environment"]["soil"]["ph_optimal_min"]
    opt_max=candidate_crop_profile["environment"]["soil"]["ph_optimal_max"]
    tol_min=candidate_crop_profile["environment"]["soil"]["ph_tolerance_min"]
    tol_max=candidate_crop_profile["environment"]["soil"]["ph_tolerance_max"]
    
    if soil_ph is None:
        return{
            "status":"UNKNOWN",
            "score":None
        }
    if opt_min <= soil_ph <= opt_max:
        return{
            "status":"OPTIMAL",
            "score":100
        }
    elif tol_min <= soil_ph <= tol_max:
        return{
            "status":"TOLERATED",
            "score":60
        }
    else:
        return{
            "status": "OUTSIDE_TOLERANCE",
            "score": 0
        }

def water_demand_class(candidate_crop_profile):
    cropwater=candidate_crop_profile["water"]
    min_mm=cropwater.get("fao_crop_water_need_min_mm")
    max_mm=cropwater.get("fao_crop_water_need_max_mm")
    
    if min_mm is None and max_mm is None:
        return "UNKNOWN"
    max_val = max_mm or 0
    
    if max_val >=700: #Note: if max_mm happens to be None, default it to 0 using max_val = max_mm or 0 before comparing!
        return "HIGH"
    
    elif max_val >= 550 :
        return "MEDIUM"
    
    else:
        return "LOW"
def evaluate_water(candidate_crop_profile,irrigation_level):
    demand = water_demand_class(candidate_crop_profile)
    if demand=="UNKNOWN":
        return {
            "status":"UNKNOWN",
            "score": None
        }
    if irrigation_level =="adequate" or irrigation_level =="high" :
        return {
            "status":"PASS",
            "score": 100
        }
    elif irrigation_level == "limited" or irrigation_level == "medium":
        if demand == "HIGH":
            return{
                "status": "CAUTION",
                "score": 60
            }
        else:
            return{
                "status" : "PASS",
                "score": 85
            }
    else:
        if demand=="HIGH":
            return {
                "status": "POOR_MATCH",
                "score" : 25
            }
        elif demand == "MEDIUM":
            return{
                "status":"CAUTION",
                "score" : 55
            }
        else:
            return {
                "status" : "PASS",
                "score" : 85
            }

def evaluate_rotation(current_crop_profile,candidate_crop_profile):
    score = 50
    curr_id = current_crop_profile["identity"]["crop_id"]
    cand_id = candidate_crop_profile["identity"]["crop_id"]
    
    curr_fam = current_crop_profile["identity"]["family"]
    cand_fam = candidate_crop_profile["identity"]["family"]
    
    if curr_id == cand_id :
        score = score - 35
    elif curr_fam == cand_fam :
        score -= 20
    else: 
        score +=20
    
    soil_effect = candidate_crop_profile.get("rotation",{}).get("soil_effect",{})
    if soil_effect.get("fixes_nitrogen") is True:
        score += 25
    
    score = max(0,min(100,score))
    
    if score >= 70 :
        status = "GOOD_ROTATION"
    elif score >=45:
        status = "NEUTRAL_ROTATION"
    else:
        status = "POOR_ROTATION"
    
    return {
        "status": status,
        "score" : score
    }