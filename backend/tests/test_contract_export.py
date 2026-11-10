from pathlib import Path

import pytest

from ivlia.api.schemas import exports, main

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"


@pytest.mark.parametrize(("name", "text"), exports().items())
def test_versioned_export_is_up_to_date(name: str, text: str) -> None:
    versioned = (SCHEMAS_DIR / name).read_text(encoding="utf-8")

    assert versioned == text, f"schemas/{name} is out of date: run `just contract`"


def test_main_writes_every_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out_dir = tmp_path / "schemas"
    monkeypatch.setattr("sys.argv", ["schemas", str(out_dir)])

    main()

    for name, text in exports().items():
        assert (out_dir / name).read_text(encoding="utf-8") == text
