from producer import create_invoice


def invoice_for_order(total):
    return create_invoice(total=total)
