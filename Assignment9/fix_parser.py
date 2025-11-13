# fix_parser.py
class FixParser:
    @staticmethod
    def parse(msg: str, delimiter: str = "|") -> dict:
        if not msg:
            return {}

        msg = msg.strip()
        # Replace SOH if present with the chosen delimiter for safety
        msg = msg.replace("\x01", delimiter)

        fields = msg.split(delimiter)
        parsed = {}

        for field in fields:
            if "=" not in field:
                continue
            tag, value = field.split("=", 1)
            parsed[tag.strip()] = value.strip()

        return parsed


if __name__ == "__main__":
    msg = "8=FIX.4.2|35=D|55=AAPL|54=1|38=100|40=2|10=128"
    print(FixParser.parse(msg))