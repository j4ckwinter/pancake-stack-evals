def read_total(payload):
    if not isinstance(payload, dict) or set(payload) != {"version", "invoice"}:
        raise ValueError("invalid envelope")
    version = payload["version"]
    if type(version) is not int:
        raise ValueError("version must be an integer")
    if version not in (1, 2):
        raise ValueError("unsupported version")
    field = "total" if version == 1 else "amount"
    invoice = payload["invoice"]
    if not isinstance(invoice, dict) or set(invoice) != {field}:
        raise ValueError("invalid invoice fields")
    amount = invoice[field]
    if type(amount) not in (int, float) or amount < 0:
        raise ValueError("invalid amount")
    return amount
