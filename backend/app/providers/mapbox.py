import httpx
from app.core.config import MAPBOX_ACCESS_TOKEN,PROVIDER_TIMEOUT_SECONDS
from app.providers import ProviderUnavailable
from app.schemas import GeocodingResult
class MapboxGeocodingProvider:
    def geocode(self,location:str)->GeocodingResult:
        if not MAPBOX_ACCESS_TOKEN:raise ProviderUnavailable('MAPBOX_ACCESS_TOKEN is not configured')
        try:
            response=httpx.get('https://api.mapbox.com/search/geocode/v6/forward',params={'q':location,'country':'ke','limit':1,'access_token':MAPBOX_ACCESS_TOKEN},timeout=PROVIDER_TIMEOUT_SECONDS)
            response.raise_for_status();features=response.json().get('features',[])
            if not features:return GeocodingResult(display_name=location,confidence=0)
            feature=features[0];coordinates=feature.get('geometry',{}).get('coordinates',[])
            return GeocodingResult(latitude=coordinates[1] if len(coordinates)>1 else None,longitude=coordinates[0] if len(coordinates)>1 else None,display_name=feature.get('properties',{}).get('full_address') or feature.get('place_formatted') or feature.get('name') or location,confidence=.8)
        except (httpx.HTTPError,ValueError,IndexError) as error:
            raise ProviderUnavailable('Mapbox geocoding failed') from error
