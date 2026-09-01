"""
Test fixtures and configuration for ManakAI tests.
"""

import pytest
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def pytest_configure(config):
    """Register custom markers so `pytest --strict-markers` doesn't warn/fail."""
    config.addinivalue_line(
        "markers",
        "integration: real-dependency integration test (e.g. downloads/loads "
        "the actual embedding model, or requires a running Qdrant instance). "
        "May be skipped automatically in offline/sandboxed environments."
    )


@pytest.fixture
def sample_text():
    """Sample text for processing."""
    return "LED  Street  Lighting  System\n\nRequirements for outdoor IP65/IP66 rated fixtures."


@pytest.fixture
def sample_product_description():
    """Sample product description."""
    return "Supply of 90W LED Street Lights, suitable for outdoor road lighting, IP66, minimum efficacy 120 lm/W."


@pytest.fixture
def sample_standard_record():
    """Sample standard record."""
    return {
        "standard_id": "TEST-001",
        "standard_number": "TEST-STANDARD-001",
        "title": "LED Street Lighting",
        "scope": "Requirements for LED luminaires used for road and street lighting.",
        "description": "Specifies performance and safety requirements.",
        "sector": "Lighting",
        "status": "Active",
    }


@pytest.fixture
def sample_standards_list():
    """List of sample standards."""
    return [
        {
            "standard_id": "TEST-001",
            "standard_number": "TEST-STANDARD-001",
            "title": "LED Street Lighting",
            "scope": "Requirements for road lighting",
        },
        {
            "standard_id": "TEST-002",
            "standard_number": "TEST-STANDARD-002",
            "title": "Electrical Safety",
            "scope": "Safety requirements for electrical equipment",
        },
        {
            "standard_id": "TEST-003",
            "standard_number": "TEST-STANDARD-003",
            "title": "Concrete Specifications",
            "scope": "Requirements for concrete in construction",
        },
    ]


@pytest.fixture
def hindi_text():
    """Sample text in Hindi."""
    return "सड़क के लिए 90W एलईडी स्ट्रीट लाइट, IP66 रेटेड"


@pytest.fixture
def technical_text():
    """Sample technical text with specifications."""
    return "LED luminaire with efficacy 120 lm/W, IP65 rated, 50Hz, 230V AC"
