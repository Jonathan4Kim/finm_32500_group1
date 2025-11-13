from fix_parser import FixParser


def test_parse_returns_kv_pairs():
    msg = "8=FIX.4.2|35=D|55=AAPL|54=1|38=100"

    parsed = FixParser.parse(msg)

    assert parsed["8"] == "FIX.4.2"
    assert parsed["55"] == "AAPL"
    assert parsed["38"] == "100"


def test_parse_handles_soh_and_delimiter_choice():
    msg = "8=FIX.4.2\x0135=D\x0155=MSFT"

    parsed = FixParser.parse(msg, delimiter="|")

    assert parsed == {"8": "FIX.4.2", "35": "D", "55": "MSFT"}


def test_parse_ignores_invalid_fields_and_empty_messages():
    assert FixParser.parse("") == {}

    msg = "8=FIX.4.2|BADFIELD|55=TSLA"
    parsed = FixParser.parse(msg)

    assert "BADFIELD" not in parsed
