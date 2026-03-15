"""Tests for dataset build pipeline."""

from __future__ import annotations

from src.data.build_dataset import (
    _MAX_TOTAL_CHARS,
    _estimate_too_long,
    _samples_to_dataset_dict,
    _validate_samples,
)
from src.data.dataset_generator import Sample
from src.constants import SYSTEM_PROMPT


def _make_sample(sample_type: str = "A", question: str = "Q", answer: str = "A") -> Sample:
    """Helper to create a valid sample."""
    return Sample(
        sample_type=sample_type,
        messages=(
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ),
    )


class TestValidateSamples:
    """Tests for sample validation."""

    def test_valid_samples_pass(self, capsys):
        samples = [_make_sample() for _ in range(5)]
        _validate_samples(samples)
        captured = capsys.readouterr()
        assert "格式驗證通過" in captured.out

    def test_empty_content_detected(self, capsys):
        bad_sample = Sample(
            sample_type="A",
            messages=(
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": ""},
                {"role": "assistant", "content": "answer"},
            ),
        )
        _validate_samples([bad_sample])
        captured = capsys.readouterr()
        assert "空白內容" in captured.out


class TestSamplesToDatasetDict:
    """Tests for converting samples to HuggingFace DatasetDict."""

    def test_split_sizes(self):
        samples = [_make_sample(question=f"Q{i}", answer=f"A{i}") for i in range(100)]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.1, seed=42)

        assert "train" in ds_dict
        assert "test" in ds_dict
        assert len(ds_dict["train"]) == 90
        assert len(ds_dict["test"]) == 10

    def test_messages_format(self):
        samples = [_make_sample(question=f"Q{i}", answer=f"A{i}") for i in range(10)]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.2, seed=42)

        row = ds_dict["train"][0]
        messages = row["messages"]
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

    def test_messages_are_list_not_string(self):
        """Messages should be stored as native list, not JSON string."""
        samples = [_make_sample(question=f"Q{i}", answer=f"A{i}") for i in range(10)]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.2, seed=42)

        row = ds_dict["train"][0]
        assert isinstance(row["messages"], list), (
            f"Expected list, got {type(row['messages'])}"
        )

    def test_sample_type_preserved(self):
        samples = [_make_sample(sample_type="B", question=f"Q{i}", answer=f"A{i}") for i in range(10)]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.2, seed=42)

        row = ds_dict["train"][0]
        assert row["sample_type"] == "B"


class TestSerializationRoundTrip:
    """Tests for dataset serialization round-trip integrity."""

    def test_messages_survive_save_load_cycle(self, tmp_path):
        """Messages should remain as list of dicts after save/load."""
        from datasets import DatasetDict

        samples = [_make_sample(question=f"Q{i}", answer=f"A{i}") for i in range(20)]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.2, seed=42)

        # Save to disk
        save_path = tmp_path / "test_dataset"
        ds_dict.save_to_disk(str(save_path))

        # Load from disk
        loaded = DatasetDict.load_from_disk(str(save_path))

        # Verify messages are still lists of dicts
        for split_name in ("train", "test"):
            for row in loaded[split_name]:
                msgs = row["messages"]
                assert isinstance(msgs, list), (
                    f"Expected list, got {type(msgs)} in {split_name}"
                )
                assert len(msgs) == 3
                for msg in msgs:
                    assert isinstance(msg, dict), (
                        f"Expected dict, got {type(msg)} in {split_name}"
                    )
                    assert "role" in msg
                    assert "content" in msg

    def test_content_preserved_after_round_trip(self, tmp_path):
        """Verify actual content is preserved through save/load."""
        from datasets import DatasetDict

        samples = [
            _make_sample(question=f"特殊問題{i}", answer=f"特殊回答{i}")
            for i in range(10)
        ]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.2, seed=42)

        save_path = tmp_path / "test_dataset"
        ds_dict.save_to_disk(str(save_path))
        loaded = DatasetDict.load_from_disk(str(save_path))

        # Find our test content in the loaded dataset
        found = False
        for split_name in ("train", "test"):
            for row in loaded[split_name]:
                if "特殊問題" in row["messages"][1]["content"]:
                    assert "特殊回答" in row["messages"][2]["content"]
                    found = True
                    break
            if found:
                break
        assert found, "Content not preserved after round-trip"


