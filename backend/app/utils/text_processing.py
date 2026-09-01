"""
Text processing utilities for standard descriptions and product specifications.

Handles cleaning, normalization, and preprocessing of technical documentation
while preserving domain-specific information (standard numbers, technical specs, units).
"""

import re
import unicodedata
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize text while preserving technical information.

    Handles:
    - Repeated whitespace
    - Unnecessary line breaks
    - Unicode normalization
    - PDF extraction artifacts
    - Repeated punctuation

    Preserves:
    - Standard numbers (IS, IEC, ISO)
    - Technical specifications (IP65, 90W, 230V, 50Hz, 120 lm/W)
    - Units and measurements

    Args:
        text: Raw text input

    Returns:
        Cleaned text
    """
    if not text or not isinstance(text, str):
        return ""

    # Unicode normalization (NFKD keeps formatting, NFC is more aggressive)
    text = unicodedata.normalize("NFKD", text)

    # Remove common PDF artifacts and control characters
    text = re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", text)

    # Remove excessive spaces (but keep single space)
    text = re.sub(r" +", " ", text)

    # Remove excessive line breaks (keep max 2 consecutive)
    text = re.sub(r"\n\n+", "\n\n", text)

    # Remove excessive punctuation (but keep technical notation like IP-65)
    # Don't remove hyphens in specifications
    text = re.sub(r"\.{2,}", ".", text)  # Remove multiple dots
    text = re.sub(r"!{2,}", "!", text)   # Remove multiple exclamations
    text = re.sub(r"\?{2,}", "?", text)  # Remove multiple question marks

    # Fix spacing around punctuation
    text = re.sub(r"\s+([.,!?;:])", r"\1", text)
    text = re.sub(r"([.,!?;:])\s+", r"\1 ", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text


def clean_product_description(text: str) -> str:
    """
    Clean product/procurement descriptions while preserving technical details.

    For product specifications like:
    "Supply of 90W LED Street Lights, suitable for outdoor road lighting, IP66, minimum efficacy 120 lm/W."

    Preserves all technical information while normalizing format.

    Args:
        text: Product description text

    Returns:
        Cleaned product description
    """
    # Start with general cleaning
    text = clean_text(text)

    # Normalize common abbreviations consistently but don't remove them
    # Example: LED should stay as LED, not be lowercased

    # Remove common junk words from beginning/end that don't add meaning
    # but be careful not to remove technical content
    junk_patterns = [
        r"^(please|kindly|request|note|remark)[\s:,]*",  # Start with junk
        r"[\s:,]*(please|kindly|request|note|remark)$",  # End with junk
    ]

    for pattern in junk_patterns:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    text = text.strip()
    return text


def build_standard_text(
    title: str,
    scope: str,
    description: Optional[str] = None,
) -> str:
    """
    Build embedding text from standard metadata.

    Combines title, scope, and optional description for semantic embedding.
    This is the text that gets embedded into Qdrant.

    Args:
        title: Standard title
        scope: Scope of applicability
        description: Optional detailed description

    Returns:
        Combined text ready for embedding
    """
    parts = []

    if title and isinstance(title, str):
        parts.append(f"Title: {clean_text(title)}")

    if scope and isinstance(scope, str):
        parts.append(f"Scope: {clean_text(scope)}")

    if description and isinstance(description, str):
        parts.append(f"Description: {clean_text(description)}")

    # Combine with newlines for structure
    result = "\n".join(parts)

    return result.strip()


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 50,
    min_chunk_size: int = 50,
) -> List[str]:
    """
    Split text into overlapping chunks for processing.

    Useful for:
    - Long documents that exceed embedding context
    - Future PDF text processing
    - Preserving context through overlap

    Args:
        text: Text to chunk
        chunk_size: Target characters per chunk
        overlap: Characters to overlap between chunks
        min_chunk_size: Minimum chunk size to return

    Returns:
        List of text chunks
    """
    if not text or not isinstance(text, str):
        return []

    text = text.strip()
    if not text:
        return []

    # Validate parameters
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if overlap < 0:
        raise ValueError("overlap cannot be negative")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    if min_chunk_size < 0:
        raise ValueError("min_chunk_size cannot be negative")

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = min(start + chunk_size, text_length)

        # Extract chunk
        chunk = text[start:end]

        # Only include if meets minimum size
        if len(chunk) >= min_chunk_size:
            chunks.append(chunk)

        # Move start position (stride is chunk_size - overlap)
        stride = chunk_size - overlap
        start += stride

        # Avoid infinite loop with very small chunk_size
        if stride <= 0:
            break

    # Handle case where text is shorter than chunk_size
    if not chunks and text:
        chunks.append(text)

    return chunks


def normalize_standard_number(standard_number: str) -> str:
    """
    Normalize standard number format for consistency.

    Examples:
        "IS 302" -> "IS 302"
        "IS 302:2013" -> "IS 302:2013"
        "IEC 60598-2-3" -> "IEC 60598-2-3"

    Args:
        standard_number: Standard number string

    Returns:
        Normalized standard number
    """
    if not standard_number or not isinstance(standard_number, str):
        return ""

    # Clean whitespace
    number = re.sub(r"\s+", " ", standard_number.strip())

    # Uppercase standard prefix (IS, IEC, ISO, etc.)
    number = re.sub(
        r"^(is|iec|iso|en|din|bs)\s+",
        lambda m: m.group(1).upper() + " ",
        number,
        flags=re.IGNORECASE
    )

    return number


def validate_text_for_embedding(text: str) -> tuple[bool, Optional[str]]:
    """
    Validate text before embedding.

    Args:
        text: Text to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not text:
        return False, "Text cannot be empty"

    if not isinstance(text, str):
        return False, f"Text must be string, got {type(text).__name__}"

    if text.strip() == "":
        return False, "Text cannot be whitespace-only"

    # Text is valid
    return True, None


