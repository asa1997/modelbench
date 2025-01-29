import json
import pathlib
from statistics import fmean

from modelgauge.locales import validate_locale


class Standards:

    def __init__(self, path: pathlib.Path):
        self.data = None
        self.path = path
        self.reload()

    def reload(self):
        with open(self.path) as f:
            self.data = json.load(f)["standards"]

    def reference_standard_for(self, name):
        if name not in self.data["reference_standards"]:
            raise ValueError(f"No standard yet for {name}. Run `modelbench calibrate --update` to add one.")
        return self.data["reference_standards"][name]

    def average_standard_across_references(self, locale: str = "", version: str = "1.0") -> float:
        assert version == "1.0", "Only version 1.0 is supported."
        if not locale:
            raise ValueError("Locale is required for v1.0 scoring.")
        locale = locale.lower()
        validate_locale(locale)
        values = [v for k, v in self.data["reference_standards"].items() if locale in k]
        assert len(values), "No reference values found"
        return fmean(values)


STANDARDS = Standards(pathlib.Path(__file__).parent / "standards.json")
