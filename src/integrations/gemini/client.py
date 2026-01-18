"""
Gemini API client for KonseptiKeiju.

Provides wrapper for Google's Gemini API with support for:
- Standard generation
- Deep Research with Google Search grounding
- Retry logic and error handling
- Automatic prompt logging for traceability

Uses the new google-genai SDK (google.generativeai is deprecated).
"""

import asyncio
from typing import Any

from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.logger import get_logger
from src.core.prompt_logger import log_prompt

logger = get_logger(__name__)


class GeminiClient:
    """
    Client for Google Gemini API using google-genai SDK.
    
    Handles authentication, request formatting, and response parsing.
    Supports standard generation and research with search grounding.
    """

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model = settings.gemini_model
        self._client = None

    def _get_client(self):
        """Get or create the google-genai client."""
        if self._client is None:
            from google import genai
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    @staticmethod
    def _extract_text_from_response(response: Any) -> str:
        """
        Robustly extract text from a google-genai response.

        Some models/SDK versions may return `response.text=None` even when
        content exists in candidates/parts. We defensively probe fields.
        """
        if response is None:
            return ""
        # Preferred
        text = getattr(response, "text", None)
        if isinstance(text, str) and text.strip():
            return text

        # Fallback to candidates[0].content.parts[].text
        candidates = getattr(response, "candidates", None) or []
        if candidates:
            cand0 = candidates[0]
            content = getattr(cand0, "content", None)
            if content is not None:
                parts = getattr(content, "parts", None) or []
                texts: list[str] = []
                for p in parts:
                    t = getattr(p, "text", None)
                    if isinstance(t, str) and t:
                        texts.append(t)
                joined = "".join(texts).strip()
                if joined:
                    return joined

        # Last resort: string repr
        try:
            return str(response).strip()
        except Exception:
            return ""

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 8192,
        category: str = "research",
        prompt_type: str = "generate",
    ) -> str:
        """
        Generate a response from Gemini.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system instructions
            temperature: Creativity setting (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Generated text response
        """
        from google.genai import types
        
        client = self._get_client()
        
        # Build full prompt with system instructions
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n---\n\n{prompt}"
        
        logger.debug(
            "Gemini generate request",
            model=self.model,
            prompt_length=len(full_prompt),
        )
        
        # Run in thread pool since the SDK may block
        loop = asyncio.get_event_loop()
        
        def execute():
            response = client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
            )
            return self._extract_text_from_response(response)
        
        result = await loop.run_in_executor(None, execute)
        
        # Log the prompt for traceability
        log_prompt(
            category=category,
            prompt_type=prompt_type,
            prompt=full_prompt,
            metadata={
                "model": self.model,
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
            response=result,
        )
        
        logger.info(
            "Gemini generate complete",
            model=self.model,
            response_length=len(result or ""),
        )
        
        return result


    async def deep_research(
        self,
        query: str,
        system_prompt: str | None = None,
    ) -> str:
        """
        Conduct deep research using Gemini with Google Search grounding.
        
        Uses the google-genai SDK with search grounding to gather
        real-time information about the target company.
        
        Args:
            query: The research query
            system_prompt: Optional system instructions to prepend
            
        Returns:
            Research results as markdown text
        """
        from google.genai import types
        
        client = self._get_client()
        
        logger.info("Starting Gemini Research with Search Grounding", query_length=len(query))
        print("🔍 Starting Deep Research with Google Search...")
        
        # Build full query with system context
        full_query = query
        if system_prompt:
            full_query = f"{system_prompt}\n\n---\n\n{query}"
        
        # Log the prompt before execution
        log_prompt(
            category="research",
            prompt_type="deep_research",
            prompt=full_query,
            metadata={
                "model": self.model,
                "system_prompt_included": system_prompt is not None,
                "method": "search_grounding",
            },
        )
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        
        def _format_sources_md(sources: list[dict[str, str]]) -> str:
            if not sources:
                return ""
            lines = ["", "", "## Lähteet (Search Grounding)", ""]
            for s in sources:
                title = (s.get("title") or "").strip()
                url = (s.get("url") or "").strip()
                if not url:
                    continue
                if title:
                    lines.append(f"- {title} — {url}")
                else:
                    lines.append(f"- {url}")
            return "\n".join(lines).rstrip() + "\n"

        def _extract_sources_from_response(response: Any) -> list[dict[str, str]]:
            """
            Attempt to extract grounded/citation sources from a google-genai response.

            The SDK's response shape can vary; we defensively probe likely fields.
            """
            out: list[dict[str, str]] = []
            seen: set[str] = set()

            def _add(url: str | None, title: str | None = None) -> None:
                if not url:
                    return
                u = str(url).strip()
                if not u or u in seen:
                    return
                seen.add(u)
                out.append({"url": u, "title": (title or "").strip()})

            # Sometimes grounding metadata is at response-level
            gm_resp = getattr(response, "grounding_metadata", None) or getattr(
                response, "groundingMetadata", None
            )
            candidates = getattr(response, "candidates", None) or []

            def _scan_grounding_metadata(gm: Any) -> None:
                if not gm:
                    return

                # Preferred: grounding_chunks -> web -> (uri/title)
                chunks = getattr(gm, "grounding_chunks", None) or getattr(gm, "groundingChunks", None)
                if chunks:
                    for ch in chunks:
                        web = getattr(ch, "web", None) or getattr(ch, "web", None)
                        if web is None:
                            continue
                        # web can be object or dict-like
                        url = getattr(web, "uri", None) or getattr(web, "url", None)
                        title = getattr(web, "title", None)
                        if hasattr(web, "get"):
                            url = url or web.get("uri") or web.get("url")
                            title = title or web.get("title")
                        _add(url, title)

                # Fallback: try to find any obvious url fields in known locations
                supports = getattr(gm, "grounding_supports", None) or getattr(gm, "groundingSupports", None)
                if supports:
                    for sup in supports:
                        # Some SDK versions store references to chunk indices; ignore if no direct URL
                        url = getattr(sup, "url", None) or getattr(sup, "uri", None)
                        title = getattr(sup, "title", None)
                        if hasattr(sup, "get"):
                            url = url or sup.get("url") or sup.get("uri")
                            title = title or sup.get("title")
                        _add(url, title)

            if gm_resp:
                _scan_grounding_metadata(gm_resp)

            for cand in candidates:
                gm = getattr(cand, "grounding_metadata", None) or getattr(cand, "groundingMetadata", None)
                if gm:
                    _scan_grounding_metadata(gm)

            return out

        def execute_search():
            print("⏳ Searching and analyzing (this may take 1-2 minutes)...")
            
            try:
                # Try with Google Search grounding first
                google_search_tool = types.Tool(
                    google_search=types.GoogleSearch()
                )
                
                response = client.models.generate_content(
                    model=self.model,
                    contents=full_query,
                    config=types.GenerateContentConfig(
                        temperature=0.5,
                        max_output_tokens=16384,
                        tools=[google_search_tool],
                    ),
                )
                
                # Extract text from response
                result_text = None
                if hasattr(response, 'text') and response.text:
                    result_text = response.text
                elif hasattr(response, 'candidates') and response.candidates:
                    candidate = response.candidates[0]
                    if hasattr(candidate, 'content') and candidate.content:
                        parts = candidate.content.parts
                        if parts:
                            texts = [p.text for p in parts if hasattr(p, 'text') and p.text]
                            if texts:
                                result_text = "".join(texts)
                
                if result_text and len(result_text) > 100:
                    print(f"✓ Search grounding returned {len(result_text)} chars")
                    sources = _extract_sources_from_response(response)
                    return result_text, sources
                    
                # If search grounding returned too little, try without it
                print("⚠️ Search grounding returned minimal results, trying direct generation...")
                
            except Exception as e:
                print(f"⚠️ Search grounding failed: {e}, trying direct generation...")
            
            # Fallback: direct generation without search tool
            print("📝 Running direct research generation...")
            response = client.models.generate_content(
                model=self.model,
                contents=full_query,
                config=types.GenerateContentConfig(
                    temperature=0.5,
                    max_output_tokens=16384,
                ),
            )
            
            if hasattr(response, 'text') and response.text:
                return response.text, []
            elif hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    parts = candidate.content.parts
                    if parts:
                        texts = [p.text for p in parts if hasattr(p, 'text') and p.text]
                        if texts:
                            return "".join(texts), []
            
            return str(response), []
        
        result_text, sources = await loop.run_in_executor(None, execute_search)
        result = result_text + _format_sources_md(sources)
        
        # Ensure result is not empty
        if not result or len(result) < 50:
            result = "[Research returned insufficient data - please check API key and model availability]"
        
        # Log the FULL result
        log_prompt(
            category="research",
            prompt_type="deep_research_result",
            prompt="[See deep_research prompt]",
            metadata={
                "result_length": len(result),
                "model": self.model,
                "sources_count": len(sources) if isinstance(sources, list) else 0,
            },
            response=result,
        )
        
        logger.info("Deep Research complete", result_length=len(result))
        print(f"✅ Research complete! ({len(result)} characters)")
        
        return result

    async def structured_generate(
        self,
        prompt: str,
        schema: dict[str, Any],
        system_prompt: str | None = None,
    ) -> dict[str, Any]:
        """
        Generate structured JSON output.
        
        Args:
            prompt: The prompt
            schema: JSON schema for the expected output
            system_prompt: Optional system instructions
            
        Returns:
            Parsed JSON response
        """
        import json
        import re
        
        # Add schema to prompt
        full_prompt = f"""{prompt}

Output your response as valid JSON matching this schema:
```json
{json.dumps(schema, indent=2)}
```

Respond ONLY with the JSON, no additional text."""

        response = await self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=0.3,  # Lower for structured output
        )
        
        # Extract JSON from response
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response.strip()
        
        return json.loads(json_str)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=5, max=60),
    )
    async def generate_image(
        self,
        prompt: str,
        width: int = 1080,
        height: int = 1920,
        aspect_ratio: str | None = None,
        image_size: str | None = None,
    ) -> bytes:
        """
        Generate an image using Gemini Image model.

        Args:
            prompt: The image generation prompt
            width: Image width (default 1080)
            height: Image height (default 1920)
            aspect_ratio: Optional aspect ratio (e.g., "9:16")
            image_size: Optional size hint (e.g., "4K", "2K", "1K")

        Returns:
            Image bytes (PNG format)
        """
        from google.genai import types
        import base64

        client = self._get_client()
        image_model = settings.gemini_image_model

        logger.info(
            "Starting Gemini image generation",
            model=image_model,
            prompt_length=len(prompt),
            dimensions=f"{width}x{height}" if not image_size else "auto",
            image_size=image_size,
            aspect_ratio=aspect_ratio,
        )
        print(f"🖼️ Generating image with {image_model}...")

        # Log the prompt
        log_prompt(
            category="ad",
            prompt_type="image_generation",
            prompt=prompt,
            metadata={
                "model": image_model,
                "width": width,
                "height": height,
                "aspect_ratio": aspect_ratio,
                "image_size": image_size,
            },
        )

        loop = asyncio.get_event_loop()

        def execute_image_gen():
            # Gemini image generation
            # Note: The exact API may vary based on model capabilities
            image_config = None
            if aspect_ratio or image_size:
                image_config = types.ImageConfig(
                    aspect_ratio=aspect_ratio,
                    image_size=image_size,
                )

            response = client.models.generate_content(
                model=image_model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE"],
                    image_config=image_config,
                ),
            )

            # Extract image from response
            image_bytes = None

            # Check for inline data in parts
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'content') and candidate.content:
                    for part in candidate.content.parts:
                        if hasattr(part, 'inline_data') and part.inline_data:
                            if part.inline_data.data:
                                # Data might be base64 encoded
                                data = part.inline_data.data
                                if isinstance(data, str):
                                    image_bytes = base64.b64decode(data)
                                else:
                                    image_bytes = data
                                break
                        # Some responses may have image in different structure
                        if hasattr(part, 'image') and part.image:
                            if hasattr(part.image, 'data'):
                                image_bytes = part.image.data
                                break

            # Fallback: check response.image or similar
            if not image_bytes and hasattr(response, 'image'):
                if hasattr(response.image, 'data'):
                    image_bytes = response.image.data

            return image_bytes

        image_bytes = await loop.run_in_executor(None, execute_image_gen)

        if not image_bytes:
            raise ValueError("Gemini Image model did not return image data")

        logger.info(
            "Gemini image generation complete",
            model=image_model,
            size_kb=len(image_bytes) / 1024,
        )
        print(f"✅ Image generated ({len(image_bytes) / 1024:.1f} KB)")

        return image_bytes
