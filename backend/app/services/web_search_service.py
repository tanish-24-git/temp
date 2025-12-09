"""Web Search Service

Integrates with search APIs to fetch industry-specific compliance regulations.
Prioritizes open-source and free solutions.

Search Strategy (in order):
1. SearxNG (open source, self-hosted, FREE) ⭐
2. DuckDuckGo Instant Answer API (free, no key needed) ⭐
3. Serper API (paid, requires API key)
4. RAG Fallback (hardcoded knowledge base, always works) ⭐
"""

import os
import logging
from typing import List, Dict, Any, Optional
import httpx
from ..config import settings
from .compliance_knowledge_base import get_fallback_knowledge, search_knowledge_base

logger = logging.getLogger(__name__)


class WebSearchService:
    """
    Search for industry regulations and best practices.
    
    **Open Source First**: Tries free/open-source options before paid APIs.
    
    Priority Order:
    1. SearxNG (docker run -p 8888:8080 searxng/searxng)
    2. DuckDuckGo (no setup needed)
    3. Serper API (optional, needs SERPER_API_KEY)
    4. RAG Fallback (always works)
    """
    
    def __init__(self):
        self.searxng_url = os.getenv("SEARXNG_URL", "http://localhost:8888")
        self.serper_api_key = os.getenv("SERPER_API_KEY")
        
        logger.info("WebSearchService initialized with open-source priority")
    
    async def search_regulations(
        self,
        industry: str,
        region: str = "India",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for industry-specific compliance regulations.
        
        Args:
            industry: Industry name (e.g., "insurance", "healthcare")
            region: Geographic region (e.g., "India", "US", "EU")
            max_results: Maximum number of results to return
            
        Returns:
            List of search results with title, snippet, url
        """
        query = f"{industry} compliance regulations {region} requirements"
        
        # Strategy 1: SearxNG (open source)
        try:
            results = await self._search_via_searxng(query, max_results)
            if results:
                logger.info(f"✅ Search via SearxNG: {len(results)} results")
                return results
        except Exception as e:
            logger.debug(f"SearxNG unavailable: {str(e)}")
        
        # Strategy 2: DuckDuckGo (free, open)
        try:
            results = await self._search_via_duckduckgo(query, max_results)
            if results:
                logger.info(f"✅ Search via DuckDuckGo: {len(results)} results")
                return results
        except Exception as e:
            logger.debug(f"DuckDuckGo search failed: {str(e)}")
        
        # Strategy 3: Serper (paid, optional)
        if self.serper_api_key:
            try:
                results = await self._search_via_serper(query, max_results)
                if results:
                    logger.info(f"✅ Search via Serper: {len(results)} results")
                    return results
            except Exception as e:
                logger.debug(f"Serper API failed: {str(e)}")
        
        # Strategy 4: RAG Fallback (always works)
        logger.info(f"📚 Using RAG fallback for industry: {industry}")
        return get_fallback_knowledge(industry)[:max_results]
    
    async def search_brand_guidelines(
        self,
        industry: str,
        topics: List[str],
        max_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for brand guideline best practices."""
        query = f"{industry} brand guidelines best practices {' '.join(topics)}"
        
        # Try open source first
        for search_method in [
            self._search_via_searxng,
            self._search_via_duckduckgo,
        ]:
            try:
                results = await search_method(query, max_results)
                if results:
                    return results
            except:
                continue
        
        # RAG fallback
        logger.info("📚 Using RAG fallback for brand guidelines")
        return search_knowledge_base(query, industry)[:max_results]
    
    async def _search_via_serper(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Search using Serper API (https://serper.dev).
        
        Requires SERPER_API_KEY environment variable.
        """
        url = "https://google.serper.dev/search"
        
        headers = {
            "X-API-KEY": self.serper_api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": max_results
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Parse results
            results = []
            for item in data.get("organic", [])[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": "serper"
                })
            
            logger.info(f"Serper search returned {len(results)} results")
            return results
    
    async def _search_via_duckduckgo(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo Instant Answer API (FREE, no key needed).
        
        Open source, privacy-focused, no rate limits for reasonable use.
        """
        url = "https://api.duckduckgo.com/"
        
        params = {
            "q": query,
            "format": "json",
            "no_html": "1",
            "skip_disambig": "1"
        }
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                results = []
                
                # Parse abstract (if available)
                if data.get("Abstract"):
                    results.append({
                        "title": data.get("Heading", "Compliance Information"),
                        "snippet": data.get("Abstract", ""),
                        "url": data.get("AbstractURL", ""),
                        "source": "duckduckgo"
                    })
                
                # Parse related topics
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and topic.get("Text"):
                        results.append({
                            "title": topic.get("Text", "")[:100],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", ""),
                            "source": "duckduckgo"
                        })
                
                if results:
                    logger.info(f"DuckDuckGo returned {len(results)} results")
                
                return results[:max_results]
                
        except Exception as e:
            logger.debug(f"DuckDuckGo search failed: {str(e)}")
            return []
    
    async def _search_via_searxng(
        self,
        query: str,
        max_results: int
    ) -> List[Dict[str, Any]]:
        """
        Search using self-hosted SearxNG instance (OPEN SOURCE).
        
        Setup: docker run -d -p 8888:8080 searxng/searxng
        Set SEARXNG_URL=http://localhost:8888
        """
        url = f"{self.searxng_url}/search"
        
        params = {
            "q": query,
            "format": "json",
            "pageno": 1
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                # Parse results
                results = []
                for item in data.get("results", [])[:max_results]:
                    results.append({
                        "title": item.get("title", ""),
                        "snippet": item.get("content", ""),
                        "url": item.get("url", ""),
                        "source": "searxng"
                    })
                
                logger.info(f"SearxNG search returned {len(results)} results")
                return results
                
        except httpx.ConnectError:
            logger.warning(
                f"SearxNG not available at {self.searxng_url}. "
                "Install with: docker run -d -p 8888:8080 searxng/searxng"
            )
            return []
        except Exception as e:
            logger.error(f"SearxNG search failed: {str(e)}")
            return []
    
    def _parse_results(self, results: List[Dict]) -> List[Dict[str, str]]:
        """
        Parse and clean search results.
        
        Extracts title, snippet, url from various search providers.
        """
        parsed = []
        
        for result in results:
            parsed.append({
                "title": result.get("title", "").strip(),
                "snippet": result.get("snippet", "").strip(),
                "url": result.get("url", "").strip()
            })
        
        return parsed


# Singleton instance
web_search_service = WebSearchService()
