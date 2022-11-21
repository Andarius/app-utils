def test_main(capsys):
    from app_utils.__main__ import cli

    cli.run_with_args('-h')
    assert capsys.readouterr().out.rstrip()
