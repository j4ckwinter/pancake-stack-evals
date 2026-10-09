New invoices must be exactly {"version": 2, "invoice": {"amount": value}}.
The public create_invoice(total=...) parameter and invoice_for_order(total=...)
remain supported, including positional calls. Values are nonnegative numbers.
The live consumer reads only v2 invoices. The archive reader reads explicit v1
and v2 envelopes. Persisted archives must not be rewritten.
A v1 envelope is exactly {"version": 1, "invoice": {"total": value}}.
Version values must be integers, excluding booleans.
Both readers must reject unknown or missing versions, missing invoice objects,
missing or conflicting amount/total fields, extra envelope or invoice fields,
non-dictionary envelopes or invoice objects, and negative or nonnumeric values
(including booleans). Reject malformed records with ValueError. A live read of
v1 also raises ValueError. Zero is valid. There is no unversioned fallback.
Keep unrelated files unchanged. Existing passing coverage must remain useful.
