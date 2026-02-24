"""
Geocoding router - Google Geocoding API integration
"""
import math
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Configuración de Costos de Delivery
STORE_LATITUDE = 53.7145
STORE_LONGITUDE = -6.3503
BASE_DELIVERY_FEE = 3.00
RATE_PER_KM = 1.00

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calcula la distancia en kilómetros entre dos coordenadas"""
    R = 6371.0  # Radio de la Tierra en km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def calculate_delivery_fee(destination_lat: float, destination_lon: float) -> float:
    """Calcula la tarifa de delivery según la distancia a la tienda."""
    if not destination_lat or not destination_lon:
        return BASE_DELIVERY_FEE  # Tarifa base si no hay coordenadas

    distance_km = haversine_distance(STORE_LATITUDE, STORE_LONGITUDE, destination_lat, destination_lon)
    
    # Ejemplo de regla de negocio:
    # 3.00 base por los primeros 2 km, + 1.00 por cada km adicional
    if distance_km <= 2.0:
        return BASE_DELIVERY_FEE
    else:
        extra_km = distance_km - 2.0
        return round(BASE_DELIVERY_FEE + (extra_km * RATE_PER_KM), 2)

class GeocodeResponse(BaseModel):
    """Geocoding response model"""
    found: bool
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    eircode: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None
    location_type: Optional[str] = None

def parse_google_geocode_result(result: dict) -> dict:
    """
    Parse Google Geocoding API result into our address format
    """
    if not result.get("geometry"):
        return None

    address_components = {}
    street_number = ""
    route = ""

    # Parse address components
    for component in result.get("address_components", []):
        types = component.get("types", [])

        if "street_number" in types:
            street_number = component.get("long_name", "")
        elif "route" in types:
            route = component.get("long_name", "")
        elif "sublocality_level_1" in types or "sublocality" in types:
            address_components["address_line2"] = component.get("long_name", "")
        elif "locality" in types:
            address_components["city"] = component.get("long_name", "")
        elif "postal_town" in types and not address_components.get("city"):
            address_components["city"] = component.get("long_name", "")
        elif "administrative_area_level_1" in types:
            county = component.get("long_name", "")
            # Remove "County " prefix if present
            if county.startswith("County "):
                county = county[7:]
            address_components["county"] = county
        elif "postal_code" in types:
            address_components["eircode"] = component.get("long_name", "")
        elif "country" in types:
            address_components["country"] = component.get("long_name", "")

    # Combine street number and route
    address_line1 = (street_number + " " + route).strip()
    if address_line1:
        address_components["address_line1"] = address_line1

    # Get coordinates
    geometry = result.get("geometry", {})
    location = geometry.get("location", {})
    address_components["latitude"] = location.get("lat")
    address_components["longitude"] = location.get("lng")
    address_components["location_type"] = geometry.get("location_type", "")

    # Get formatted address
    address_components["formatted_address"] = result.get("formatted_address", "")

    # Set defaults for Ireland
    if not address_components.get("city"):
        address_components["city"] = "Drogheda"
    if not address_components.get("county"):
        address_components["county"] = "Louth"
    if not address_components.get("country"):
        address_components["country"] = "Ireland"

    return address_components

async def call_google_geocode(query: str) -> Optional[dict]:
    """
    Call Google Geocoding API
    """
    if not settings.GOOGLE_MAPS_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://maps.googleapis.com/maps/api/geocode/json",
                params={
                    "address": query,
                    "components": "country:IE",
                    "key": settings.GOOGLE_MAPS_API_KEY
                }
            )

            if response.status_code != 200:
                logger.error(f"Google Geocoding API error: {response.status_code}")
                return None

            data = response.json()

            if data.get("status") != "OK":
                logger.warning(f"Google Geocoding API status: {data.get('status')} - {data.get('error_message', '')}")
                return None

            results = data.get("results", [])
            if not results:
                return None

            return results[0]

    except Exception as e:
        logger.error(f"Error calling Google Geocoding API: {str(e)}")
        return None


async def call_nominatim_search(query: str) -> Optional[dict]:
    """
    Call Nominatim (OpenStreetMap) free-text search
    Free, no API key needed, 1 request/second rate limit
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "q": query,
                    "format": "json",
                    "addressdetails": 1,
                    "limit": 5,
                    "countrycodes": "ie"
                },
                headers={"User-Agent": "BurgerPOS/1.0"}
            )

            if response.status_code != 200:
                logger.error(f"Nominatim search error: {response.status_code}")
                return None

            data = response.json()
            if not data:
                return None

            # Return the first result
            return data[0]

    except Exception as e:
        logger.error(f"Error calling Nominatim search: {str(e)}")
        return None


