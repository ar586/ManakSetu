"""
Tests for text processing utilities.
"""

import pytest
from app.utils import text_processing


class TestCleanText:
    """Tests for clean_text function."""

    def test_clean_whitespace(self, sample_text):
        """Test cleaning excessive whitespace."""
        result = text_processing.clean_text(sample_text)
        assert "  " not in result  # No double spaces
        assert result.count("\n") <= 2  # No excessive line breaks

    def test_preserve_technical_specs(self):
        """Test that technical specs are preserved."""
        text = "IP65/IP66 rated, 90W, 230V, 50Hz, 120 lm/W"
        result = text_processing.clean_text(text)

        assert "IP65" in result
        assert "IP66" in result
        assert "90W" in result
        assert "230V" in result
        assert "50Hz" in result
        assert "120 lm/W" in result

    def test_preserve_standard_numbers(self):
        """Test that standard numbers are preserved."""
        text = "According to IS 302, IEC 60598, and ISO 9001..."
        result = text_processing.clean_text(text)

        assert "IS 302" in result
        assert "IEC 60598" in result
        assert "ISO 9001" in result

    def test_empty_input(self):
        """Test handling of empty input."""
        assert text_processing.clean_text("") == ""
        assert text_processing.clean_text(None) == ""
        assert text_processing.clean_text("   ") == ""

    def test_unicode_normalization(self):
        """Test Unicode normalization."""
        text = "café"  # é can be represented different ways
        result = text_processing.clean_text(text)
        assert len(result) > 0
        assert "caf" in result.lower()

    def test_strip_leading_trailing_whitespace(self):
        """Test stripping of leading/trailing whitespace."""
        text = "   hello world   "
        result = text_processing.clean_text(text)
        assert result == "hello world"


class TestCleanProductDescription:
    """Tests for clean_product_description function."""

    def test_preserve_technical_info(self, sample_product_description):
        """Test preservation of technical specifications in product description."""
        result = text_processing.clean_product_description(sample_product_description)

        assert "90W" in result
        assert "LED" in result
        assert "IP66" in result
        assert "120 lm/W" in result
        assert "outdoor" in result

    def test_remove_junk_words(self):
        """Test removal of junk words from beginning."""
        text = "Please supply 90W LED lights for road use"
        result = text_processing.clean_product_description(text)
        assert "90W" in result
        assert "LED" in result
        assert "road" in result


class TestBuildStandardText:
    """Tests for build_standard_text function."""

    def test_combine_title_scope_description(self, sample_standard_record):
        """Test combining title, scope, and description."""
        result = text_processing.build_standard_text(
            sample_standard_record["title"],
            sample_standard_record["scope"],
            sample_standard_record["description"]
        )

        assert "Title:" in result
        assert "Scope:" in result
        assert "Description:" in result
        assert sample_standard_record["title"] in result
        assert sample_standard_record["scope"] in result
        assert sample_standard_record["description"] in result

    def test_without_description(self):
        """Test with title and scope only."""
        title = "LED Lighting"
        scope = "Requirements for outdoor use"

        result = text_processing.build_standard_text(title, scope)

        assert "Title:" in result
        assert "Scope:" in result
        assert title in result
        assert scope in result
        assert "Description:" not in result

    def test_empty_inputs(self):
        """Test handling of empty inputs."""
        result = text_processing.build_standard_text("", "")
        assert result == ""


class TestChunkText:
    """Tests for chunk_text function."""

    def test_basic_chunking(self):
        """Test basic text chunking."""
        text = "This is a test. " * 50
        chunks = text_processing.chunk_text(text, chunk_size=100, overlap=20)

        assert len(chunks) > 1
        assert all(len(c) >= 50 for c in chunks)  # min_chunk_size=50

    def test_overlap_preservation(self):
        """Test that overlap preserves context."""
        text = "A B C D E F G H I J K L M N O P" * 10
        chunks = text_processing.chunk_text(text, chunk_size=50, overlap=20)

        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            chunk1 = chunks[i]
            chunk2 = chunks[i + 1]
            # Some overlap should exist
            assert chunk1[-30:] in (chunk1 + chunk2) or chunk2[:30] in (chunk1 + chunk2)

    def test_empty_input(self):
        """Test handling of empty input."""
        assert text_processing.chunk_text("") == []
        assert text_processing.chunk_text(None) == []

    def test_short_text(self):
        """Test with text shorter than chunk size."""
        text = "Short text"
        chunks = text_processing.chunk_text(text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_invalid_parameters(self):
        """Test validation of chunk parameters."""
        text = "Test text"

        with pytest.raises(ValueError):
            text_processing.chunk_text(text, chunk_size=0)  # Negative chunk size

        with pytest.raises(ValueError):
            text_processing.chunk_text(text, chunk_size=10, overlap=10)  # overlap >= chunk_size


class TestNormalizeStandardNumber:
    """Tests for normalize_standard_number function."""

    def test_basic_normalization(self):
        """Test basic standard number normalization."""
        assert "IS " in text_processing.normalize_standard_number("is 302")
        assert "IEC " in text_processing.normalize_standard_number("iec 60598")
        assert "ISO " in text_processing.normalize_standard_number("iso 9001")

    def test_preserve_full_number(self):
        """Test preserving full standard number."""
        result = text_processing.normalize_standard_number("IS 302:2013")
        assert "302:2013" in result

    def test_empty_input(self):
        """Test handling of empty input."""
        assert text_processing.normalize_standard_number("") == ""
        assert text_processing.normalize_standard_number(None) == ""


class TestValidateTextForEmbedding:
    """Tests for validate_text_for_embedding function."""

    def test_valid_text(self):
        """Test validation of valid text."""
        is_valid, error = text_processing.validate_text_for_embedding("Valid text")
        assert is_valid is True
        assert error is None

    def test_empty_text(self):
        """Test validation of empty text."""
        is_valid, error = text_processing.validate_text_for_embedding("")
        assert is_valid is False
        assert error is not None

    def test_whitespace_only(self):
        """Test validation of whitespace-only text."""
        is_valid, error = text_processing.validate_text_for_embedding("   \n\t  ")
        assert is_valid is False
        assert error is not None

    def test_invalid_type(self):
        """Test validation of invalid type."""
        is_valid, error = text_processing.validate_text_for_embedding(123)
        assert is_valid is False
        assert error is not None


class TestMultilingualSupport:
    """Tests for multilingual text processing."""

    def test_hindi_text(self, hindi_text):
        """Test cleaning of Hindi text."""
        result = text_processing.clean_text(hindi_text)
        assert len(result) > 0
        assert "90W" in result  # English numbers preserved

    def test_supports_multilingual(self):
        """Test multilingual support flag."""
        assert text_processing.supports_multilingual() is True


class TestMergeTexts:
    """Tests for merge_texts function."""

    def test_merge_multiple_texts(self):
        """Test merging multiple text fragments."""
        texts = ["Hello", "world", "test"]
        result = text_processing.merge_texts(texts)
        assert result == "Hello world test"

    def test_filter_empty_values(self):
        """Test filtering of empty values."""
        texts = ["Hello", "", None, "world"]
        result = text_processing.merge_texts(texts)
        assert result == "Hello world"

    def test_custom_separator(self):
        """Test custom separator."""
        texts = ["Hello", "world"]
        result = text_processing.merge_texts(texts, separator=" | ")
        assert result == "Hello | world"
