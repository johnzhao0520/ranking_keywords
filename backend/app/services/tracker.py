"""
Google Keyword Tracking Service

Uses Serper.dev API to track keyword rankings
Docs: https://serper.dev/docs/search
"""
import httpx
from typing import Optional, List
from app.core.config import settings
import asyncio


class GoogleTracker:
    def __init__(self, api_key: str = None):
        self.api_key = (api_key or settings.SERPER_API_KEY or "").strip()
        self.base_url = "https://google.serper.dev/search"
    
    async def track_keyword(
        self, 
        keyword: str, 
        country: str = "com",
        language: str = "en"
    ) -> Optional[dict]:
        """Track a keyword and return ranking results"""
        
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not configured")
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Serper.dev supports country codes in the 'gl' parameter
        params = {
            "q": keyword,
            "gl": country,  # Country: com, co.uk, co.jp, etc.
            "hl": language,  # Language: en, zh-CN, etc.
            "num": 100  # Get top 100 results
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    self.base_url, 
                    headers=headers, 
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                
                # Parse organic results
                results = data.get("organic", [])
                
                # Extract position and details for each result
                ranked_results = []
                for idx, result in enumerate(results, 1):
                    ranked_results.append({
                        "position": idx,
                        "title": result.get("title"),
                        "link": result.get("link"),
                        "snippet": result.get("snippet"),
                        "domain": self._extract_domain(result.get("link", "")),
                    })
                
                return {
                    "results": ranked_results,
                    "count": len(ranked_results),
                    "keyword": keyword,
                    "country": country,
                }
                
            except httpx.HTTPError as e:
                print(f"HTTP error tracking keyword {keyword}: {e}")
                return None
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""
        try:
            from urllib.parse import urlparse
            return urlparse(url).netloc
        except:
            return ""
    
    def calculate_credits(self, rank: int) -> int:
        """Calculate credits based on ranking position"""
        if rank is None or rank <= 0:
            return 1
        if rank <= 100:
            return 10  # Top 100 costs 10x
        return 1
    
    async def track_multiple(
        self, 
        keywords: List[dict],
        delay: float = 1.0  # Delay between requests to avoid rate limiting
    ) -> List[dict]:
        """Track multiple keywords with rate limiting"""
        
        results = []
        
        for kw_info in keywords:
            result = await self.track_keyword(
                keyword=kw_info.get("keyword"),
                country=kw_info.get("country", "com"),
                language=kw_info.get("language", "en")
            )
            
            if result:
                results.append({
                    "keyword_id": kw_info.get("id"),
                    "success": True,
                    "data": result
                })
            else:
                results.append({
                    "keyword_id": kw_info.get("id"),
                    "success": False,
                    "error": "Tracking failed"
                })
            
            # Rate limiting
            if delay > 0:
                await asyncio.sleep(delay)
        
        return results


# Singleton instance
google_tracker = GoogleTracker()


# Usage Example:
"""
from app.services.tracker import google_tracker

# Single keyword
result = await google_tracker.track_keyword(
    keyword="SEO services",
    country="com",  # Google.com
    language="en"
)

# Multiple keywords
results = await google_tracker.track_multiple([
    {"id": 1, "keyword": "SEO services", "country": "com"},
    {"id": 2, "keyword": "SEO agency", "country": "co.uk"},
])

# Calculate credits
credits = google_tracker.calculate_credits(rank=5)  # Returns 10 for top 100
"""


# Country Code Reference:
"""
Google Domains:
- com (United States)
- co.uk (United Kingdom)
- co.jp (Japan)
- com.au (Australia)
- de (Germany)
- fr (France)
- ca (Canada)
- co.in (India)
- com.br (Brazil)
- com.sg (Singapore)
- co.nz (New Zealand)
- cn (China)
- hk (Hong Kong)
- tw (Taiwan)

Use 'gl' parameter to target specific country
"""
