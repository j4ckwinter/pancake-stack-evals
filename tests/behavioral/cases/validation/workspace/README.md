# Invoice reader

`reader.read_total(payload)` returns a nonnegative numeric invoice total.
The envelope has exactly `version` and `invoice` fields. Version must have the
exact Python integer type: booleans and floats are invalid, even when numerically
equal to a supported version. Version 1 uses exactly `invoice.total`; version 2
uses exactly `invoice.amount`. Malformed input raises `ValueError`; error messages
are not part of the contract. Run `python3 -B -m unittest discover -v`.
