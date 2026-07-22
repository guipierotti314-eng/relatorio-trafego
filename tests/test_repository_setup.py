from pathlib import Path


ROOT = Path(__file__).parents[1]


def test_shared_excel_is_explicitly_allowed_by_gitignore() -> None:
    rules = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "*.xlsx" in rules
    assert "!dados/" in rules
    assert "!dados/base_atual.xlsx" in rules
    assert rules.index("!dados/base_atual.xlsx") > rules.index("*.xlsx")


def test_required_excel_dependencies_are_declared() -> None:
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").casefold()
    for package in ("streamlit", "pandas", "openpyxl"):
        assert any(line.startswith(package) for line in requirements.splitlines())


def test_production_code_has_no_manual_base_uploader() -> None:
    application = (ROOT / "app.py").read_text(encoding="utf-8")
    loader = (ROOT / "src" / "data_loader.py").read_text(encoding="utf-8")
    assert "file_uploader" not in application
    assert "uploaded_file" not in application
    assert "BytesIO" not in loader