class TestDeduplication:
    """Tests for v7 question deduplication in build pipeline."""

    def test_dedup_removes_exact_duplicates(self):
        """Duplicate questions should be removed, keeping first occurrence."""
        samples = [
            _make_sample(question="相同問題", answer="回答1"),
            _make_sample(question="相同問題", answer="回答2"),
            _make_sample(question="不同問題", answer="回答3"),
        ]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.5, seed=42)
        total = len(ds_dict["train"]) + len(ds_dict["test"])
        assert total == 2, f"Expected 2 after dedup, got {total}"

    def test_no_train_test_question_overlap(self):
        """No question should appear in both train and test sets."""
        samples = [
            _make_sample(question=f"問題{i}", answer=f"回答{i}")
            for i in range(100)
        ]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.1, seed=42)

        train_questions = {
            row["messages"][1]["content"] for row in ds_dict["train"]
        }
        test_questions = {
            row["messages"][1]["content"] for row in ds_dict["test"]
        }
        overlap = train_questions & test_questions
        assert len(overlap) == 0, (
            f"Found {len(overlap)} overlapping questions between train/test"
        )


class TestTokenLengthFilter:
    """Tests for v8 overly long sample filtering."""

    def test_short_sample_passes(self):
        """A short sample should not be filtered."""
        sample = _make_sample(question="短問題", answer="短回答")
        assert not _estimate_too_long(sample)

    def test_long_sample_filtered(self):
        """A sample exceeding _MAX_TOTAL_CHARS should be detected."""
        long_answer = "很長的回答。" * 450
        sample = _make_sample(question="問題", answer=long_answer)
        assert _estimate_too_long(sample)

    def test_long_sample_excluded_from_dataset(self):
        """Overly long samples should be excluded from the final dataset."""
        long_answer = "超長" * 1500
        normal_samples = [
            _make_sample(question=f"正常問題{i}", answer=f"正常回答{i}")
            for i in range(10)
        ]
        long_sample = _make_sample(question="超長問題", answer=long_answer)
        samples = normal_samples + [long_sample]
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.1, seed=42)
        total = len(ds_dict["train"]) + len(ds_dict["test"])
        assert total == 10, f"Expected 10 after filtering, got {total}"


class TestStratifiedSplit:
    """Tests for v9 stratified train/test split."""

    def test_type_ratio_consistency(self):
        """Train and test sets should have similar type distributions."""
        from collections import Counter

        samples = (
            [_make_sample(sample_type="A", question=f"AQ{i}", answer=f"AA{i}") for i in range(60)]
            + [_make_sample(sample_type="B", question=f"BQ{i}", answer=f"BA{i}") for i in range(20)]
            + [_make_sample(sample_type="F", question=f"FQ{i}", answer=f"FA{i}") for i in range(20)]
        )
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.1, seed=42)

        train_types = Counter(row["sample_type"] for row in ds_dict["train"])
        test_types = Counter(row["sample_type"] for row in ds_dict["test"])

        # All types should be present in both splits
        assert set(train_types.keys()) == set(test_types.keys()), (
            f"Type mismatch: train={set(train_types.keys())}, test={set(test_types.keys())}"
        )

        # Type A ratio in train and test should be within 5% of each other
        train_total = sum(train_types.values())
        test_total = sum(test_types.values())
        for sample_type in train_types:
            train_ratio = train_types[sample_type] / train_total
            test_ratio = test_types[sample_type] / test_total
            assert abs(train_ratio - test_ratio) < 0.05, (
                f"Type {sample_type} ratio diverges: train={train_ratio:.2%}, test={test_ratio:.2%}"
            )

    def test_stratified_preserves_total(self):
        """Stratified split should preserve total sample count."""
        samples = (
            [_make_sample(sample_type="A", question=f"AQ{i}", answer=f"AA{i}") for i in range(50)]
            + [_make_sample(sample_type="C", question=f"CQ{i}", answer=f"CA{i}") for i in range(30)]
            + [_make_sample(sample_type="E", question=f"EQ{i}", answer=f"EA{i}") for i in range(20)]
        )
        ds_dict = _samples_to_dataset_dict(samples, test_size=0.1, seed=42)
        total = len(ds_dict["train"]) + len(ds_dict["test"])
        assert total == 100, f"Expected 100, got {total}"
