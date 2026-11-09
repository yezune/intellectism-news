from intellectism_news import cli, pipeline
from intellectism_news.models import Item


def make_item(id: str = "x", title: str = "Layoffs", source: str = "rss:ILO") -> Item:
    return Item(
        id=id,
        field="labor",
        source=source,
        title=title,
        url=f"https://example.com/{id}",
        published="2026-11-09T00:00:00+00:00",
        summary="",
    )


def write_config(root):
    (root / "config").mkdir()
    (root / "config" / "fields.yaml").write_text(
        """timezone: Asia/Seoul
fields:
  labor:
    name: 노동
    question: 누가 일하고, 무엇이 대체되는가
    keywords: {layoffs: 3}
    min_relevance: 2
    sources:
      rss:
        weight: 1.5
        feeds: [{name: ILO, require_keywords: true}]
      arxiv: {weight: 1.0}
    limits: {candidates: 10, max_items: 20, max_per_source: 3}
""",
        encoding="utf-8",
    )


def test_list(tmp_path, capsys):
    write_config(tmp_path)
    assert cli.main(["--root", str(tmp_path), "list"]) == 0
    assert "labor" in capsys.readouterr().out


def test_daily(tmp_path, monkeypatch, capsys):
    write_config(tmp_path)
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: ([make_item()], {}))
    assert (
        cli.main(["--root", str(tmp_path), "daily", "--field", "labor", "--date", "2026-11-10"])
        == 0
    )
    assert "생성됨" in capsys.readouterr().out


def test_check(tmp_path, monkeypatch, capsys):
    write_config(tmp_path)
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: ([make_item()], {}))
    assert (
        cli.main(["--root", str(tmp_path), "daily", "--field", "labor", "--date", "2026-11-10"])
        == 0
    )
    assert (
        cli.main(["--root", str(tmp_path), "check", "--field", "labor", "--date", "2026-11-10"])
        == 0
    )
    assert "OK" in capsys.readouterr().out


def test_check_missing(tmp_path):
    write_config(tmp_path)
    assert (
        cli.main(["--root", str(tmp_path), "check", "--field", "labor", "--date", "2026-11-10"])
        == 1
    )


def test_candidates(tmp_path, monkeypatch, capsys):
    write_config(tmp_path)
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: ([make_item()], {}))
    assert (
        cli.main(["--root", str(tmp_path), "daily", "--field", "labor", "--date", "2026-11-10"])
        == 0
    )
    assert (
        cli.main(
            ["--root", str(tmp_path), "candidates", "--field", "labor", "--date", "2026-11-10"]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert "Layoffs" in out
    assert "score" in out


def test_candidates_json(tmp_path, monkeypatch, capsys):
    write_config(tmp_path)
    monkeypatch.setattr(pipeline, "fetch_all", lambda field, run_date: ([make_item()], {}))
    assert (
        cli.main(["--root", str(tmp_path), "daily", "--field", "labor", "--date", "2026-11-10"])
        == 0
    )
    assert (
        cli.main(
            [
                "--root",
                str(tmp_path),
                "candidates",
                "--field",
                "labor",
                "--date",
                "2026-11-10",
                "--json",
            ]
        )
        == 0
    )
    out = capsys.readouterr().out
    assert '"candidates"' in out
    assert '"id": "x"' in out
