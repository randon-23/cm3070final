from django.test import TestCase
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from ..models import Volunteer, VolunteerMatchingPreferences, Organization, OrganizationPreferences, Following, Endorsement, StatusPost
from accounts_notifs.models import Account
from uuid import UUID
from datetime import date

def create_common_objects():
    #Creating a volunteer account
    volunteer_account = Account.objects.create(
        email_address='test_email_vol@tester.com',
        password='testerpassword',
        user_type='volunteer',
        contact_number='+1234567890'
    )
    organization_account = Account.objects.create(
        email_address='test_email_org@tester.com',
        password='testerpassword',
        user_type='organization',
        contact_number='+0987654321'
    )
    return volunteer_account, organization_account

class TestVolunteerModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, _= create_common_objects()

    def test_create_volunteer(self):
        volunteer=Volunteer.objects.create(
            account=self.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1999, 1, 1),
        )

        self.assertEqual(volunteer.account, self.volunteer_account)
        self.assertEqual(volunteer.first_name, "John")
        self.assertEqual(volunteer.last_name, "Doe")
        self.assertEqual(volunteer.dob, date(1999, 1, 1))
        self.assertIsNotNone(volunteer.volontera_points)
        self.assertIsNotNone(volunteer.followers)
        self.assertEqual(volunteer.volontera_points, 0)
        self.assertEqual(volunteer.followers, 0)

    def test_create_volunteer_dob_future(self):
        volunteer = Volunteer(
            account=self.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(2026, 1, 1), 
        )

        with self.assertRaises(ValidationError):
            volunteer.full_clean() 

    def test_volunteer_account_association_uniqueness(self):
        #Creating a volunteer
        Volunteer.objects.create(
            account=self.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1999, 1, 1),
        )

        #Creating another volunteer associated with the same account
        #This should raise an IntegrityError
        with self.assertRaises(ValidationError) as error:
            volunteer=Volunteer.objects.create(
                account=self.volunteer_account,
                first_name="Jane",
                last_name="Doe",
                dob=date(2000, 6, 5),
            )
            volunteer.full_clean()
        
        self.assertIn("Volunteer with this Account already exists.", str(error.exception))

class TestVolunteerMatchingPreferencesModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, _= create_common_objects()
        cls.volunteer=Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1999, 1, 1)
        )
        cls.preferences=VolunteerMatchingPreferences.objects.create(
            volunteer=cls.volunteer,
            availability=['monday', 'tuesday', 'friday'],
            preferred_work_types='both',
            preferred_duration=['short-term', 'medium-term'],
            fields_of_interest=['education', 'health'],
            skills=['teaching', 'public speaking']
        )

    def test_create_volunteer_preferences_creation(self):
        self.assertEqual(self.preferences.volunteer, self.volunteer)
        self.assertEqual(self.preferences.availability, ['monday', 'tuesday', 'friday'])
        self.assertEqual(self.preferences.preferred_work_types, 'both')
        self.assertEqual(self.preferences.preferred_duration, ['short-term', 'medium-term'])
        self.assertEqual(self.preferences.fields_of_interest, ['education', 'health'])
        self.assertEqual(self.preferences.skills, ['teaching', 'public speaking'])

    def test_invalid_preferred_duration(self):
        self.preferences.preferred_duration = ['short-term', 'invalid']
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("Invalid choices", str(context.exception.message_dict["preferred_duration"]))
    
    def test_invalid_availability(self):
        self.preferences.availability = ['monday', 'invalid']
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("Invalid choices", str(context.exception.message_dict["availability"]))

    def test_preferred_duration_not_list(self):
        self.preferences.preferred_duration = 'short-term'
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("must be a list", str(context.exception.message_dict["preferred_duration"]))

    def test_availability_not_list(self):
        self.preferences.availability = 'monday'
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("must be a list", str(context.exception.message_dict["availability"]))

    def test_empty_fields_of_interest(self):
        self.preferences.fields_of_interest = []
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("must not be empty", str(context.exception.message_dict["fields_of_interest"]))

    def test_fields_of_interest_exceeds_max(self):
        self.preferences.fields_of_interest = ['education', 'health', 'technology', 'environment', 'arts', 'sports']
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("must be at most 5", str(context.exception.message_dict["fields_of_interest"]))
    
    def test_invalid_fields_of_interest(self):
        self.preferences.fields_of_interest = ['invalid']
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("Invalid choices", str(context.exception.message_dict["fields_of_interest"]))
    
    def test_empty_skills(self):
        self.preferences.skills = []
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("must not be empty", str(context.exception.message_dict["skills"]))

    def test_skills_not_list(self):
        self.preferences.skills = 'teaching'
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("must be a list", str(context.exception.message_dict["skills"]))
    
    def test_skills_exceed_limit(self):
        self.preferences.skills = ['teaching', 'public speaking', 'coding', 'writing', 'research', 
                                   'communication', 'translation', 'first aid', 'counseling', 'mentoring', 'videography']
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("must be at most 10", str(context.exception.message_dict["skills"]))

    def test_invalid_skills(self):
        self.preferences.skills = ['invalid']
        with self.assertRaises(ValidationError) as context:
            self.preferences.full_clean()
        self.assertIn("Invalid choices", str(context.exception.message_dict["skills"]))
    
class TestOrganizationModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        _, cls.organization_account= create_common_objects()
        cls.organization_address = {
            'raw': '1 Somewhere Ave, Northcote, VIC 3070, AU',
            'street_number': '1',
            'route': 'Somewhere Ave',
            'locality': 'Northcote',
            'postal_code': '3070',
            'state': 'Victoria',
            'state_code': 'VIC',
            'country': 'Australia',
            'country_code': 'AU'
        }
        cls.organization=Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Earth",
            organization_description="A non-profit dedicated to environmental conservation.",
            organization_address=cls.organization_address
        )

    def test_create_organization(self):
        self.assertEqual(self.organization.account, self.organization_account)
        self.assertEqual(self.organization.organization_name, "Save the Earth")
        self.assertEqual(self.organization.organization_description, "A non-profit dedicated to environmental conservation.")
        self.assertIsNotNone(self.organization.organization_address)
        self.assertEqual(self.organization.followers, 0)

        organization_address = self.organization.organization_address
        self.assertEqual(organization_address['raw'], self.organization_address['raw'])
        self.assertEqual(organization_address['street_number'], self.organization_address['street_number'])
        self.assertEqual(organization_address['route'], self.organization_address['route'])
        self.assertEqual(organization_address['locality'], self.organization_address['locality'])
        self.assertEqual(organization_address['postal_code'], self.organization_address['postal_code'])
        self.assertEqual(organization_address['state'], self.organization_address['state'])
        self.assertEqual(organization_address['state_code'], self.organization_address['state_code'])
        self.assertEqual(organization_address['country'], self.organization_address['country'])
        self.assertEqual(organization_address['country_code'], self.organization_address['country_code'])

    def test_organization_address_components(self):
        self.assertEqual(self.organization.organization_address['street_number'], '1')
        self.assertEqual(self.organization.organization_address['locality'], 'Northcote')
        self.assertEqual(self.organization.organization_address['postal_code'], '3070')
        self.assertEqual(self.organization.organization_address['state'], 'Victoria')
        self.assertEqual(self.organization.organization_address['state_code'], 'VIC')
        self.assertEqual(self.organization.organization_address['country'], 'Australia')
        self.assertEqual(self.organization.organization_address['country_code'], 'AU')
    
    def test_organization_name_max_length(self):
        self.organization.organization_name = "A" * 101
        with self.assertRaises(Exception) as context:
            self.organization.full_clean()

        self.assertIn("organization_name", str(context.exception))

    def test_organization_description_max_length(self):
        self.organization.organization_description = "A" * 501
        with self.assertRaises(Exception) as context:
            self.organization.full_clean()

        self.assertIn("organization_description", str(context.exception))

    def test_update_followers(self):
        self.organization.followers = 100
        self.assertEqual(self.organization.followers, 100)

    def test_negative_followers(self):
        self.organization.followers = -1
        with self.assertRaises(ValidationError) as context:
            self.organization.full_clean()

        self.assertIn("Followers cannot be negative", str(context.exception))

    def test_duplicate_organization_name(self):
        with self.assertRaises(Exception):
            organization = Organization.objects.create(
                account=self.organization_account,
                organization_name="Save the Earth",
                organization_description="A non-profit dedicated to environmental conservation.",
                organization_address=self.organization_address,
                followers=100
            )
            organization.full_clean()

    def test_update_organization_address(self):
        new_address = {
            'raw': '1 Somewhere Ave, Northcote, VIC 3070, AU'
        }
        self.organization.organization_address = new_address
        self.organization.save()

        self.assertEqual(self.organization.organization_address, new_address)

class TestOrganizationPreferencesModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        _, cls.organization_account= create_common_objects()
        cls.organization=Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Earth",
            organization_description="A non-profit dedicated to environmental conservation.",
            organization_address={
                'raw': '1 Somewhere Ave, Northcote, VIC 3070, AU',
                'street_number': '1',
                'route': 'Somewhere Ave',
                'locality': 'Northcote',
                'postal_code': '3070',
                'state': 'Victoria',
                'state_code': 'VIC',
                'country': 'Australia',
                'country_code': 'AU'
            }
        )

    # Test saving a valid OrganizationPreferences instance.
    def test_valid_organization_preferences(self):
        preferences = OrganizationPreferences.objects.create(
            organization=self.organization,
            location={
                "lat": 40.7128,
                "lon": -74.0060,
                "city": "New York",
                "formatted_address": "New York, NY, USA"
            }
        )
        self.assertEqual(preferences.organization, self.organization)

    # Test that enabling point opportunities without a rate raises ValidationError
    def test_location_not_dictionary(self):
        preferences = OrganizationPreferences(
            organization=self.organization,
            location = "Hello"
        )
        with self.assertRaises(ValidationError) as context:
            preferences.full_clean()

        self.assertIn("Location must be a dictionary", str(context.exception))

    # Test that preferences can be saved properly.
    def test_save_organization_preferences(self):
        preferences = OrganizationPreferences(
            organization=self.organization,
            location={
                "lat": 40.7128,
                "lon": -74.0060,
                "city": "New York",
                "formatted_address": "New York, NY, USA"
            }
        )
        preferences.save()
        self.assertEqual(preferences.organization, self.organization)
        self.assertEqual(preferences.location, {
            "lat": 40.7128,
            "lon": -74.0060,
            "city": "New York",
            "formatted_address": "New York, NY, USA"
        })

class TestFollowingModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account_follower, cls.organization_account= create_common_objects()
        cls.volunteer_follower=Volunteer.objects.create(
            account=cls.volunteer_account_follower,
            first_name="John",
            last_name="Doe",
            dob=date(1999, 1, 1)
        )
        cls.volunteer_account_to_be_followed=Account.objects.create(
            email_address='test2vol@volontera.com',
            password='testerpassword',
            user_type='volunteer',
            contact_number="+1234567660"
        )
        cls.volunteer_to_be_followed=Volunteer.objects.create(
            account=cls.volunteer_account_to_be_followed,
            first_name="Mary",
            last_name="Dean",
            dob=date(1999, 1, 1)
        )
        cls.organization_address = {
            'raw': '1 Somewhere Ave, Northcote, VIC 3070, AU',
            'street_number': '1',
            'route': 'Somewhere Ave',
            'locality': 'Northcote',
            'postal_code': '3070',
            'state': 'Victoria',
            'state_code': 'VIC',
            'country': 'Australia',
            'country_code': 'AU'
        }
        cls.organization=Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Earth",
            organization_description="A non-profit dedicated to environmental conservation.",
            organization_address=cls.organization_address
        )
        cls.organization_account_to_be_followed=Account.objects.create(
            email_address="org@account.com",
            password="SecurePass123",
            user_type="organization",
            contact_number="+1234567150"
        )
        cls.organization_to_be_followed=Organization.objects.create(
            account=cls.organization_account_to_be_followed,
            organization_name="Save the Animals",
            organization_description="A non-profit dedicated to animal welfare.",
            organization_address={
                'raw': '2 Somewhere Ave, Northcote, VIC 3070, AU'
            }
        )
    
    def test_valid_follow_volunteer(self):
        following=Following.objects.create(
            follower=self.volunteer_account_follower,
            followed_volunteer=self.volunteer_to_be_followed
        )
        self.assertEqual(following.follower, self.volunteer_account_follower)
        self.assertEqual(following.followed_volunteer, self.volunteer_to_be_followed)
        self.assertIsNone(following.followed_organization)

    def test_valid_follow_organization(self):
        following=Following.objects.create(
            follower=self.volunteer_account_follower,
            followed_organization=self.organization
        )
        self.assertEqual(following.follower, self.volunteer_account_follower)
        self.assertEqual(following.followed_organization, self.organization)
        self.assertIsNone(following.followed_volunteer)

    def test_mutual_exclusivity(self):
        with self.assertRaises(IntegrityError):
            Following.objects.create(
                follower=self.volunteer_account_follower,
                followed_volunteer=self.volunteer_to_be_followed,
                followed_organization=self.organization
            )
    
    def test_unique_follower_volunteer(self):
        Following.objects.create(
            follower=self.volunteer_account_follower,
            followed_volunteer=self.volunteer_to_be_followed
        )
        with self.assertRaises(IntegrityError):
            Following.objects.create(
                follower=self.volunteer_account_follower,
                followed_volunteer=self.volunteer_to_be_followed
            )

    def test_unique_follower_organization(self):
        Following.objects.create(
            follower=self.volunteer_account_follower,
            followed_organization=self.organization
        )
        with self.assertRaises(IntegrityError):
            Following.objects.create(
                follower=self.volunteer_account_follower,
                followed_organization=self.organization
            )
    
    def test_prevent_self_following(self):
        with self.assertRaises(IntegrityError):
            Following.objects.create(
                follower=self.volunteer_account_follower,
                followed_volunteer=self.volunteer_follower
            )

    def test_prevent_organization_from_following_other_organizations(self):
        with self.assertRaises(ValidationError):
            Following.objects.create(
                follower=self.organization_account,
                followed_organization=self.organization_to_be_followed
            )

    def test_organizations_can_follow_volunteers(self):
        following=Following.objects.create(
            follower=self.organization_account,
            followed_volunteer=self.volunteer_to_be_followed
        )
        self.assertEqual(following.follower, self.organization_account)
        self.assertEqual(following.followed_volunteer, self.volunteer_to_be_followed)
        self.assertIsNone(following.followed_organization)

    def test_no_follow_entity(self):
        with self.assertRaises(IntegrityError):
            Following.objects.create(
                follower=self.volunteer_account_follower
            )

    def test_follow_multiple_entities(self):
        following_volunteer=Following.objects.create(
            follower=self.volunteer_account_follower,
            followed_volunteer=self.volunteer_to_be_followed
        )
        following_organization=Following.objects.create(
            follower=self.volunteer_account_follower,
            followed_organization=self.organization
        )
        self.assertEqual(following_volunteer.follower, self.volunteer_account_follower)
        self.assertEqual(following_volunteer.followed_volunteer, self.volunteer_to_be_followed)
        self.assertIsNone(following_volunteer.followed_organization)
        self.assertEqual(following_organization.follower, self.volunteer_account_follower)
        self.assertEqual(following_organization.followed_organization, self.organization)
        self.assertIsNone(following_organization.followed_volunteer)

    def test_followed_by_multiple_entities(self):
        follower_1=Following.objects.create(
            follower=self.volunteer_account_follower,
            followed_organization=self.organization
        )
        follower_2=Following.objects.create(
            follower=self.volunteer_account_to_be_followed,
            followed_organization=self.organization
        )
        self.assertEqual(follower_1.follower, self.volunteer_account_follower)
        self.assertEqual(follower_1.followed_organization, self.organization)
        self.assertIsNone(follower_1.followed_volunteer)
        self.assertEqual(follower_2.follower, self.volunteer_account_to_be_followed)
        self.assertEqual(follower_2.followed_organization, self.organization)
        self.assertIsNone(follower_2.followed_volunteer)

class TestEndorsementModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer1 = Account.objects.create_user(
            email_address="volunteer1@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+1234567890"
        )
        cls.volunteer2 = Account.objects.create_user(
            email_address="volunteer2@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+0987654321"
        )
        cls.organization1 = Account.objects.create_user(
            email_address="org1@example.com",
            password="SecurePass123!",
            user_type="organization",
            contact_number="+23499876652"
        )
        cls.organization2 = Account.objects.create_user(
            email_address="org2@example.com",
            password="SecurePass123!",
            user_type="organization",
            contact_number="+23499876653"
        )
        cls.volunteer1_profile = Volunteer.objects.create(
            account=cls.volunteer1,
            first_name="John",
            last_name="Doe",
            dob=date(1999, 1, 1)
        )
        cls.volunteer2_profile = Volunteer.objects.create(
            account=cls.volunteer2,
            first_name="Jane",
            last_name="Doe",
            dob=date(1999, 1, 1)
        )
        cls.organization1_profile = Organization.objects.create(
            account=cls.organization1,
            organization_name="Save the Earth",
            organization_description="A non-profit dedicated to environmental conservation.",
            organization_address={
                'raw': '1 Somewhere Ave, Northcote, VIC 3070, AU',
                'street_number': '1',
                'route': 'Somewhere Ave',
                'locality': 'Northcote',
                'postal_code': '3070',
                'state': 'Victoria',
                'state_code': 'VIC',
                'country': 'Australia',
                'country_code': 'AU'
            }
        )
        cls.organization2_profile = Organization.objects.create(
            account=cls.organization2,
            organization_name="Save the Animals",
            organization_description="A non-profit dedicated to animal welfare.",
            organization_address={
                'raw': '2 Somewhere Ave, Northcote, VIC 3070, AU',
                'street_number': '2',
                'route': 'Somewhere Ave',
                'locality': 'Northcote',
                'postal_code': '3070',
                'state': 'Victoria',
                'state_code': 'VIC',
                'country': 'Australia',
                'country_code': 'AU'
            }
        )

    def test_valid_volunteer_to_volunteer_endorsement(self):
        endorsement = Endorsement.objects.create(
            giver=self.volunteer1,
            receiver=self.volunteer2,
            endorsement="Great work!"
        )
        self.assertEqual(endorsement.giver, self.volunteer1)
        self.assertEqual(endorsement.receiver, self.volunteer2)

    def test_valid_organization_to_volunteer_endorsement(self):
        endorsement = Endorsement.objects.create(
            giver=self.organization1,
            receiver=self.volunteer1,
            endorsement="Awesome volunteer!"
        )
        self.assertEqual(endorsement.giver, self.organization1)
        self.assertEqual(endorsement.receiver, self.volunteer1)

    def test_organization_cannot_endorse_organization(self):
        endorsement = Endorsement(
            giver=self.organization1,
            receiver=self.organization2,
            endorsement="Supportive organization!"
        )
        with self.assertRaises(ValidationError) as e:
            endorsement.full_clean()
        self.assertIn("Organizations cannot endorse each other.", str(e.exception))

    def test_cannot_endorse_self(self):
        endorsement = Endorsement(
            giver=self.volunteer1,
            receiver=self.volunteer1,
            endorsement="Self-endorsement!"
        )
        with self.assertRaises(ValidationError) as e:
            endorsement.full_clean()
        self.assertIn("Cannot endorse oneself.", str(e.exception))

class TestStatusPostModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = Account.objects.create_user(
            email_address="user@example.com",
            password="SecurePass123!",
            user_type="volunteer",
            contact_number="+1234567890"
        )
        cls.user_profile = Volunteer.objects.create(
            account=cls.user,
            first_name="John",
            last_name="Doe",
            dob=date(1999, 1, 1)
        )

    def test_create_status_post(self):
        status = StatusPost.objects.create(
            author=self.user,
            content="Excited to volunteer today!"
        )
        self.assertEqual(status.author, self.user)
        self.assertEqual(status.content, "Excited to volunteer today!")

    def test_create_status_post_empty_content_fails(self):
        status = StatusPost(author=self.user, content="   ")
        with self.assertRaises(ValidationError) as e:
            status.full_clean()
        self.assertIn("Status post content cannot be empty.", str(e.exception))