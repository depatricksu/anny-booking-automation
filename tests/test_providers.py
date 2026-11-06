from auth.providers import PROVIDERS, get_provider
from auth.providers.lmu import LMUProvider


def test_lmu_registered():
    assert get_provider("lmu") is LMUProvider
    assert get_provider("LMU") is LMUProvider
    assert "lmu" in PROVIDERS


def test_lmu_domain():
    assert LMUProvider.domain == "lmu.de"
