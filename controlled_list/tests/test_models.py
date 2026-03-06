from django.test import TestCase

from controlled_list.models import (
    AccessRight,
    CarrierType,
    IdentifierType,
    Keyword,
    ReproductionRight,
)


class ControlledListModelTests(TestCase):
    def test_str_returns_value(self):
        self.assertEqual(str(AccessRight(statement="Open")), "Open")
        self.assertEqual(str(CarrierType(type="Box", width=10)), "Box")
        self.assertEqual(str(IdentifierType(type="ISBN")), "ISBN")
        self.assertEqual(str(Keyword(keyword="  democracy ")), "democracy")
        self.assertEqual(str(ReproductionRight(statement="Allowed")), "Allowed")
