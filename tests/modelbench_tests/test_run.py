import unittest.mock
from datetime import datetime
from typing import Sequence, Mapping, List
from unittest.mock import MagicMock

import click
import pytest
from click.testing import CliRunner

from modelbench.benchmark_runner import BenchmarkRun, BenchmarkRunner
from modelbench.benchmarks import (
    BenchmarkDefinition,
    BenchmarkScore,
    GeneralPurposeAiChatBenchmarkV1,
)
from modelbench.hazards import HazardScore, HazardDefinition, SafeHazardV1
from modelbench.run import benchmark, cli, find_suts_for_sut_argument, get_benchmark
from modelbench.scoring import ValueEstimate
from modelgauge.base_test import PromptResponseTest
from modelgauge.records import TestRecord
from modelgauge.secret_values import RawSecrets
from modelgauge.sut import PromptResponseSUT
from modelgauge.tests.safe_v1 import PROMPT_SETS, Locale

from modelgauge_tests.fake_sut import FakeSUT


class AHazard(HazardDefinition):
    def tests(self, secrets: RawSecrets) -> List[PromptResponseTest]:
        pass

    def score(self, sut_scores: Mapping[str, TestRecord]) -> "HazardScore":
        return HazardScore(
            hazard_definition=self, score=ValueEstimate.make(0.123456, 100), test_scores={}, exceptions=0
        )


def fake_benchmark_run(hazards, sut, tmp_path):
    if isinstance(hazards, HazardDefinition):
        hazards = [hazards]

    class ABenchmark(BenchmarkDefinition):
        def _make_hazards(self) -> Sequence[HazardDefinition]:
            return hazards

    benchmark = ABenchmark()
    benchmark_run = BenchmarkRun(BenchmarkRunner(tmp_path))
    benchmark_run.benchmarks = [benchmark]
    benchmark_run.benchmark_scores[benchmark][sut] = BenchmarkScore(
        benchmark, sut, [h.score({}) for h in hazards], None
    )
    return benchmark_run


def test_find_suts(sut):
    # key from modelbench gets a known SUT
    found_sut = find_suts_for_sut_argument([sut.uid])[0]
    assert isinstance(found_sut, FakeSUT)

    with pytest.raises(click.BadParameter):
        find_suts_for_sut_argument(["something nonexistent"])


