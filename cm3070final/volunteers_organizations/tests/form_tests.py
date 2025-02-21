from django.test import TestCase
from accounts_notifs.models import Account
from ..models import Volunteer, Organization
from ..forms import VolunteerForm, OrganizationForm
from datetime import date
import json

class TestVolunteerForm(TestCase):
    def setUp(self):
        self.account = Account.objects.create(
            email_address="volunteer@gmail.com",
            password="securePassword1!",
            user_type="volunteer",
            contact_number="+35612345678"
        )
        self.valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "dob": date(1990,1,1),
            "bio": "I love volunteering",
            "profile_img": None
        }

    def test_form_valid_with_correct_data(self):
        form = VolunteerForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_with_missing_first_name(self):
        self.valid_data.pop('first_name')
        form = VolunteerForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_form_invalid_with_invalid_dob(self):
        self.valid_data['dob'] = date(2026,1,1)
        form = VolunteerForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('dob', form.errors)
        self.assertEqual(form.errors['dob'], ['Invalid Date of Birth'])
    
    def test_form_save_creates_volunteer(self):
        form=VolunteerForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        volunteer=form.save(account=self.account)
        self.assertEqual(volunteer.first_name, self.valid_data["first_name"])
        self.assertEqual(volunteer.account, self.account)

class TestOrganizationForm(TestCase):
    def setUp(self):
        self.account=Account.objects.create(
            email_address="organization@gmail.com",
            password="securePassword1!",
            user_type="organization",
            contact_number="+35612345678"
        )
        self.valid_data = {
            "organization_name": "Test Organization",
            "organization_description": "We are a test organization",
            "street_number": "123",
            "route": "Test Street",
            "locality": "Test City",
            "postal_code": "ABC123",
            "state": "Test State",
            "country": "Test Country",
            "organization_website": "https://testorg.com",
            "organization_profile_img": None
        }

    def test_form_valid_with_correct_data(self):
        form=OrganizationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_with_missing_organization_name(self):
        self.valid_data.pop('organization_name')
        form=OrganizationForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('organization_name', form.errors)

    def test_form_saves_address_correctly(self):
        form = OrganizationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        organization = form.save(account=self.account)
        self.assertEqual(
            organization.organization_address['raw'],
            "123, Test Street, Test City, Test State, ABC123, Test Country",
        )
    
    def test_form_save_creates_organization(self):
        form=OrganizationForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        organization = form.save(account=self.account)
        self.assertEqual(organization.organization_name, self.valid_data["organization_name"])
        self.assertEqual(organization.account, self.account)