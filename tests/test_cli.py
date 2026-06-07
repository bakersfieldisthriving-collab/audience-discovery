from audience_discovery.main import main, run, build_parser


def test_cli_dry_run_exports(tmp_path, capsys) -> None:
    db_path = tmp_path / "leads.sqlite"
    output_dir = tmp_path / "outputs"

    main(["--dry-run", "--limit", "3", "--db-path", str(db_path), "--output-dir", str(output_dir)])

    captured = capsys.readouterr()
    assert "3 stored" in captured.out
    assert (output_dir / "leads_raw.csv").exists()
    assert (output_dir / "leads_scored.csv").exists()
    assert (output_dir / "leads_review_queue.csv").exists()


def test_run_export_only(tmp_path) -> None:
    args = build_parser().parse_args(["--export-only", "--db-path", str(tmp_path / "empty.sqlite"), "--output-dir", str(tmp_path)])

    counts = run(args)

    assert counts["total_leads"] == 0
