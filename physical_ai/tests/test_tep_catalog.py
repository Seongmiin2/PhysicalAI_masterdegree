from src.data.catalog_tep import DOCUMENT_PATTERN


def test_document_pattern_is_conservative() -> None:
    assert DOCUMENT_PATTERN.search("README.md")
    assert DOCUMENT_PATTERN.search("variable_metadata.csv")
    assert not DOCUMENT_PATTERN.search("fault_01_mode_1.zip")
