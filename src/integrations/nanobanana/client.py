"""
Nano Banana Pro client for KonseptiKeiju.

Nano Banana Pro is Gemini's native image generation capability
(gemini-3-pro-image-preview). This client is a thin wrapper over
Gemini image generation to keep the pipeline naming consistent.
"""

from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.logger import get_logger

logger = get_logger(__name__)


class NanoBananaClient:
    """
    Client for Nano Banana Pro (Gemini Image) generation.
    """

    def __init__(self):
        pass

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def generate_image(
        self,
        prompt: str,
        width: int = 1080,
        height: int = 1920,
        style: str = "professional",
    ) -> bytes:
        """
        Generate an image from a prompt using Gemini Image (Nano Banana Pro).
        """
        from src.integrations.gemini import GeminiClient
        from math import isfinite

        logger.info(
            "Generating image",
            width=width,
            height=height,
            prompt_length=len(prompt),
        )

        # Derive a reasonable aspect ratio hint if possible
        aspect_ratio = None
        try:
            ratio = width / height
            if isfinite(ratio):
                if abs(ratio - (9 / 16)) < 0.05:
                    aspect_ratio = "9:16"
                elif abs(ratio - (3 / 4)) < 0.05:
                    aspect_ratio = "3:4"
                elif abs(ratio - (16 / 9)) < 0.05:
                    aspect_ratio = "16:9"
        except Exception:
            aspect_ratio = None

        client = GeminiClient()
        image_bytes = await client.generate_image(
            prompt=prompt,
            aspect_ratio=aspect_ratio,
            image_size="4K",
        )
        
        logger.info(
            "Image generated",
            size_kb=len(image_bytes) / 1024,
        )
        
        return image_bytes

    async def generate_variants(
        self,
        prompt: str,
        count: int = 3,
        **kwargs,
    ) -> list[bytes]:
        """
        Generate multiple image variants.
        
        Args:
            prompt: Image generation prompt
            count: Number of variants to generate
            **kwargs: Additional parameters for generate_image
            
        Returns:
            List of image bytes
        """
        import asyncio
        
        tasks = [
            self.generate_image(prompt, **kwargs)
            for _ in range(count)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out failures
        images = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.warning(f"Variant {i + 1} failed: {result}")
            else:
                images.append(result)
        
        if not images:
            raise RuntimeError("All variant generations failed")
        
        return images
