from typing import Any

from ddgs import DDGS

from app.core.config import WEB_CORROBORATION_MAX_RESULTS
from app.providers import ProviderUnavailable


class DuckDuckGoNewsProvider:
    """Fetch recent public news without passing reporter-authored text upstream."""

    def search(self, category: str, location_name: str) -> list[dict[str, Any]]:
        query = f'{category} {location_name} Kenya'
        try:
            results = list(
                DDGS().news(
                    query=query,
                    region='wt-wt',
                    safesearch='moderate',
                    timelimit='d',
                    max_results=WEB_CORROBORATION_MAX_RESULTS,
                )
                or []
            )
            # A weekly fallback is intentionally used only when today's search
            # has no usable results. The service still rejects results >48h old.
            if not results:
                results = list(
                    DDGS().news(
                        query=query,
                        region='wt-wt',
                        safesearch='moderate',
                        timelimit='w',
                        max_results=WEB_CORROBORATION_MAX_RESULTS,
                    )
                    or []
                )
            return results
        except Exception as error:
            raise ProviderUnavailable('DuckDuckGo News search failed') from error
