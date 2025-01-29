from modelbench.hazards import STANDARDS, SafeHazardV1
from modelgauge.locales import EN_US


def test_existing_standard():
    assert STANDARDS.reference_standard_for(SafeHazardV1("dfm", EN_US, "practice").uid) is not None
    assert STANDARDS.reference_standard_for(SafeHazardV1("dfm", EN_US, "official").uid) is not None
    assert SafeHazardV1("dfm", EN_US, "practice").reference_standard() is not None
    assert SafeHazardV1("dfm", EN_US, "official").reference_standard() is not None
