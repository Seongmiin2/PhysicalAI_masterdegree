from src.data.reinartz import semantic_mapping, split_name


def test_semantic_mapping_and_missing_xmv12() -> None:
    columns = ["run_id", "sample", *[f"xmeas_{i}" for i in range(1, 42)], *[f"xmv_{i}" for i in range(1, 12)]]
    mapping = semantic_mapping(columns)
    assert (mapping.semantic_role == "STATE").sum() == 41
    assert ((mapping.semantic_role == "ACTION_CANDIDATE") & mapping.included).sum() == 11
    missing = mapping[mapping.source_column == "xmv_12"].iloc[0]
    assert not missing.included
    assert missing.mapping_confidence == "CONFIRMED"


def test_run_split_classification() -> None:
    assert split_name({1}, {0}) == "train"
    assert split_name({0}, {1}) == "test"
    assert split_name({0, 1}, {0, 1}) == "LEAKED_BOTH"
