#!/usr/bin/env python3
"""
Test registration wizard UI improvements
"""
import unittest
from setup.registration_wizard import RegistrationWizard


class RegistrationWizardUITest(unittest.TestCase):
    """Test registration wizard UI"""

    def test_wizard_creation(self):
        """Test that wizard can be created"""
        wizard = RegistrationWizard()
        self.assertIsNotNone(wizard)
        self.assertIsNone(wizard.registration_data)

    def test_css_includes_improvements(self):
        """Test that CSS includes UI improvements"""
        wizard = RegistrationWizard()
        css = wizard.CSS

        # Check for status styling
        self.assertIn("#status", css)
        self.assertIn("min-height", css)

        # Check for result_area hiding
        self.assertIn("#result_area", css)
        self.assertIn("display: none", css)

        # Check for visible class
        self.assertIn(".visible", css)
        self.assertIn("display: block", css)


if __name__ == "__main__":
    unittest.main()
