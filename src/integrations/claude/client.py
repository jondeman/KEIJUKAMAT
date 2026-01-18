"""
Claude API client for KonseptiKeiju.

Provides wrapper for Anthropic's Claude API with support for:
- Standard generation
- Extended thinking for complex creative tasks
- Retry logic and error handling
"""

from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.config import settings
from src.core.logger import get_logger

logger = get_logger(__name__)


class ClaudeClient:
    """
    Client for Anthropic Claude API.
    
    Handles authentication, request formatting, and response parsing.
    Uses Claude for creative concept generation tasks.
    """

    def __init__(self):
        self.api_key = settings.anthropic_api_key
        self.model = settings.claude_model
        self._client = None

    def _get_client(self):
        """Get or create the Anthropic client."""
        if self._client is None:
            import anthropic
            self._client = anthropic.AsyncAnthropic(api_key=self.api_key)
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
    )
    async def generate(
        self,
        prompt: str,
        system: str | None = None,
        temperature: float = 0.8,
        max_tokens: int = 8192,
    ) -> str:
        """
        Generate a response from Claude.
        
        Args:
            prompt: The user prompt
            system: Optional system instructions
            temperature: Creativity setting (0-1)
            max_tokens: Maximum response length
            
        Returns:
            Generated text response
        """
        client = self._get_client()
        
        logger.debug(
            "Claude generate request",
            model=self.model,
            prompt_length=len(prompt),
        )
        
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        
        # Add temperature if not using extended thinking
        # (extended thinking requires temperature=1)
        kwargs["temperature"] = temperature
        
        if system:
            kwargs["system"] = system
        
        response = await client.messages.create(**kwargs)
        
        # Extract text from response
        result = ""
        for block in response.content:
            if hasattr(block, "text"):
                result += block.text
        
        logger.info(
            "Claude generate complete",
            model=self.model,
            response_length=len(result),
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        
        return result

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=5, max=60),
    )
    async def creative_generate(
        self,
        prompt: str,
        system: str | None = None,
    ) -> str:
        """
        Generate creative content with extended thinking.
        
        This method uses Claude's extended thinking capability
        for more thoughtful, creative outputs.
        
        Args:
            prompt: The creative prompt
            system: Optional system instructions
            
        Returns:
            Generated creative content
        """
        logger.info("Starting creative generation with extended thinking")
        
        # Creative tasks benefit from higher temperature
        result = await self.generate(
            prompt=prompt,
            system=system,
            temperature=0.9,
            max_tokens=16384,
        )
        
        return result

    async def self_critique(
        self,
        content: str,
        criteria: list[str],
    ) -> tuple[bool, list[str]]:
        """
        Have Claude critique content against criteria.
        
        Args:
            content: The content to critique
            criteria: List of criteria to check against
            
        Returns:
            Tuple of (passes_all, list_of_issues)
        """
        criteria_text = "\n".join(f"- {c}" for c in criteria)
        
        prompt = f"""Please critique the following content against these criteria:

{criteria_text}

CONTENT:
{content}

For each criterion, indicate PASS or FAIL with a brief explanation.
At the end, provide a summary: OVERALL_PASS or OVERALL_FAIL.

Format your response as:
CRITERION 1: [PASS/FAIL] - [explanation]
CRITERION 2: [PASS/FAIL] - [explanation]
...
OVERALL: [PASS/FAIL]
ISSUES: [list any issues that need addressing]
"""
        
        response = await self.generate(
            prompt=prompt,
            temperature=0.3,  # Lower for analytical task
            max_tokens=2048,
        )
        
        # Parse response
        passes = "OVERALL: PASS" in response.upper() or "OVERALL_PASS" in response.upper()
        
        issues = []
        if "ISSUES:" in response:
            issues_section = response.split("ISSUES:")[-1].strip()
            issues = [
                line.strip().lstrip("- ")
                for line in issues_section.split("\n")
                if line.strip() and line.strip() != "None"
            ]
        
        # Also extract FAIL items
        for line in response.split("\n"):
            if "FAIL" in line.upper() and "OVERALL" not in line.upper():
                issues.append(line.strip())
        
        return passes, issues
