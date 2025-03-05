from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import VolunteerOpportunity
from accounts_notifs.models import Account
from volunteers_organizations.models import Organization, Volunteer
from django.urls import reverse
from datetime import date, timedelta
import json

Account = get_user_model()

def create_common_objects():
    #Creating a volunteer account
    volunteer_account = Account.objects.create(
        email_address='test_email_vol@tester.com',
        password='testerpassword',
        user_type='volunteer',
        contact_number="+35612345678"
    )
    organization_account = Account.objects.create(
        email_address='test_email_org@tester.com',
        password='testerpassword',
        user_type='organization',
        contact_number="+35612345679"
    )
    return volunteer_account, organization_account

class GetOpportunitiesAPITest(APITestCase):
    # Create test data: user, organization, and opportunities.
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.volunteer_account, cls.organization_account = create_common_objects()

        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )

        # Create an organization
        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="Non-profit organization.",
            organization_address={
                'raw': '123 Help St, Kindness City, US',
                'street_number': '123',
                'route': 'Help St',
                'locality': 'Kindness City',
                'postal_code': '12345',
                'state': 'CA',
                'state_code': 'CA',
                'country': 'United States',
                'country_code': 'US'
            }
        )

        # One-time opportunity (Must have opportunity_date, opportunity_time_from, and opportunity_time_to)
        cls.opportunity_online = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Online Teaching",
            description="Teach kids remotely",
            work_basis="online",
            duration="short-term",
            opportunity_date=date.today() + timedelta(days=5),  # Required
            opportunity_time_from="09:00:00",  # Required
            opportunity_time_to="11:00:00",  # Required
            ongoing=False,  # Not ongoing
            area_of_work="education",
            requirements=["teaching", "communication"],
            required_location={"lat": 35.9, "lon": 14.5},
            languages=["English", "French"],
            status="upcoming"
        )

        # Ongoing opportunity (Must NOT have opportunity_date, time_from, or time_to)
        cls.opportunity_in_person = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Beach Cleanup",
            description="Help clean the beach",
            work_basis="in-person",
            duration="long-term",
            opportunity_date=None,  # Should not exist
            opportunity_time_from=None,  # Should not exist
            opportunity_time_to=None,  # Should not exist
            ongoing=True,  # Ongoing
            days_of_week=["saturday", "sunday"],
            area_of_work="environment",
            requirements=["teamwork"],
            required_location={"lat": 35.92, "lon": 14.49},
            languages=["Maltese"],
            status="upcoming"
        )

        # Another ongoing opportunity (Must NOT have opportunity_date, time_from, or time_to)
        cls.opportunity_tech = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Web Development Project",
            description="Help build a website for an NGO",
            work_basis="both",
            duration="medium-term",
            opportunity_date=None,  # Should not exist
            opportunity_time_from=None,  # Should not exist
            opportunity_time_to=None,  # Should not exist
            ongoing=True,  # Ongoing
            days_of_week=["monday", "wednesday"],
            area_of_work="technology",
            requirements=["coding", "web development"],
            required_location={"lat": 35.88, "lon": 14.48},
            languages=["English"],
            status="upcoming"
        )

        cls.url = reverse("opportunities_engagements:get_opportunities")

    def setUp(self):
        self.client.force_authenticate(user=self.volunteer_account)        

    # Should return all upcoming opportunities when no filters are applied.
    def test_no_filters_returns_all_upcoming(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)  # We created 3 test opportunities

    # Should return only opportunities that match the work type.
    def test_filter_by_work_basis(self):
        response = self.client.get(self.url, {"work_basis": "online"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Online Teaching")

    # Should return opportunities that match the selected duration.
    def test_filter_by_duration(self):
        response = self.client.get(self.url, {"duration": "long-term"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Beach Cleanup")

    # Should return opportunities that match the selected area of work.
    def test_filter_by_area_of_work(self):
        response = self.client.get(self.url, {"area_of_work": "technology"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Web Development Project")

    # Should return opportunities that match the required skills.
    def test_filter_by_requirements(self):
        response = self.client.get(self.url, {"requirements": "coding"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Web Development Project")

    # Should return opportunities that match the required languages.
    def test_filter_by_languages(self):
        response = self.client.get(self.url, {"languages": "Maltese"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Beach Cleanup")

    # Should return only one-time or ongoing opportunities.
    def test_filter_by_opportunity_type(self):
        response = self.client.get(self.url, {"one_time": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Online Teaching")

        response = self.client.get(self.url, {"ongoing": "on"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    # Should return only opportunities within the given date range.
    def test_filter_by_date_range(self):
        response = self.client.get(self.url, {"start_date": str(date.today() + timedelta(days=4)), "end_date": str(date.today() + timedelta(days=6))})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Online Teaching")

    # Should return opportunities within proximity range.
    def test_filter_by_location(self):
        location_json = json.dumps({"lat": 35.91, "lon": 14.50, "city": "Valletta", "formatted_address": "Valletta, Malta"})
        response = self.client.get(self.url, {"location_input": "Valletta, Malta", "location": location_json, "proximity": "2"})
        print("\nResponse Data (Opportunities Returned):")
        for opp in response.data:
            print(f"- {opp['title']} | Location: {opp['required_location']}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # Should include in-person and tech opportunities

    # Should return the correct filtered opportunities when multiple filters are applied.
    def test_combination_filters(self):
        response = self.client.get(self.url, {
            "work_basis": "both",
            "languages": "English",
            "requirements": "coding"
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["title"], "Web Development Project")

    # Ensure filtering by days_of_week correctly returns only the relevant ongoing opportunities.
    def test_filter_by_days_of_week(self):
        response = self.client.get(self.url, {"days_of_week": "saturday"})

        self.assertEqual(response.status_code, 200)
        results = response.json()

        # Should return only the Beach Cleanup opportunity (since it has "saturday" in days_of_week)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Beach Cleanup")

        # Test for multiple day filtering (Monday + Wednesday should match 'Web Development Project')
        response = self.client.get(self.url, {"days_of_week": ["monday", "wednesday"]})
        self.assertEqual(response.status_code, 200)
        results = response.json()

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["title"], "Web Development Project")