def merge_texts(texts: List[str], separator: str = " ") -> str:
    """
    Merge multiple text fragments into single text.

    Useful for combining title, scope, description before embedding.

    Args:
        texts: List of text fragments
        separator: Text to join with

    Returns:
        Merged text
    """
    if not texts:
        return ""

    # Filter out empty/None values
    valid_texts = [t for t in texts if t and isinstance(t, str)]

    return separator.join(valid_texts)


# Multilingual support examples (no translation, just documentation)
MULTILINGUAL_EXAMPLES = {
    "hindi": "सड़क के लिए 90W एलईडी स्ट्रीट लाइट",
    "tamil": "சாலை விளக்குகளுக்கான 90W LED தெருக்களை",
    "english": "90W LED street light for road lighting",
}


def supports_multilingual() -> bool:
    """
    Check if system supports multilingual text processing.

    Currently the embedding model (sentence-transformers multilingual) supports this.

    Returns:
        True if multilingual input is supported
    """
    return True


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test text cleaning
    sample_text = """
    LED  Street  Lighting   System

    Requirements for LED luminaires used for road and street lighting.
    Suitable for outdoor applications with IP65/IP66 rating.
    """

    print("Original:")
    print(repr(sample_text))
    print("\nCleaned:")
    print(repr(clean_text(sample_text)))

    # Test product description
    product = "Supply of 90W LED Street Lights, IP66, efficacy 120 lm/W"
    print("\nProduct description:")
    print(repr(clean_product_description(product)))

    # Test standard text building
    title = "LED Street Lighting"
    scope = "Requirements for road lighting"
    description = "Performance and safety specifications"

    combined = build_standard_text(title, scope, description)
    print("\nCombined standard text:")
    print(combined)

    # Test chunking
    long_text = "This is a test. " * 50
    chunks = chunk_text(long_text, chunk_size=100, overlap=20)
    print(f"\nText chunked into {len(chunks)} pieces")
