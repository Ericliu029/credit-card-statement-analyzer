from datetime import date

from parsers.chase_parser import ChaseStatementParser


def test_chase_card_product_and_last_four_are_detected():
    text = """
    CHASE
    With Sapphire Preferred, you'll earn points on travel.
    Account Number: XXXX XXXX XXXX 0224
    Statement Date: 05/25/26
    05/22 QATAR AIR 164.00
    """

    transaction = ChaseStatementParser().parse(text)[0]

    assert transaction.card == "Chase Sapphire Preferred (ending 0224)"


def test_transaction_before_january_statement_uses_previous_year():
    text = """
    CHASE
    Statement Date: 01/25/26
    Account Number: XXXX XXXX XXXX 0224
    12/27 IC* INSTACART INSTACART.COM CA 20.86
    01/02 OMNY VENDING NEW YORK NY 2.90
    """

    transactions = ChaseStatementParser().parse(text)

    assert transactions[0].date == date(2025, 12, 27)
    assert transactions[1].date == date(2026, 1, 2)
