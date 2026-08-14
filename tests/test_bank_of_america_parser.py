from datetime import date

from parsers import select_parser
from parsers.bank_of_america_parser import BankOfAmericaStatementParser


BOA_TEXT = """
BANK OF AMERICA
Visa Signature
Account # 4400 6666 0468 5541
Statement Closing Date 07/08/2026
Purchases and Adjustments
06/18 06/19 BOIST INVE* AD3KFRZ0H REDMOND WA 7132 5541 -59.00
07/04 07/04 ONLINE/MOBILE RECURRING FROM CHK 9182 2725 5541 -6.98
06/15 06/16 BOIST INVE* AD3KFRZ0H BOIST.ORG WA 0284 5541 59.00
06/15 06/16 BOIST INVE* 2ESSW22J0 BOIST.ORG WA 9082 5541 5.99
07/01 07/02 APPLE.COM/BILL 866-712-7753 CA 7775 5541 7.61
07/05 07/06 APPLE.COM/BILL 866-712-7753 CA 6132 5541 0.99
07/08 07/08 INTEREST CHARGED ON PURCHASES 0.00
"""


def test_bank_of_america_is_selected_before_generic_parser():
    parser = select_parser(BOA_TEXT)

    assert isinstance(parser, BankOfAmericaStatementParser)


def test_bank_of_america_columns_and_card_are_parsed():
    transactions = BankOfAmericaStatementParser().parse(BOA_TEXT)

    assert len(transactions) == 6
    assert transactions[0].date == date(2026, 6, 18)
    assert transactions[0].merchant == "BOIST INVE* AD3KFRZ0H REDMOND WA"
    assert transactions[0].amount == -59.0
    assert transactions[0].card == "Bank of America Visa Signature (ending 5541)"
    assert transactions[1].category == "Payments & Credits"
    assert transactions[2].amount == 59.0
    assert transactions[-1].merchant == "APPLE.COM/BILL 866-712-7753 CA"


def test_word_purchases_alone_does_not_select_chase():
    parser = select_parser("PURCHASES AND ADJUSTMENTS")

    assert parser.issuer_name == "Generic"