async def call_nominatim_reverse(lat: float, lon: float) -> Optional[dict]:
    """
    Call Nominatim reverse geocoding to get address from coordinates.
    Useful when we have coordinates but no street-level address.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "lat": lat,
                    "lon": lon,
                    "format": "json",
                    "addressdetails": 1,
                    "zoom": 18  # Maximum detail level
                },
                headers={"User-Agent": "BurgerPOS/1.0"}
            )

            if response.status_code != 200:
                return None

            data = response.json()
            if not data or data.get("error"):
                return None

            return data

    except Exception as e:
        logger.error(f"Error calling Nominatim reverse: {str(e)}")
        return None


def parse_nominatim_result(result: dict) -> Optional[dict]:
    """
    Parse Nominatim result into our address format
    """
    if not result:
        return None

    address = result.get("address", {})
    
    # Build address line 1
    house_number = address.get("house_number", "")
    road = address.get("road", "")
    
    address_line1 = (house_number + " " + road).strip()
    
    # If no street address, try other fields
    if not address_line1:
        address_line1 = (
            address.get("neighbourhood", "") or 
            address.get("suburb", "") or 
            address.get("hamlet", "") or
            address.get("village", "") or
            ""
        )
    
    # If still no address, use display_name first part
    if not address_line1:
        display = result.get("display_name", "")
        parts = display.split(",")
        if parts:
            address_line1 = parts[0].strip()
    
    # Get city
    city = (
        address.get("city", "") or
        address.get("town", "") or
        address.get("village", "") or 
        address.get("hamlet", "") or
        "Drogheda"
    )
    
    # Get county
    county = address.get("county", "Louth")
    if county.startswith("County "):
        county = county[7:]
    
    # Get coordinates
    lat = float(result.get("lat", 0))
    lon = float(result.get("lon", 0))
    
    return {
        "address_line1": address_line1,
        "address_line2": address.get("suburb", "") or address.get("neighbourhood", ""),
        "city": city,
        "county": county,
        "country": "Ireland",
        "latitude": lat,
        "longitude": lon,
        "formatted_address": result.get("display_name", ""),
        "location_type": "NOMINATIM"
    }


# Eircode prefix to area mapping (for fallback)
EIRCODE_AREA_MAP = {
    "A41": {"city": "Portlaoise", "county": "Laois", "lat": 53.0342, "lon": -7.5498},
    "A63": {"city": "Longford", "county": "Longford", "lat": 53.7275, "lon": -7.7933},
    "A67": {"city": "Athlone", "county": "Westmeath", "lat": 53.4233, "lon": -7.9403},
    "A75": {"city": "Tullamore", "county": "Offaly", "lat": 53.2740, "lon": -7.4887},
    "A81": {"city": "Navan", "county": "Meath", "lat": 53.6528, "lon": -6.6816},
    "A82": {"city": "Trim", "county": "Meath", "lat": 53.5553, "lon": -6.7922},
    "A83": {"city": "Enfield", "county": "Meath", "lat": 53.4175, "lon": -6.8319},
    "A84": {"city": "Mullingar", "county": "Westmeath", "lat": 53.5246, "lon": -7.3378},
    "A85": {"city": "Kells", "county": "Meath", "lat": 53.7276, "lon": -6.8794},
    "A86": {"city": "Dunshaughlin", "county": "Meath", "lat": 53.5120, "lon": -6.5412},
    "A91": {"city": "Dundalk", "county": "Louth", "lat": 54.0008, "lon": -6.4058},
    "A92": {"city": "Drogheda", "county": "Louth", "lat": 53.7145, "lon": -6.3503},
    "A94": {"city": "Blackrock", "county": "Dublin", "lat": 53.3015, "lon": -6.1782},
    "A96": {"city": "Glenageary", "county": "Dublin", "lat": 53.2815, "lon": -6.1337},
    "A98": {"city": "Bray", "county": "Wicklow", "lat": 53.2028, "lon": -6.0985},
    "C15": {"city": "Maynooth", "county": "Kildare", "lat": 53.3814, "lon": -6.5918},
    "D01": {"city": "Dublin", "county": "Dublin", "lat": 53.3498, "lon": -6.2603},
    "D02": {"city": "Dublin", "county": "Dublin", "lat": 53.3382, "lon": -6.2591},
    "D03": {"city": "Dublin", "county": "Dublin", "lat": 53.3563, "lon": -6.2729},
    "D04": {"city": "Dublin", "county": "Dublin", "lat": 53.3285, "lon": -6.2355},
    "D05": {"city": "Dublin", "county": "Dublin", "lat": 53.3658, "lon": -6.3149},
    "D06": {"city": "Dublin", "county": "Dublin", "lat": 53.3336, "lon": -6.2773},
    "D07": {"city": "Dublin", "county": "Dublin", "lat": 53.3583, "lon": -6.2820},
    "D08": {"city": "Dublin", "county": "Dublin", "lat": 53.3397, "lon": -6.2921},
    "D09": {"city": "Dublin", "county": "Dublin", "lat": 53.3727, "lon": -6.2563},
    "D10": {"city": "Dublin", "county": "Dublin", "lat": 53.3517, "lon": -6.3235},
    "D11": {"city": "Dublin", "county": "Dublin", "lat": 53.3826, "lon": -6.2802},
    "D12": {"city": "Dublin", "county": "Dublin", "lat": 53.3232, "lon": -6.3280},
    "D13": {"city": "Dublin", "county": "Dublin", "lat": 53.3877, "lon": -6.2172},
    "D14": {"city": "Dublin", "county": "Dublin", "lat": 53.3066, "lon": -6.2553},
    "D15": {"city": "Dublin", "county": "Dublin", "lat": 53.3922, "lon": -6.3868},
    "D16": {"city": "Dublin", "county": "Dublin", "lat": 53.2927, "lon": -6.2423},
    "D17": {"city": "Dublin", "county": "Dublin", "lat": 53.3958, "lon": -6.1836},
    "D18": {"city": "Dublin", "county": "Dublin", "lat": 53.2755, "lon": -6.2108},
    "D20": {"city": "Dublin", "county": "Dublin", "lat": 53.3342, "lon": -6.3818},
    "D22": {"city": "Dublin", "county": "Dublin", "lat": 53.3135, "lon": -6.3855},
    "D24": {"city": "Dublin", "county": "Dublin", "lat": 53.2875, "lon": -6.3720},
    "E21": {"city": "Arklow", "county": "Wicklow", "lat": 52.7950, "lon": -6.1622},
    "E25": {"city": "Wicklow", "county": "Wicklow", "lat": 52.9748, "lon": -6.0504},
    "E32": {"city": "Gorey", "county": "Wexford", "lat": 52.6748, "lon": -6.2932},
    "E34": {"city": "Enniscorthy", "county": "Wexford", "lat": 52.5015, "lon": -6.5643},
    "E41": {"city": "Carlow", "county": "Carlow", "lat": 52.8365, "lon": -6.9261},
    "E45": {"city": "New Ross", "county": "Wexford", "lat": 52.3964, "lon": -6.9371},
    "E53": {"city": "Kilkenny", "county": "Kilkenny", "lat": 52.6541, "lon": -7.2448},
    "E91": {"city": "Wexford", "county": "Wexford", "lat": 52.3369, "lon": -6.4633},
    "F12": {"city": "Castlebar", "county": "Mayo", "lat": 53.7609, "lon": -9.2954},
    "F23": {"city": "Ballinrobe", "county": "Mayo", "lat": 53.6308, "lon": -9.2280},
    "F26": {"city": "Belmullet", "county": "Mayo", "lat": 54.2250, "lon": -10.0004},
    "F28": {"city": "Westport", "county": "Mayo", "lat": 53.8007, "lon": -9.5162},
    "F31": {"city": "Roscommon", "county": "Roscommon", "lat": 53.6315, "lon": -8.1833},
    "F35": {"city": "Boyle", "county": "Roscommon", "lat": 53.9719, "lon": -8.2905},
    "F42": {"city": "Ballina", "county": "Mayo", "lat": 54.1145, "lon": -9.1566},
    "F45": {"city": "Claremorris", "county": "Mayo", "lat": 53.7223, "lon": -8.9856},
    "F52": {"city": "Tuam", "county": "Galway", "lat": 53.5126, "lon": -8.8565},
    "F56": {"city": "Ballinasloe", "county": "Galway", "lat": 53.3313, "lon": -8.2338},
    "F91": {"city": "Sligo", "county": "Sligo", "lat": 54.2766, "lon": -8.4761},
    "F92": {"city": "Donegal", "county": "Donegal", "lat": 54.6538, "lon": -8.1096},
    "F93": {"city": "Letterkenny", "county": "Donegal", "lat": 54.9536, "lon": -7.7358},
    "F94": {"city": "Carrick-on-Shannon", "county": "Leitrim", "lat": 53.9470, "lon": -8.0905},
    "H12": {"city": "Cavan", "county": "Cavan", "lat": 53.9897, "lon": -7.3633},
    "H14": {"city": "Virginia", "county": "Cavan", "lat": 53.8348, "lon": -7.0810},
    "H16": {"city": "Monaghan", "county": "Monaghan", "lat": 54.2492, "lon": -6.9685},
    "H18": {"city": "Clones", "county": "Monaghan", "lat": 54.1803, "lon": -7.2322},
    "H23": {"city": "Carrickmacross", "county": "Monaghan", "lat": 54.0006, "lon": -6.7177},
    "H53": {"city": "Loughrea", "county": "Galway", "lat": 53.1920, "lon": -8.5686},
    "H54": {"city": "Clifden", "county": "Galway", "lat": 53.4892, "lon": -10.0203},
    "H62": {"city": "Oranmore", "county": "Galway", "lat": 53.2706, "lon": -8.9304},
    "H65": {"city": "Athenry", "county": "Galway", "lat": 53.2965, "lon": -8.7479},
    "H71": {"city": "Ennis", "county": "Clare", "lat": 52.8432, "lon": -8.9862},
    "H91": {"city": "Galway", "county": "Galway", "lat": 53.2707, "lon": -9.0568},
    "K32": {"city": "Swords", "county": "Dublin", "lat": 53.4582, "lon": -6.2187},
    "K34": {"city": "Malahide", "county": "Dublin", "lat": 53.4508, "lon": -6.1545},
    "K36": {"city": "Balbriggan", "county": "Dublin", "lat": 53.6094, "lon": -6.1870},
    "K45": {"city": "Celbridge", "county": "Kildare", "lat": 53.3398, "lon": -6.5401},
    "K56": {"city": "Leixlip", "county": "Kildare", "lat": 53.3648, "lon": -6.4895},
    "K67": {"city": "Naas", "county": "Kildare", "lat": 53.2159, "lon": -6.6596},
    "K78": {"city": "Athy", "county": "Kildare", "lat": 52.9916, "lon": -6.9821},
    "N37": {"city": "Nenagh", "county": "Tipperary", "lat": 52.8618, "lon": -8.1960},
    "N39": {"city": "Birr", "county": "Offaly", "lat": 53.0978, "lon": -7.9127},
    "N41": {"city": "Edenderry", "county": "Offaly", "lat": 53.3431, "lon": -7.0476},
    "N91": {"city": "Drogheda", "county": "Louth", "lat": 53.7145, "lon": -6.3503},
    "P12": {"city": "Cork", "county": "Cork", "lat": 51.8985, "lon": -8.4756},
    "P14": {"city": "Youghal", "county": "Cork", "lat": 51.9534, "lon": -7.8460},
    "P17": {"city": "Midleton", "county": "Cork", "lat": 51.9145, "lon": -8.1729},
    "P24": {"city": "Bandon", "county": "Cork", "lat": 51.7464, "lon": -8.7375},
    "P25": {"city": "Kinsale", "county": "Cork", "lat": 51.7068, "lon": -8.5309},
    "P31": {"city": "Carrigaline", "county": "Cork", "lat": 51.8181, "lon": -8.3924},
    "P32": {"city": "Fermoy", "county": "Cork", "lat": 52.1383, "lon": -8.2750},
    "P36": {"city": "Cobh", "county": "Cork", "lat": 51.8517, "lon": -8.2961},
    "P43": {"city": "Mallow", "county": "Cork", "lat": 52.1344, "lon": -8.6431},
    "P47": {"city": "Macroom", "county": "Cork", "lat": 51.9062, "lon": -8.9612},
    "P51": {"city": "Kanturk", "county": "Cork", "lat": 52.1778, "lon": -8.9047},
    "P56": {"city": "Castletownbere", "county": "Cork", "lat": 51.6500, "lon": -9.9078},
    "P61": {"city": "Skibbereen", "county": "Cork", "lat": 51.5522, "lon": -9.2637},
    "P67": {"city": "Clonakilty", "county": "Cork", "lat": 51.6238, "lon": -8.8887},
    "P72": {"city": "Bantry", "county": "Cork", "lat": 51.6811, "lon": -9.4505},
    "P75": {"city": "Dunmanway", "county": "Cork", "lat": 51.7207, "lon": -9.1115},
    "P81": {"city": "Tramore", "county": "Waterford", "lat": 52.1619, "lon": -7.1532},
    "P85": {"city": "Dungarvan", "county": "Waterford", "lat": 52.0886, "lon": -7.6210},
    "R14": {"city": "Greystones", "county": "Wicklow", "lat": 53.1419, "lon": -6.0618},
    "R21": {"city": "Thurles", "county": "Tipperary", "lat": 52.6810, "lon": -7.8008},
    "R32": {"city": "Newbridge", "county": "Kildare", "lat": 53.1820, "lon": -6.7973},
    "R35": {"city": "Kildare", "county": "Kildare", "lat": 53.1567, "lon": -6.9116},
    "R42": {"city": "Portarlington", "county": "Laois", "lat": 53.1634, "lon": -7.1899},
    "R45": {"city": "Mountmellick", "county": "Laois", "lat": 53.1131, "lon": -7.3258},
    "R51": {"city": "Cashel", "county": "Tipperary", "lat": 52.5168, "lon": -7.8875},
    "R56": {"city": "Shannon", "county": "Clare", "lat": 52.7095, "lon": -8.8623},
    "R93": {"city": "Clonmel", "county": "Tipperary", "lat": 52.3553, "lon": -7.7079},
    "R95": {"city": "Tipperary", "county": "Tipperary", "lat": 52.4735, "lon": -8.1553},
    "T12": {"city": "Cork", "county": "Cork", "lat": 51.8985, "lon": -8.4756},
    "T23": {"city": "Cork", "county": "Cork", "lat": 51.8985, "lon": -8.4756},
    "T34": {"city": "Ballincollig", "county": "Cork", "lat": 51.8868, "lon": -8.5851},
    "T45": {"city": "Douglas", "county": "Cork", "lat": 51.8728, "lon": -8.4328},
    "T56": {"city": "Glanmire", "county": "Cork", "lat": 51.9108, "lon": -8.3952},
    "V14": {"city": "Listowel", "county": "Kerry", "lat": 52.4452, "lon": -9.4856},
    "V15": {"city": "Tralee", "county": "Kerry", "lat": 52.2710, "lon": -9.6993},
    "V23": {"city": "Killarney", "county": "Kerry", "lat": 52.0599, "lon": -9.5045},
    "V31": {"city": "Dingle", "county": "Kerry", "lat": 52.1413, "lon": -10.2685},
    "V35": {"city": "Kenmare", "county": "Kerry", "lat": 51.8804, "lon": -9.5830},
    "V42": {"city": "Newcastle West", "county": "Limerick", "lat": 52.4494, "lon": -9.0610},
    "V63": {"city": "Kilmallock", "county": "Limerick", "lat": 52.3993, "lon": -8.5752},
    "V92": {"city": "Cahirciveen", "county": "Kerry", "lat": 51.9474, "lon": -10.2257},
    "V93": {"city": "Killorglin", "county": "Kerry", "lat": 52.1027, "lon": -9.7825},
    "V94": {"city": "Limerick", "county": "Limerick", "lat": 52.6638, "lon": -8.6267},
    "V95": {"city": "Abbeyfeale", "county": "Limerick", "lat": 52.3848, "lon": -9.3017},
    "W12": {"city": "Lucan", "county": "Dublin", "lat": 53.3500, "lon": -6.4479},
    "W23": {"city": "Tallaght", "county": "Dublin", "lat": 53.2876, "lon": -6.3540},
    "W34": {"city": "Clondalkin", "county": "Dublin", "lat": 53.3239, "lon": -6.3941},
    "W91": {"city": "Waterford", "county": "Waterford", "lat": 52.2593, "lon": -7.1101},
    "X35": {"city": "Carrick-on-Suir", "county": "Tipperary", "lat": 52.3477, "lon": -7.4107},
    "X42": {"city": "Thomastown", "county": "Kilkenny", "lat": 52.5307, "lon": -7.1375},
    "X91": {"city": "Waterford", "county": "Waterford", "lat": 52.2593, "lon": -7.1101},
    "Y14": {"city": "Wexford", "county": "Wexford", "lat": 52.3369, "lon": -6.4633},
    "Y21": {"city": "Gorey", "county": "Wexford", "lat": 52.6748, "lon": -6.2932},
    "Y25": {"city": "New Ross", "county": "Wexford", "lat": 52.3964, "lon": -6.9371},
    "Y34": {"city": "Enniscorthy", "county": "Wexford", "lat": 52.5015, "lon": -6.5643},
    "Y35": {"city": "Rosslare", "county": "Wexford", "lat": 52.2576, "lon": -6.3850},
}


@router.get("/api/geocoding/eircode", response_model=GeocodeResponse)
async def geocode_eircode(code: str = Query(..., description="Irish Eircode to geocode")):
    """
    Geocode an Irish Eircode using multiple strategies:
    
    1. Eircode prefix map → get correct area/city/coords
    2. Nominatim reverse geocoding → get real street name from area coords
    3. Google Geocoding API (fallback, if API key works)
    
    NOTE: Nominatim free-text search does NOT work for Eircodes
    (Eircodes are proprietary An Post data not in OpenStreetMap).
    For exact Eircode→address mapping, a paid service like Autoaddress.ie is needed.
    """
    # Clean up eircode (remove spaces, uppercase)
    clean_eircode = code.replace(" ", "").upper()

    if not clean_eircode:
        raise HTTPException(status_code=400, detail="Eircode cannot be empty")

    # Format with space for search: A92D65P -> A92 D65P
    formatted_eircode = clean_eircode
    if len(clean_eircode) == 7:
        formatted_eircode = clean_eircode[:3] + " " + clean_eircode[3:]

    logger.info(f"🔍 Geocoding Eircode: {formatted_eircode}")

    best_result = None
    prefix = clean_eircode[:3]
    area_info = EIRCODE_AREA_MAP.get(prefix)

    # === Strategy 1: Google Geocoding API (may return exact address) ===
    if settings.GOOGLE_MAPS_API_KEY:
        logger.info("🗺️ Strategy 1: Google Geocoding API...")
        
        query1 = f"{formatted_eircode}, Ireland"
        google_result = await call_google_geocode(query1)

        # Try with area context for better precision
        if area_info and (not google_result or google_result.get("geometry", {}).get("location_type") != "ROOFTOP"):
            query2 = f"{formatted_eircode}, {area_info['city']}, Co. {area_info['county']}, Ireland"
            google_result2 = await call_google_geocode(query2)
            if google_result2:
                if not google_result or google_result2.get("geometry", {}).get("location_type") == "ROOFTOP":
                    google_result = google_result2

        if google_result:
            parsed = parse_google_geocode_result(google_result)
            if parsed:
                addr = parsed.get("address_line1", "")
                if addr and not any(x in addr.lower() for x in ["area", "county", "ireland"]):
                    logger.info(f"✅ Google found street-level: {parsed.get('formatted_address')}")
                    best_result = parsed
                elif parsed.get("latitude") and parsed.get("longitude"):
                    # Google gave us coordinates but no street → reverse geocode
                    logger.info(f"📍 Strategy 1b: Reverse geocoding Google coordinates...")
                    import asyncio
                    await asyncio.sleep(1)  # Nominatim rate limit
                    reverse_result = await call_nominatim_reverse(parsed["latitude"], parsed["longitude"])
                    if reverse_result:
                        reverse_parsed = parse_nominatim_result(reverse_result)
                        if reverse_parsed:
                            reverse_addr = reverse_parsed.get("address_line1", "")
                            if reverse_addr and not any(x in reverse_addr.lower() for x in ["area", "county"]):
                                # Override city/county with prefix map data (more reliable)
                                if area_info:
                                    reverse_parsed["city"] = area_info["city"]
                                    reverse_parsed["county"] = area_info["county"]
                                logger.info(f"✅ Reverse geocoding found: {reverse_addr}")
                                best_result = reverse_parsed

    # === Strategy 2: Eircode prefix map + reverse geocoding ===
    if not best_result and area_info:
        logger.info(f"📋 Strategy 2: Eircode prefix map for {prefix} ({area_info['city']})")
        
        # Reverse geocode the area center coordinates for a real street name
        reverse_result = await call_nominatim_reverse(area_info["lat"], area_info["lon"])
        
        if reverse_result:
            reverse_parsed = parse_nominatim_result(reverse_result)
            if reverse_parsed:
                reverse_addr = reverse_parsed.get("address_line1", "")
                if reverse_addr and reverse_addr != area_info["city"]:
                    # Use the street from reverse geocoding but city/county from prefix map
                    reverse_parsed["city"] = area_info["city"]
                    reverse_parsed["county"] = area_info["county"]
                    logger.info(f"✅ Reverse geocoding area center: {reverse_addr}, {area_info['city']}")
                    best_result = reverse_parsed
        
        # Final fallback: just use the prefix map data
        if not best_result:
            best_result = {
                "address_line1": f"{area_info['city']} Area",
                "city": area_info["city"],
                "county": area_info["county"],
                "country": "Ireland",
                "latitude": area_info["lat"],
                "longitude": area_info["lon"],
                "formatted_address": f"{area_info['city']}, Co. {area_info['county']}, Ireland",
                "location_type": "PREFIX_MAP"
            }

    if not best_result:
        logger.warning(f"❌ Eircode not found: {clean_eircode}")
        return GeocodeResponse(found=False)

    # Ensure eircode is set to the clean version
    best_result["eircode"] = clean_eircode

    logger.info(f"✅ Geocoded {clean_eircode}: {best_result.get('address_line1')}, {best_result.get('city')}")

    return GeocodeResponse(
        found=True,
        address_line1=best_result.get("address_line1"),
        address_line2=best_result.get("address_line2"),
        city=best_result.get("city"),
        county=best_result.get("county"),
        eircode=best_result.get("eircode"),
        latitude=best_result.get("latitude"),
        longitude=best_result.get("longitude"),
        formatted_address=best_result.get("formatted_address"),
        location_type=best_result.get("location_type")
    )

