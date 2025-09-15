#!/usr/bin/env python3
"""
🏘️ OPTIMIZED MULTI-PROPERTY-TYPE CLEANER 🏘️
Extracts optimal fields for each property type:
- Type 1: Residential Apartments (filter out projects)
- Type 2: Independent Houses/Villas  
- Type 3: Residential Land/Plots
- Type 5: Farm Houses
Each type gets its most relevant fields!
"""

import json
import pandas as pd
import os
import re
from datetime import datetime

class OptimizedMultiTypePropertyCleaner:
    def __init__(self):
        # 🎯 FEATURES & AMENITIES MAPPING (same for all types)
        self.FEATURES_MAPPING = {
            1: "Swimming Pool", 2: "Power Back-up", 3: "Separate entry for servant room",
            4: "CCTV Surveillance", 5: "Feng Shui / Vaastu Compliant", 6: "Park",
            8: "Private Garden / Terrace", 9: "Security Personnel", 10: "Centrally Air Conditioned",
            12: "Fitness Centre / GYM", 13: "Children's Play Area", 17: "Club house / Community Center",
            19: "Visitor Parking", 20: "Intercom Facility", 21: "Lift(s)", 23: "Maintenance Staff",
            24: "Multipurpose Community Hall", 25: "Piped-gas", 26: "Rain Water Harvesting",
            28: "Water Storage", 29: "Waste Disposal", 30: "Internet/wi-fi connectivity",
            31: "Water softening plant", 32: "Water purifier", 33: "Shopping Centre",
            36: "Access Control System", 38: "Senior Citizen Area", 39: "Recently Renovated",
            40: "Natural Light", 41: "Airy Rooms", 42: "Spacious Interiors", 43: "Low Density Society",
            44: "Security / Fire Alarm", 45: "High Ceiling Height", 46: "Water Storage", 47: "No open drainage around"
        }
        
        self.AMENITIES_MAPPING = {
            1: "Swimming Pool", 2: "Gymnasium", 3: "Security", 4: "Power Backup", 5: "Parking",
            6: "CCTV Surveillance", 7: "Elevator", 8: "Garden", 9: "Children's Play Area", 10: "Club House",
            11: "24x7 Security", 12: "Maintenance Staff", 13: "Visitor Parking", 14: "Intercom",
            15: "Fire Safety", 16: "Earthquake Resistant", 17: "Multipurpose Hall", 18: "ATM",
            19: "Shopping Center", 20: "Wi-Fi", 21: "Internet", 22: "Cafeteria", 23: "Library",
            24: "Jogging Track", 25: "Tennis Court", 26: "Badminton Court", 27: "Basketball Court",
            28: "Cricket Pitch", 29: "Football Ground", 30: "Volleyball Court", 31: "Skating Rink",
            32: "Yoga/Meditation Area", 33: "Spa", 34: "Salon", 35: "Medical Center", 36: "Pharmacy",
            37: "Bank", 38: "Post Office", 39: "Community Hall", 40: "Conference Room", 41: "Business Center",
            42: "Banquet Hall", 43: "Party Hall", 44: "Barbecue", 45: "Amphitheater", 46: "Mini Theater",
            47: "Indoor Games", 48: "Card Room", 49: "Billiards", 50: "Table Tennis",
            101: "Refrigerator", 102: "Washing Machine", 103: "Dishwasher"
        }
        
        self.FACING_MAPPING = {
            0: "North", 1: "South", 2: "East", 3: "West", 4: "North-West", 5: "North-East", 
            6: "South-West", 7: "South-East", 8: "North-East-West", 9: "North-South-East",
            10: "North-South-West", 11: "South-East-West", 12: "All Sides"
        }

        self.OVERLOOKING_MAPPING = {
            1: "Park/Garden", 2: "Main Road", 3: "Club House", 4: "Pool", 5: "Others",
            6: "Lake", 7: "Hills", 8: "City View", 9: "Sea View", 10: "Garden View", 11: "Pool View", 12: "Club View"
        }
        
        self.FURNISH_MAPPING = {
            0: "Unfurnished", 1: "Semi-Furnished", 2: "Fully Furnished", 3: "Furnished"
        }

    def decode_field_codes(self, field_value, mapping_dict):
        """Decode comma-separated field codes"""
        if not field_value or field_value in ['', 'None', None]:
            return []
        try:
            codes = [int(x.strip()) for x in str(field_value).split(',') if x.strip().isdigit()]
            return [mapping_dict[code] for code in codes if code in mapping_dict]
        except:
            return []

    def safe_get(self, obj, path, default=""):
        """Safely get nested values"""
        try:
            keys = path.split('.')
            result = obj
            for key in keys:
                if isinstance(result, dict) and key in result:
                    result = result[key]
                else:
                    return default
            return result if result is not None else default
        except:
            return default

    def convert_sqft_to_sqm(self, area_sqft):
        """Convert square feet to square meters"""
        try:
            # 1 sq ft = 0.092903 sq m
            sqft_value = float(area_sqft)
            sqm_value = sqft_value * 0.092903
            return round(sqm_value, 2)
        except:
            return area_sqft

    def extract_area_value(self, area_str):
        """Extract numeric area value from string"""
        if not area_str:
            return None
        try:
            # Remove any non-numeric characters except decimal point
            import re
            numeric_part = re.findall(r'\d+\.?\d*', str(area_str))
            if numeric_part:
                return float(numeric_part[0])
        except:
            pass
        return None

    def get_comprehensive_area_info(self, prop):
        """Get comprehensive area information with type and value in square meters"""
        area_info = {
            'area_value': "Not Specified",
            'area_type': "Not Specified",
            'area_sqm': "Not Specified"
        }
        
        # Priority order: Super Built-up > Built-up > Carpet Area
        
        # Check for Super Built-up Area
        if prop.get('SUPERBUILTUP_AREA') or prop.get('SUPERBUILTUP_SQFT'):
            area_value = prop.get('SUPERBUILTUP_AREA') or prop.get('SUPERBUILTUP_SQFT')
            if area_value and str(area_value).strip() and str(area_value) != '0':
                area_info['area_type'] = "Super Built-up Area"
                area_info['area_value'] = str(area_value)
                # Convert to square meters
                numeric_value = self.extract_area_value(area_value)
                if numeric_value:
                    area_info['area_sqm'] = self.convert_sqft_to_sqm(numeric_value)
                return area_info
        
        # Check for Built-up Area
        if prop.get('BUILDUP_AREA') or prop.get('BUILDUP_SQFT'):
            area_value = prop.get('BUILDUP_AREA') or prop.get('BUILDUP_SQFT')
            if area_value and str(area_value).strip() and str(area_value) != '0':
                area_info['area_type'] = "Built-up Area"
                area_info['area_value'] = str(area_value)
                numeric_value = self.extract_area_value(area_value)
                if numeric_value:
                    area_info['area_sqm'] = self.convert_sqft_to_sqm(numeric_value)
                return area_info
        
        # Check for Carpet Area
        if prop.get('CARPET_AREA') or prop.get('CARPET_SQFT'):
            area_value = prop.get('CARPET_AREA') or prop.get('CARPET_SQFT')
            if area_value and str(area_value).strip() and str(area_value) != '0':
                area_info['area_type'] = "Carpet Area"
                area_info['area_value'] = str(area_value)
                numeric_value = self.extract_area_value(area_value)
                if numeric_value:
                    area_info['area_sqm'] = self.convert_sqft_to_sqm(numeric_value)
                return area_info
        
        # Check generic AREA field as fallback
        if prop.get('AREA'):
            area_value = prop.get('AREA')
            if area_value and str(area_value).strip() and str(area_value) != '0':
                area_text = str(area_value).lower()
                if 'carpet' in area_text:
                    area_info['area_type'] = "Carpet Area"
                elif 'super' in area_text or 'built' in area_text:
                    area_info['area_type'] = "Super Built-up Area"
                else:
                    area_info['area_type'] = "Area"
                
                area_info['area_value'] = str(area_value)
                numeric_value = self.extract_area_value(area_value)
                if numeric_value:
                    area_info['area_sqm'] = self.convert_sqft_to_sqm(numeric_value)
                return area_info
        
        return area_info

    def get_flexible_area(self, prop):
        """Get area value - kept for backward compatibility"""
        area_info = self.get_comprehensive_area_info(prop)
        return area_info['area_value']

    def get_flexible_area_type(self, prop):
        """Get area type - kept for backward compatibility"""
        area_info = self.get_comprehensive_area_info(prop)
        return area_info['area_type']

    def get_flexible_area_sqm(self, prop):
        """Get area in square meters"""
        area_info = self.get_comprehensive_area_info(prop)
        return area_info['area_sqm']

    def get_all_area_types_sqm(self, prop):
        """Get all available area types in square meters for separate columns"""
        area_data = {
            'superbuiltup_area': "",
            'builtup_area': "",
            'carpet_area': ""
        }
        
        # Check for Super Built-up Area
        if prop.get('SUPERBUILTUP_AREA') or prop.get('SUPERBUILTUP_SQFT'):
            area_value = prop.get('SUPERBUILTUP_AREA') or prop.get('SUPERBUILTUP_SQFT')
            if area_value and str(area_value).strip() and str(area_value) != '0':
                numeric_value = self.extract_area_value(area_value)
                if numeric_value:
                    area_data['superbuiltup_area'] = self.convert_sqft_to_sqm(numeric_value)
        
        # Check for Built-up Area (also try alternative field names)
        buildup_sources = [
            prop.get('BUILDUP_AREA'), 
            prop.get('BUILDUP_SQFT'), 
            prop.get('BUILT_UP_AREA'), 
            prop.get('BUILTUP_AREA')
        ]
        for area_value in buildup_sources:
            if area_value and str(area_value).strip() and str(area_value) != '0':
                numeric_value = self.extract_area_value(area_value)
                if numeric_value:
                    area_data['builtup_area'] = self.convert_sqft_to_sqm(numeric_value)
                    break
        
        # Check for Carpet Area
        if prop.get('CARPET_AREA') or prop.get('CARPET_SQFT'):
            area_value = prop.get('CARPET_AREA') or prop.get('CARPET_SQFT')
            if area_value and str(area_value).strip() and str(area_value) != '0':
                numeric_value = self.extract_area_value(area_value)
                if numeric_value:
                    area_data['carpet_area'] = self.convert_sqft_to_sqm(numeric_value)
        
        # Check generic AREA field and try to categorize it
        if prop.get('AREA') and not any(area_data.values()):
            area_value = prop.get('AREA')
            if area_value and str(area_value).strip() and str(area_value) != '0':
                area_text = str(area_value).lower()
                numeric_value = self.extract_area_value(area_value)
                if numeric_value:
                    area_sqm = self.convert_sqft_to_sqm(numeric_value)
                    if 'carpet' in area_text:
                        area_data['carpet_area'] = area_sqm
                    elif 'super' in area_text or 'superbuilt' in area_text:
                        area_data['superbuiltup_area'] = area_sqm
                    elif 'built' in area_text:
                        area_data['builtup_area'] = area_sqm
                    # If it's generic 'area' and no specific type found, skip it as per user request
        
        return area_data

    def clean_landmarks_display(self, landmarks_list):
        """Clean landmarks to show just the count and type"""
        if not landmarks_list or landmarks_list == ["No landmarks data"]:
            return "No landmarks data"
        
        cleaned = []
        for landmark in landmarks_list:
            # Extract just the meaningful part
            if '(' in landmark and ')' in landmark:
                # Extract count and type: "2 Metro Stations (MetroStation)" -> "2 Metro Stations"
                parts = landmark.split('(')
                if len(parts) >= 2:
                    clean_part = parts[0].strip()
                    cleaned.append(clean_part)
                else:
                    cleaned.append(landmark)
            else:
                cleaned.append(landmark)
        
        return ", ".join(cleaned)

    def get_common_fields(self, prop):
        """Extract common fields for all property types"""
        return {
            'Property_ID': prop.get('PROP_ID', ''),
            'Property_Type': self.safe_get(prop, 'FORMATTED.PROP_TYPE_LABEL', prop.get('PROPERTY_TYPE', '')),
            'City': prop.get('CITY', ''),
            'Locality': prop.get('localityLabel', ''),
            'Price': prop.get('FORMATTED_PRICE', ''),
            'Price_Sqft': prop.get('PRICE_SQFT', ''),
            'Features': self.decode_field_codes(prop.get('FEATURES', ''), self.FEATURES_MAPPING),
            'Amenities': self.decode_field_codes(prop.get('AMENITIES', ''), self.AMENITIES_MAPPING),
            'Facing': self.FACING_MAPPING.get(prop.get('FACING', ''), 'Not Specified'),
            'Overlooking': self.decode_field_codes(prop.get('OVERLOOKING', ''), self.OVERLOOKING_MAPPING),
            'Landmarks': self.get_landmarks(prop),
            'Latitude': self.safe_get(prop, 'MAP_DETAILS.LATITUDE', ''),
            'Longitude': self.safe_get(prop, 'MAP_DETAILS.LONGITUDE', ''),
            'Description': prop.get('DESCRIPTION', '').replace('\n', ' ').replace('\r', ''),
            'Property_URL': f"https://www.99acres.com{prop.get('PD_URL', '')}" if prop.get('PD_URL') else '',
            'Register_Date': prop.get('REGISTER_DATE__U', ''),
            'Expiry_Date': prop.get('EXPIRY_DATE', ''),
            'Age': prop.get('AGE', ''),
            'Gated_Community': 'Yes' if prop.get('GATED') == 'Y' else 'No'
        }

    def get_landmarks(self, prop):
        """Extract landmarks"""
        landmarks = []
        formatted_landmarks = prop.get('FORMATTED_LANDMARK_DETAILS', [])
        if formatted_landmarks:
            for landmark in formatted_landmarks:
                text = landmark.get('text', '')
                category = landmark.get('category', '')
                if text:
                    landmarks.append(f"{text} ({category})" if category else text)
        return landmarks if landmarks else ["No landmarks data"]

    def extract_type1_apartment_data(self, prop):
        """Extract data for Type 1: Residential Apartments (excluding projects)"""
        # Filter out projects
        if (prop.get('entityType') == 'PROJECT' or 
            prop.get('projectUnitId') or 
            prop.get('configSummary')):
            return None
            
        # Must be apartment/flat
        property_type = prop.get('PROPERTY_TYPE', '').lower()
        if 'apartment' not in property_type and 'flat' not in property_type:
            return None
        
        data = self.get_common_fields(prop)
        
        # Remove Property_Name and add flexible area handling
        data.pop('Property_Name', None)
        
        # Apartment-specific fields with separate area type columns
        area_types = self.get_all_area_types_sqm(prop)
        data.update({
            'SuperBuiltup_Area': area_types['superbuiltup_area'],
            'Builtup_Area': area_types['builtup_area'],
            'Carpet_Area': area_types['carpet_area'],
            'BHK_Config': f"{prop.get('BEDROOM_NUM', '')} BHK" if prop.get('BEDROOM_NUM') else '',
            'Bedrooms': prop.get('BEDROOM_NUM', ''),
            'Bathrooms': prop.get('BATHROOM_NUM', ''),
            'Balconies': prop.get('BALCONY_NUM', ''),
            'Floor_Number': prop.get('FLOOR_NUM', ''),
            'Total_Floors': prop.get('TOTAL_FLOOR', ''),
            'Furnish': self.get_furnish_status(prop),
            'Parking_Spaces': self.get_parking_info(prop),
            'Building_Name': prop.get('BUILDING_NAME', ''),
            'Society_Name': prop.get('SOCIETY_NAME', ''),
            'Possession_Status': 'Ready to Move' if 'READY TO MOVE' in str(prop.get('tags', [])) else 'Under Construction'
        })
        
        # Add image information
        image_data = self.get_property_images(prop)
        # Remove API_Photo_Count for apartments as it's always zero
        image_data.pop('API_Photo_Count', None)
        data.update(image_data)
        
        # Clean landmarks
        data['Landmarks'] = self.clean_landmarks_display(data['Landmarks'])
        
        return data

    def extract_type2_house_data(self, prop):
        """Extract data for Type 2: Independent Houses ONLY (no villas)"""
        # Filter to only Independent Houses
        property_type = prop.get('PROPERTY_TYPE', '').lower()
        if 'independent house' not in property_type:
            return None
        
        data = self.get_common_fields(prop)
        
        # Remove Property_Name 
        data.pop('Property_Name', None)
        
        # House-specific fields with comprehensive area info
        data.update({
            'Plot_Area': self.get_flexible_area(prop),
            'Plot_Area_Type': self.get_flexible_area_type(prop),
            'Plot_Area_SqM': self.get_flexible_area_sqm(prop),
            'Bedrooms': prop.get('BEDROOM_NUM', ''),
            'Bathrooms': prop.get('BATHROOM_NUM', ''),
            'Balconies': prop.get('BALCONY_NUM', ''),
            'Total_Floors': prop.get('TOTAL_FLOOR', ''),
            'Furnish': self.get_furnish_status(prop),
            'Parking_Spaces': self.get_parking_info(prop),
            'Corner_Property': 'Yes' if prop.get('CORNER_PROPERTY') == 'Y' else 'No',
            'Private_Garden': 'Yes' if any('garden' in str(feature).lower() for feature in self.decode_field_codes(prop.get('FEATURES', ''), self.FEATURES_MAPPING)) else 'No',
            'House_Type': 'Independent House'
        })
        
        # Add image information
        image_data = self.get_property_images(prop)
        data.update(image_data)
        
        # Clean landmarks
        data['Landmarks'] = self.clean_landmarks_display(data['Landmarks'])
        
        return data

    def extract_type3_land_data(self, prop):
        """Extract data for Type 3: Residential Land/Plots"""
        data = self.get_common_fields(prop)
        
        # Remove Property_Name
        data.pop('Property_Name', None)
        # Remove Age (always 0)
        data.pop('Age', None)
        
        # Land-specific fields with comprehensive area info
        data.update({
            'Plot_Area': self.get_flexible_area(prop),
            'Plot_Area_Type': self.get_flexible_area_type(prop),
            'Plot_Area_SqM': self.get_flexible_area_sqm(prop),
            'Ownership_Type': prop.get('VALUE_LABEL', ''),
            'Max_Construction_Floors': prop.get('TOTAL_FLOOR', ''),
            'Parking_Provision': self.get_parking_info(prop),
            'Corner_Plot': 'Yes' if prop.get('CORNER_PROPERTY') == 'Y' else 'No',
            'Plot_Type': 'Residential Land',
            'Construction_Allowed': 'Yes' if prop.get('TOTAL_FLOOR', 0) != '0' else 'Not Specified'
        })
        
        # Add image information
        image_data = self.get_property_images(prop)
        data.update(image_data)
        
        # Clean landmarks
        data['Landmarks'] = self.clean_landmarks_display(data['Landmarks'])
        
        return data

    def extract_type5_farmhouse_data(self, prop):
        """Extract data for Type 5: Farm Houses"""
        data = self.get_common_fields(prop)
        
        # Remove Property_Name
        data.pop('Property_Name', None)
        
        # Farm House specific fields with comprehensive area info
        data.update({
            'Total_Area': self.get_flexible_area(prop),
            'Area_Type': self.get_flexible_area_type(prop),
            'Total_Area_SqM': self.get_flexible_area_sqm(prop),
            'Bedrooms': prop.get('BEDROOM_NUM', ''),
            'Bathrooms': prop.get('BATHROOM_NUM', ''),
            'Balconies': prop.get('BALCONY_NUM', ''),
            'Total_Floors': prop.get('TOTAL_FLOOR', ''),
            'Furnish': self.get_furnish_status(prop),
            'Parking_Spaces': self.get_parking_info(prop),
            'Corner_Property': 'Yes' if prop.get('CORNER_PROPERTY') == 'Y' else 'No',
            'Farm_Features': self.get_farm_features(prop),
            'Open_Space': 'Available' if any('garden' in str(feature).lower() or 'terrace' in str(feature).lower() for feature in self.decode_field_codes(prop.get('FEATURES', ''), self.FEATURES_MAPPING)) else 'Not Mentioned',
            'Security': 'Available' if any('security' in str(feature).lower() for feature in self.decode_field_codes(prop.get('FEATURES', ''), self.FEATURES_MAPPING)) else 'Not Mentioned',
            'Water_Source': 'Available' if any('water' in str(feature).lower() for feature in self.decode_field_codes(prop.get('FEATURES', ''), self.FEATURES_MAPPING)) else 'Not Mentioned'
        })
        
        # Add image information
        image_data = self.get_property_images(prop)
        data.update(image_data)
        
        # Clean landmarks
        data['Landmarks'] = self.clean_landmarks_display(data['Landmarks'])
        
        return data

    def extract_type4_builder_floor_data(self, prop):
        """Extract data for Type 4: Independent/Builder Floor"""
        # Filter out properties with no PROP_ID or minimal data
        if not prop.get('PROP_ID') or not prop.get('CITY') or not prop.get('LOCALITY'):
            return None
            
        data = self.get_common_fields(prop)
        
        # Remove Property_Name
        data.pop('Property_Name', None)
        
        # Builder Floor specific fields with comprehensive area info
        data.update({
            'Floor_Area': self.get_flexible_area(prop),
            'Area_Type': self.get_flexible_area_type(prop),
            'Floor_Area_SqM': self.get_flexible_area_sqm(prop),
            'Bedrooms': prop.get('BEDROOM_NUM', ''),
            'Bathrooms': prop.get('BATHROOM_NUM', ''),
            'Balconies': prop.get('BALCONY_NUM', ''),
            'Floor_Number': prop.get('FLOOR_NUM', ''),
            'Total_Floors': prop.get('TOTAL_FLOOR', ''),
            'Furnish': self.get_furnish_status(prop),
            'Parking_Spaces': self.get_parking_info(prop),
            'Corner_Property': 'Yes' if prop.get('CORNER_PROPERTY') == 'Y' else 'No',
            'Building_Name': prop.get('PROP_NAME', ''),
            'Floor_Type': 'Independent/Builder Floor',
            'Possession_Status': 'Ready to Move' if 'READY TO MOVE' in str(prop.get('tags', [])) else 'Under Construction'
        })
        
        # Add image information
        image_data = self.get_property_images(prop)
        data.update(image_data)
        
        # Clean landmarks
        data['Landmarks'] = self.clean_landmarks_display(data['Landmarks'])
        
        return data

    def get_furnish_status(self, prop):
        """Get furnish status"""
        formatted_furnish = self.safe_get(prop, 'FORMATTED.FURNISH_LABEL', '')
        if formatted_furnish:
            return formatted_furnish
        furnish = prop.get('FURNISH', '')
        return self.FURNISH_MAPPING.get(furnish, 'Not Specified')

    def get_parking_info(self, prop):
        """Extract comprehensive parking information"""
        parking = prop.get('RESERVED_PARKING', '')
        if parking:
            try:
                import json
                parking_data = json.loads(parking.replace("'", '"'))
                open_parking = parking_data.get('O', 0)
                covered_parking = parking_data.get('C', 0)
                
                # Format based on what's available
                if open_parking and covered_parking:
                    return f"Open: {open_parking}, Covered: {covered_parking}"
                elif open_parking:
                    return f"Open: {open_parking}"
                elif covered_parking:
                    return f"Covered: {covered_parking}"
                else:
                    return "No Parking"
            except:
                # If JSON parsing fails, return the raw parking data
                return str(parking)
        
        # Check if parking is mentioned in amenities as backup
        amenities = self.decode_field_codes(prop.get('AMENITIES', ''), self.AMENITIES_MAPPING)
        for amenity in amenities:
            if 'parking' in amenity.lower():
                return "Parking Available (from amenities)"
        
        return "Not Specified"

    def get_property_images(self, prop):
        """Extract comprehensive property image information"""
        image_data = {}
        
        # Primary image URL
        primary_image = prop.get('PHOTO_URL', '') or prop.get('MEDIUM_PHOTO_URL', '')
        image_data['Primary_Image'] = primary_image if primary_image else "No Image"
        
        # Image gallery (property images)
        property_images = prop.get('PROPERTY_IMAGES', [])
        if property_images and isinstance(property_images, list):
            image_data['Image_Gallery'] = ", ".join(property_images)
            image_data['Total_Images'] = len(property_images)
        else:
            image_data['Image_Gallery'] = "No Images"
            image_data['Total_Images'] = 0
        
        # Has photos indicator
        has_photos = prop.get('HAVEPHOTO', 'N')
        image_data['Has_Photos'] = 'Yes' if has_photos == 'Y' else 'No'
        
        # Photo count (from API)
        photo_count = prop.get('PROP_PHOTO_COUNT', '0')
        try:
            api_photo_count = int(photo_count) if photo_count else 0
        except:
            api_photo_count = 0
        image_data['API_Photo_Count'] = api_photo_count
        
        # Thumbnail images (optional)
        thumbnail_images = prop.get('THUMBNAIL_IMAGES', [])
        if thumbnail_images and isinstance(thumbnail_images, list):
            image_data['Thumbnail_Gallery'] = ", ".join(thumbnail_images)
        else:
            image_data['Thumbnail_Gallery'] = "No Thumbnails"
        
        return image_data

    def get_approved_authorities(self, prop):
        """Get approved authorities for land"""
        authorities = prop.get('APPROVED_AUTHORITIES', [])
        if authorities:
            authority_names = {
                9: "HHB (Haryana Housing Board)",
                1: "DDA (Delhi Development Authority)",
                2: "Municipal Corporation"
            }
            return [authority_names.get(auth, f"Authority {auth}") for auth in authorities]
        return ["Not Specified"]

    def get_farm_features(self, prop):
        """Get farm-specific features"""
        farm_features = []
        features = self.decode_field_codes(prop.get('FEATURES', ''), self.FEATURES_MAPPING)
        amenities = self.decode_field_codes(prop.get('AMENITIES', ''), self.AMENITIES_MAPPING)
        
        # Look for farm-related features
        farm_keywords = ['swimming pool', 'garden', 'parking', 'security', 'water']
        for feature in features + amenities:
            if any(keyword in feature.lower() for keyword in farm_keywords):
                farm_features.append(feature)
        
        return farm_features if farm_features else ["Standard Farm House Features"]

    def analyze_json_files_info(self, files, df):
        """Analyze JSON files to extract city and page information"""
        main_city = "unknown"
        page_info = "1_pages"  # Default to 1 page
        
        # Extract main city name from filename pattern: city_32_Chennai All_type1_20250708_230317.json
        for json_file in files:
            filename = os.path.basename(json_file)
            try:
                # Split by underscores and find the city part
                parts = filename.split('_')
                if len(parts) >= 3 and parts[0] == 'city':
                    # Find the city name part (between city_ID_ and _type)
                    city_part = filename.split(f'_{parts[1]}_')[1].split('_type')[0]
                    # Clean the city name
                    main_city = city_part.replace('  ', ' ').strip().replace(' ', '_').lower()
                    break  # Use the first file to get city name
            except:
                continue
        
        # Determine page scope based on property count
        if len(df) < 50:  # Small dataset = 1 page or limited pages
            page_info = "1_pages"
        else:  # Large dataset = all pages
            page_info = "all_pages"
        
        return main_city, page_info
    
    def generate_descriptive_filename(self, property_type, files, df, file_type="csv"):
        """Generate simplified filename: city_name_type_name_n_pages.extension"""
        type_names = {
            1: "apartments",
            2: "houses_villas", 
            3: "land_plots",
            4: "builder_floors",
            5: "farm_houses"
        }
        
        # Get simplified city and page info
        city_name, page_info = self.analyze_json_files_info(files, df)
        
        # Create simplified filename
        property_name = type_names.get(property_type, f"type{property_type}")
        
        if file_type == "csv":
            filename = f"{city_name}_{property_name}_{page_info}.csv"
        else:  # Excel
            filename = f"{city_name}_{property_name}_{page_info}.xlsx"
        
        return filename


    def process_all_types(self):
        """Process all property types with optimized fields"""
        print("🏘️ OPTIMIZED MULTI-PROPERTY-TYPE CLEANER")
        print("🎯 Extracts optimal fields for each property type")
        print("=" * 70)
        
        # Create output directories
        os.makedirs("output/csv_files", exist_ok=True)
        os.makedirs("output/excel_files", exist_ok=True)
        
        # Check for JSON files in output/json_files/
        json_dir = "output/json_files"
        if not os.path.exists(json_dir):
            print(f"❌ JSON files directory not found: {json_dir}")
            print("🔧 Please run the scraper first!")
            return
        
        # Find all JSON files and group by property type
        json_files = [f for f in os.listdir(json_dir) if f.endswith('.json') and 'city_' in f]
        
        if not json_files:
            print(f"❌ No JSON files found in {json_dir}")
            print("🔧 Please run the scraper first!")
            return
        
        # Group files by property type
        type_files = {1: [], 2: [], 3: [], 4: [], 5: []}
        for filename in json_files:
            if '_type1_' in filename:
                type_files[1].append(os.path.join(json_dir, filename))
            elif '_type2_' in filename:
                type_files[2].append(os.path.join(json_dir, filename))
            elif '_type3_' in filename:
                type_files[3].append(os.path.join(json_dir, filename))
            elif '_type4_' in filename:
                type_files[4].append(os.path.join(json_dir, filename))
            elif '_type5_' in filename:
                type_files[5].append(os.path.join(json_dir, filename))
        
        type_descriptions = {
            1: "Residential Apartments (excluding projects)",
            2: "Independent Houses/Villas",
            3: "Residential Land/Plots", 
            4: "Independent/Builder Floor",
            5: "Farm Houses"
        }
        
        print("📁 Property Types Found:")
        for ptype, files in type_files.items():
            if files:
                print(f"  ✅ Type {ptype}: {type_descriptions[ptype]} ({len(files)} files)")
            else:
                print(f"  ❌ Type {ptype}: {type_descriptions[ptype]} (no files)")
        
        print("\n🔧 PROCESSING EACH TYPE WITH OPTIMIZED FIELDS...")
        print("-" * 60)
        
        # Track created files for Excel creation
        created_csv_files = []
        
        for property_type, files in type_files.items():
            if not files:
                continue
                
            print(f"\n🏠 TYPE {property_type}: {type_descriptions[property_type]}")
            print(f"📁 Processing {len(files)} JSON files...")
            
            # Consolidate all properties for this type
            all_properties = []
            
            for json_file in files:
                print(f"🔧 Reading {os.path.basename(json_file)}...")
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    for prop in data:
                        try:
                            if property_type == 1:
                                extracted_data = self.extract_type1_apartment_data(prop)
                            elif property_type == 2:
                                extracted_data = self.extract_type2_house_data(prop)
                            elif property_type == 3:
                                extracted_data = self.extract_type3_land_data(prop)
                            elif property_type == 5:
                                extracted_data = self.extract_type5_farmhouse_data(prop)
                            elif property_type == 4:
                                extracted_data = self.extract_type4_builder_floor_data(prop)
                            else:
                                continue
                            
                            if extracted_data:
                                all_properties.append(extracted_data)
                                
                        except Exception as e:
                            print(f"⚠️  Warning: Error processing property: {e}")
                
                except Exception as e:
                    print(f"❌ Error reading {json_file}: {e}")
                    continue
            
            if not all_properties:
                print(f"❌ No valid properties found for Type {property_type}")
                continue
            
            # Create DataFrame and save CSV
            df = pd.DataFrame(all_properties)
            
            # Generate descriptive output filename
            descriptive_filename = self.generate_descriptive_filename(property_type, files, df, "csv")
            output_csv = f"output/csv_files/{descriptive_filename}"
            df.to_csv(output_csv, index=False, encoding='utf-8')
            created_csv_files.append((property_type, output_csv, df, files))
            
            print(f"✅ Saved: {descriptive_filename}")
            print(f"📊 Properties: {len(df)}")
            print(f"📋 Columns: {len(df.columns)}")
            
            # Show sample columns for this type
            type_names_display = {
                1: "apartments",
                2: "houses_villas", 
                3: "land_plots",
                4: "builder_floors",
                5: "farm_houses"
            }
            print(f"🔑 Key columns for {type_names_display[property_type]}:")
            key_columns = [col for col in df.columns if col not in ['Property_ID', 'Property_Name', 'Description', 'Property_URL']][:8]
            print(f"   {', '.join(key_columns)}")
        
        print("\n📊 CREATING EXCEL FILES...")
        print("-" * 40)
        
        # Create individual Excel files for each type
        for property_type, csv_file, df, files in created_csv_files:
            # Generate descriptive Excel filename
            descriptive_excel_filename = self.generate_descriptive_filename(property_type, files, df, "xlsx")
            excel_file = f"output/excel_files/{descriptive_excel_filename}"
            df.to_excel(excel_file, index=False, sheet_name=f"Type {property_type} Properties")
            print(f"📊 Excel: {descriptive_excel_filename}")
        
        # Create combined Excel file with all types
        if created_csv_files:
            print("\n📊 Creating combined Excel file...")
            
            # Generate simple combined filename
            main_city = "unknown"
            page_info = "1_pages"
            for _, _, df, files in created_csv_files:
                city_name, pages = self.analyze_json_files_info(files, df)
                if main_city == "unknown":
                    main_city = city_name
                    page_info = pages
                break
            
            combined_excel = f"output/excel_files/{main_city}_all_types_{page_info}.xlsx"
            
            with pd.ExcelWriter(combined_excel, engine='openpyxl') as writer:
                # Create summary sheet
                summary_data = []
                for property_type, csv_file, df, files in created_csv_files:
                    city_name, page_info = self.analyze_json_files_info(files, df)
                    summary_data.append({
                        'Property_Type': property_type,
                        'Type_Name': type_descriptions[property_type],
                        'Cities': city_name,
                        'Page_Scope': page_info,
                        'Count': len(df),
                        'CSV_File': os.path.basename(csv_file)
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Summary', index=False)
                
                # Add each property type as a separate sheet
                for property_type, csv_file, df, files in created_csv_files:
                    sheet_name = f"Type {property_type}"
                    # Limit sheet name to 31 chars (Excel limit)
                    if len(sheet_name) > 31:
                        sheet_name = sheet_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            print(f"📊 Combined Excel: {os.path.basename(combined_excel)}")
        
        print("\n🎯 ALL PROPERTY TYPES PROCESSED!")
        print("=" * 70)
        print("✅ CSV files saved in: output/csv_files/")
        print("✅ Excel files saved in: output/excel_files/")
        print("🎯 Each type has its optimal field structure!")

def main():
    cleaner = OptimizedMultiTypePropertyCleaner()
    cleaner.process_all_types()

if __name__ == "__main__":
    main() 