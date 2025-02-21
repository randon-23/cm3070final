from django.test import TestCase
from ..forms import AccountSignupForm, LoginForm
from ..models import Account

class TestAccountSignupForm(TestCase):
    def setUp(self):
        self.valid_data = {
            'email_address': 'testuser@example.com',
            'password_1': 'securePassword123!',
            'password_2': 'securePassword123!',
            'user_type': 'volunteer',
            'contact_prefix': '+356',
            'contact_number': '12345678',
        }

    def test_form_valid_with_correct_data(self):
        form = AccountSignupForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_when_passwords_match_but_do_not_meet_criteria(self):
        self.valid_data['password_1'] = 'mjgoat23'  
        self.valid_data['password_2'] = 'mjgoat23'
        form = AccountSignupForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password_1', form.errors)
        self.assertEqual(
            form.errors['password_1'],
            ['Password must contain at least 8 characters including one uppercase letter, one lowercase letter, one digit, and one special character']
        )

    def test_form_invalid_when_passwords_dont_match(self):
        self.valid_data['password_2'] = 'differentPassword'
        form = AccountSignupForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password_2', form.errors)
        self.assertEqual(form.errors['password_2'], ['Passwords do not match'])

    def test_form_invalid_with_missing_contact_prefix(self):
        self.valid_data.pop('contact_prefix')
        form = AccountSignupForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('contact_number', form.errors)

    def test_form_invalid_with_non_numeric_contact_number(self):
        self.valid_data['contact_number'] = '12345abc'
        form = AccountSignupForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('contact_number', form.errors)

    def test_form_saves_correctly(self):
        form = AccountSignupForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
        account = form.save(commit=False)
        # Setting paszword is done separately in signup_final so needed to add it here for tests sake
        account.set_password(self.valid_data['password_1'])
        account.save()
        self.assertEqual(account.email_address, self.valid_data['email_address'])
        self.assertTrue(account.check_password(self.valid_data['password_1']))
        self.assertEqual(account.contact_number, f"{self.valid_data['contact_prefix']}{self.valid_data['contact_number']}")

# Form acts as a data collector and thus needs to be tested to ensure that it collects the correct data and validates it correctly. Actual authenication is handled in the view and thus is not tested here.
class TestLoginForm(TestCase):
    def setUp(self):
        self.user = Account.objects.create(
            email_address='test_email@tester.com',
            user_type='volunteer',
            contact_number="+35612345678"
        )
        self.user.set_password('SecurePassword1!')
        self.user.save()

        self.valid_data = {
            'username': 'test_email@tester.com',
            'password': 'SecurePassword1!'
        }

    def test_form_valid_with_correct_data(self):
        form = LoginForm(data=self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_with_incorrect_email_format(self):
        self.valid_data['username'] = 'invalidemail'
        form = LoginForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertEqual(form.errors['username'], ['Invalid email address'])

    def test_form_invalid_with_missing_password(self):
        self.valid_data.pop('password')
        form = LoginForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password', form.errors)

    def test_form_invalid_with_nonexistent_user(self):
        self.valid_data['username'] = 'nonexistent@example.com'
        form = LoginForm(data=self.valid_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Please enter a correct email address and password. Note that both fields may be case-sensitive.',form.errors['__all__'])
