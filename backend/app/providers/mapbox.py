import re
import httpx
from app.core.config import MAPBOX_ACCESS_TOKEN,PROVIDER_TIMEOUT_SECONDS
from app.providers import ProviderUnavailable
from app.schemas import GeocodingResult
class MapboxGeocodingProvider:
    _coordinate_input=re.compile(r'^\s*(-?\d{1,2}(?:\.\d+)?)\s*,\s*(-?\d{1,3}(?:\.\d+)?)\s*$')

    @classmethod
    def _browser_coordinates(cls,location:str)->tuple[float,float]|None:
        """Accept only an explicit latitude, longitude pair within Kenya."""
        match=cls._coordinate_input.match(location)
        if not match:return None
        latitude,longitude=(float(value) for value in match.groups())
        if -4.7<=latitude<=5.5 and 33.9<=longitude<=41.9:return latitude,longitude
        return None

    @staticmethod
    def _result(feature:dict,fallback:str,confidence:float)->GeocodingResult:
        coordinates=feature.get('geometry',{}).get('coordinates',[])
        return GeocodingResult(
            latitude=coordinates[1] if len(coordinates)>1 else None,
            longitude=coordinates[0] if len(coordinates)>1 else None,
            display_name=feature.get('properties',{}).get('full_address') or feature.get('place_formatted') or feature.get('name') or fallback,
            confidence=confidence,
        )

    def geocode(self,location:str)->GeocodingResult:
        if not MAPBOX_ACCESS_TOKEN:raise ProviderUnavailable('MAPBOX_ACCESS_TOKEN is not configured')
        try:
            coordinates=self._browser_coordinates(location)
            if coordinates:
                latitude,longitude=coordinates
                response=httpx.get('https://api.mapbox.com/search/geocode/v6/reverse',params={'longitude':longitude,'latitude':latitude,'country':'ke','limit':1,'access_token':MAPBOX_ACCESS_TOKEN},timeout=PROVIDER_TIMEOUT_SECONDS)
            else:
                response=httpx.get('https://api.mapbox.com/search/geocode/v6/forward',params={'q':location,'country':'ke','limit':1,'access_token':MAPBOX_ACCESS_TOKEN},timeout=PROVIDER_TIMEOUT_SECONDS)
            response.raise_for_status();features=response.json().get('features',[])
            if not features:return GeocodingResult(display_name=location,confidence=0)
            return self._result(features[0],location,.9 if coordinates else .8)
        except (httpx.HTTPError,ValueError,IndexError) as error:
            raise ProviderUnavailable('Mapbox geocoding failed') from error