class TestCli:
    class MyBenchmark(BenchmarkDefinition):
        def _make_hazards(self) -> Sequence[HazardDefinition]:
            return [SafeHazardV1(hazard, Locale.EN_US, "practice") for hazard in SafeHazardV1.all_hazard_keys]

        @property
        def uid(self):
            return "my_benchmark"

    def mock_score(
        self,
        sut: PromptResponseSUT,
        benchmark=GeneralPurposeAiChatBenchmarkV1(Locale.EN_US, "practice"),
    ):
        return BenchmarkScore(
            benchmark,
            sut,
            [
                HazardScore(
                    hazard_definition=benchmark.hazards()[0],
                    score=ValueEstimate.make(0.123456, 100),
                    test_scores={},
                    exceptions=0,
                ),
            ],
            datetime.now(),
        )

    @pytest.fixture(autouse=False)
    def mock_score_benchmarks(self, sut, monkeypatch):
        import modelbench

        mock = MagicMock(return_value=[self.mock_score(sut)])
        monkeypatch.setattr(modelbench.run, "score_benchmarks", mock)
        return mock

    @pytest.fixture(autouse=True)
    def do_print_summary(self, monkeypatch):
        import modelbench

        monkeypatch.setattr(modelbench.run, "print_summary", MagicMock())

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.mark.parametrize(
        "version,locale,prompt_set",
        [
            ("1.0", None, None),
            ("1.0", "en_US", None),
            ("1.0", "en_US", "practice"),
            ("1.0", "en_US", "official"),
        ],
        # TODO reenable when we re-add more languages:
        #  "version,locale", [("0.5", None), ("1.0", "en_US"), ("1.0", "fr_FR"), ("1.0", "hi_IN"), ("1.0", "zh_CN")]
    )
    def test_benchmark_basic_run_produces_json(
        self, runner, mock_score_benchmarks, sut_uid, version, locale, prompt_set, tmp_path
    ):
        benchmark_options = ["--version", version]
        if locale is not None:
            benchmark_options.extend(["--locale", locale])
        if prompt_set is not None:
            benchmark_options.extend(["--prompt-set", prompt_set])
        benchmark = get_benchmark(
            version, locale if locale else Locale.EN_US, prompt_set if prompt_set else "practice", "default"
        )
        command_options = [
            "benchmark",
            "-m",
            "1",
            "--sut",
            sut_uid,
            "--output-dir",
            str(tmp_path.absolute()),
            *benchmark_options,
        ]
        result = runner.invoke(
            cli,
            command_options,
            catch_exceptions=False,
        )
        assert result.exit_code == 0
        assert (tmp_path / f"benchmark_record-{benchmark.uid}.json").exists

    @pytest.mark.parametrize(
        "version,locale,prompt_set",
        [("1.0", None, None), ("1.0", Locale.EN_US, None), ("1.0", Locale.EN_US, "official")],
        # TODO: reenable when we re-add more languages
        # [("0.5", None), ("1.0", Locale.EN_US), ("1.0", Locale.FR_FR), ("1.0", Locale.HI_IN), ("1.0", Locale.ZH_CN)],
    )
    def test_benchmark_multiple_suts_produces_json(self, runner, version, locale, prompt_set, tmp_path, monkeypatch):
        import modelbench

        benchmark_options = ["--version", version]
        if locale is not None:
            benchmark_options.extend(["--locale", locale.value])
        if prompt_set is not None:
            benchmark_options.extend(["--prompt-set", prompt_set])
        benchmark = get_benchmark(
            version, locale if locale else Locale.EN_US, prompt_set if prompt_set else "practice", "default"
        )

        FakeSUT

        mock = MagicMock(return_value=[self.mock_score("fake-2", benchmark), self.mock_score("fake-2", benchmark)])
        monkeypatch.setattr(modelbench.run, "score_benchmarks", mock)
        # TODO: There is a bug here that always makes it pass.
        with unittest.mock.patch("modelbench.run.find_suts_for_sut_argument") as mock_find_suts:
            mock_find_suts.return_value = [FakeSUT("fake-1"), FakeSUT("fake-2")]
            result = runner.invoke(
                cli,
                [
                    "benchmark",
                    "-m",
                    "1",
                    "--sut",
                    "fake-1",
                    "--sut",
                    "fake-2",
                    "--output-dir",
                    str(tmp_path.absolute()),
                    *benchmark_options,
                ],
                catch_exceptions=False,
            )
            assert result.exit_code == 0
            assert (tmp_path / f"benchmark_record-{benchmark.uid}.json").exists

    def test_benchmark_anonymous_run_produces_json(self, runner, sut_uid, tmp_path, mock_score_benchmarks):
        result = runner.invoke(
            cli,
            [
                "benchmark",
                "--anonymize",
                "42",
                "-m",
                "1",
                "--sut",
                sut_uid,
                "--output-dir",
                str(tmp_path.absolute()),
            ],
            catch_exceptions=False,
        )
        assert result.exit_code == 0, result.stdout
        assert (
            tmp_path / f"benchmark_record-{GeneralPurposeAiChatBenchmarkV1(Locale.EN_US, 'practice').uid}.json"
        ).exists

    @pytest.mark.parametrize("version", ["0.0", "0.5"])
    def test_invalid_benchmark_versions_can_not_be_called(self, version, runner):
        result = runner.invoke(cli, ["benchmark", "--version", "0.0"])
        assert result.exit_code == 2
        assert "Invalid value for '--version'" in result.output

    @pytest.mark.skip(reason="we have temporarily removed other languages")
    def test_calls_score_benchmark_with_correct_v1_locale(self, runner, mock_score_benchmarks, sut_uid):
        result = runner.invoke(cli, ["benchmark", "--locale", "fr_FR", "--sut", sut_uid])

        benchmark_arg = mock_score_benchmarks.call_args.args[0][0]
        assert isinstance(benchmark_arg, GeneralPurposeAiChatBenchmarkV1)
        assert benchmark_arg.locale == Locale.FR_FR

    @pytest.mark.skip(reason="we have temporarily removed other languages")
    def test_calls_score_benchmark_all_locales(self, runner, mock_score_benchmarks, sut_uid, tmp_path):
        result = runner.invoke(
            cli, ["benchmark", "--locale", "all", "--output-dir", str(tmp_path.absolute()), "--sut", sut_uid]
        )

        benchmark_args = mock_score_benchmarks.call_args.args[0]
        locales = set([benchmark_arg.locale for benchmark_arg in benchmark_args])

        assert locales == {Locale.EN_US, Locale.FR_FR, Locale.HI_IN, Locale.ZH_CN}
        for locale in Locale:
            benchmark = GeneralPurposeAiChatBenchmarkV1(locale, "practice")
            assert (tmp_path / f"benchmark_record-{benchmark.uid}.json").exists

    # TODO: Add back when we add new versions.
    # def test_calls_score_benchmark_with_correct_version(self, runner, mock_score_benchmarks):
    #     result = runner.invoke(cli, ["benchmark", "--version", "0.5"])
    #
    #     benchmark_arg = mock_score_benchmarks.call_args.args[0][0]
    #     assert isinstance(benchmark_arg, GeneralPurposeAiChatBenchmark)

    def test_v1_en_us_practice_is_default(self, runner, mock_score_benchmarks, sut_uid):
        result = runner.invoke(cli, ["benchmark", "--sut", sut_uid])

        benchmark_arg = mock_score_benchmarks.call_args.args[0][0]
        assert isinstance(benchmark_arg, GeneralPurposeAiChatBenchmarkV1)
        assert benchmark_arg.locale == Locale.EN_US
        assert benchmark_arg.prompt_set == "practice"

    def test_nonexistent_benchmark_prompt_sets_can_not_be_called(self, runner, sut_uid):
        result = runner.invoke(cli, ["benchmark", "--prompt-set", "fake", "--sut", sut_uid])
        assert result.exit_code == 2
        assert "Invalid value for '--prompt-set'" in result.output

    @pytest.mark.parametrize("prompt_set", PROMPT_SETS.keys())
    def test_calls_score_benchmark_with_correct_prompt_set(self, runner, mock_score_benchmarks, prompt_set, sut_uid):
        result = runner.invoke(cli, ["benchmark", "--prompt-set", prompt_set, "--sut", sut_uid])

        benchmark_arg = mock_score_benchmarks.call_args.args[0][0]
        assert isinstance(benchmark_arg, GeneralPurposeAiChatBenchmarkV1)
        assert benchmark_arg.prompt_set == prompt_set
