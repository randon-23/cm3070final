from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from ..models import VolunteerOpportunity, VolunteerOpportunityApplication, VolunteerEngagement, VolunteerOpportunitySession, VolunteerSessionEngagement, VolunteerEngagementLog
from accounts_notifs.models import Account
from volunteers_organizations.models import Organization, Volunteer, VolunteerMatchingPreferences
from django.urls import reverse
from datetime import date, time, timedelta
from django.utils import timezone
from geopy.distance import geodesic
import json
import uuid


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

class GetOpportunityAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()

        # Create common test objects
        cls.volunteer_account, cls.organization_account = create_common_objects()

        # Create organization & volunteer
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
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account, 
            first_name="John", 
            last_name="Doe",
            dob=date(1995, 1, 1)
        )

        cls.other_organization_account = Account.objects.create(
            email_address='test_email1_org@tester.com',
            password='testerpassword',
            user_type='organization',
            contact_number="+35612645675"
        )
        cls.other_organization = Organization.objects.create(
            account=cls.other_organization_account,
            organization_name="Org 2",
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
        # Create an opportunity owned by organization
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Online Teaching",
            description="Teach kids remotely",
            work_basis="online",
            duration="short-term",
            ongoing=True,
            area_of_work="education",
            requirements=["teaching", "communication"],
            required_location={"lat": 35.9, "lon": 14.5},
            languages=["English", "French"],
            status="upcoming"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.organization_account)  # Default: Organization logged in

    # Test organization retrieves its own opportunity
    def test_get_opportunity_success_organization(self):
        get_opportunity_url = reverse("opportunities_engagements:get_opportunity", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.get(get_opportunity_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Online Teaching")

    # Test organization cannot view another organization's opportunity
    def test_get_opportunity_unauthorized_organization(self):
        self.client.force_authenticate(user=self.other_organization_account)
        get_opportunity_url = reverse("opportunities_engagements:get_opportunity", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.get(get_opportunity_url)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "You can only view your own opportunities.")

    # Test volunteer can view an opportunity
    def test_get_opportunity_success_volunteer(self):
        self.client.force_authenticate(user=self.volunteer_account)
        get_opportunity_url = reverse("opportunities_engagements:get_opportunity", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.get(get_opportunity_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "Online Teaching")

    # Test unauthenticated user cannot view an opportunity
    def test_get_opportunity_unauthenticated(self):
        self.client.force_authenticate(user=None)
        get_opportunity_url = reverse("opportunities_engagements:get_opportunity", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.get(get_opportunity_url)
        self.assertEqual(response.status_code, 403)

    # Test fetching a non-existent opportunity
    def test_get_opportunity_not_found(self):
        get_opportunity_url = reverse("opportunities_engagements:get_opportunity", args=[uuid.uuid4()])
        response = self.client.get(get_opportunity_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"], "Opportunity not found.")

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

class GetNearbyAndLatestOpportunitiesAPITest(APITestCase):
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

        # Create volunteer preferences with a fixed location
        cls.preferences = VolunteerMatchingPreferences.objects.create(
            volunteer=cls.volunteer,
            location={"lat": 35.9, "lon": 14.5, "city": "Valletta", "formatted_address": "Valletta, Malta"}
        )

        cls.opportunities = []
        base_time = timezone.now()  # Current timestamp

        # Create 10 volunteer opportunities with different distances and timestamps
        locations = [
            {"lat": 35.91, "lon": 14.50},  # Close
            {"lat": 35.92, "lon": 14.51},  # Close
            {"lat": 35.95, "lon": 14.55},  # Medium distance
            {"lat": 36.00, "lon": 14.60},  # Farther away
            {"lat": 36.05, "lon": 14.65},  # Far
            {"lat": 35.89, "lon": 14.48},  # Close
            {"lat": 35.87, "lon": 14.46},  # Close
            {"lat": 35.80, "lon": 14.40},  # Medium distance
            {"lat": 35.70, "lon": 14.30},  # Far
            {"lat": 35.60, "lon": 14.20},  # Very far
        ]

        for i in range(10):
            opportunity = VolunteerOpportunity.objects.create(
                organization=cls.organization,
                title=f"Opportunity {i+1}",
                description=f"Description {i+1}",
                work_basis="in-person",
                duration="medium-term",
                ongoing=False if i % 2 == 0 else True,
                opportunity_date=(date.today() + timedelta(days=5)) if i % 2 == 0 else None,
                opportunity_time_from="09:00:00" if i % 2 == 0 else None,
                opportunity_time_to="11:00:00" if i % 2 == 0 else None,
                days_of_week=["monday", "tuesday"] if i % 2 != 0 else [],
                area_of_work="community",
                requirements=["teamwork", "communication"],
                required_location=locations[i],  # Assigning locations
                languages=["English"],
                status="upcoming",
                created_at=base_time - timedelta(seconds=i)  # Manually setting creation dates
            )
            cls.opportunities.append(opportunity)


        cls.nearby_url = reverse("opportunities_engagements:get_nearby_opportunities")
        cls.latest_url = reverse("opportunities_engagements:get_latest_opportunities")
    def setUp(self):
        self.client.force_authenticate(user=self.volunteer_account)

    # Test retrieving the 5 most recent opportunities.
    # NO WAY to override create_at field in the model which is auto_now_add=True
    # def test_get_latest_opportunities(self):
    #     response = self.client.get(self.latest_url)
    #     self.assertEqual(response.status_code, 200)

    #     # Ensure 5 opportunities are returned
    #     self.assertEqual(len(response.data), 5)

    #     # Sort expected opportunities by `created_at` descending
    #     expected_opportunities = sorted(
    #         self.opportunities, key=lambda opp: opp.created_at, reverse=True
    #     )[:5]

    #     expected_ids = [str(opp.volunteer_opportunity_id) for opp in expected_opportunities]
    #     returned_ids = [opp["volunteer_opportunity_id"] for opp in response.data]

    #     self.assertEqual(returned_ids, expected_ids)

    # Test retrieving the 5 closest opportunities.
    def test_get_nearby_opportunities(self):
        response = self.client.get(self.nearby_url)
        self.assertEqual(response.status_code, 200)

        # Ensure 5 opportunities are returned
        self.assertEqual(len(response.data), 5)

        # Get volunteer's stored location from preferences
        user_location = (self.preferences.location["lat"], self.preferences.location["lon"])

        # Sort expected opportunities by distance
        expected_opportunities = sorted(
            self.opportunities,
            key=lambda opp: geodesic(
                user_location,
                (opp.required_location["lat"], opp.required_location["lon"])
            ).km
        )[:5]

        expected_ids = [str(opp.volunteer_opportunity_id) for opp in expected_opportunities]
        returned_ids = [opp["volunteer_opportunity_id"] for opp in response.data]

        self.assertEqual(returned_ids, expected_ids)

class CreateOpportunityAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.volunteer_account, cls.organization_account = create_common_objects()

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

        cls.opportunity_data = {
            "title": "Food Drive",
            "description": "Help distribute food to those in need.",
            "work_basis": "in-person",
            "duration": "short-term",
            "opportunity_date": (date.today() + timedelta(days=5)).isoformat(),
            "opportunity_time_from": "09:00:00",
            "opportunity_time_to": "12:00:00",
            "ongoing": False,
            "area_of_work": "community",
            "requirements": ["teamwork", "organization"],
            "required_location": {"lat": 35.9, "lon": 14.5},
            "languages": ["English", "French"],
            "status": "upcoming",
            "can_apply_as_group": True,
            "slots": 10
        }

        cls.url = reverse("opportunities_engagements:create_opportunity")

    def setUp(self):
        self.client.force_authenticate(user=self.organization_account)

    def test_create_opportunity_success(self):
        response = self.client.post(self.url, self.opportunity_data, format="json", context={'request': self.client})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Successfully created opportunity")
        self.assertIn("data", response.data)

    def test_create_opportunity_missing_fields(self):
        incomplete_data = self.opportunity_data.copy()
        del incomplete_data["title"]  # Remove a required field

        response = self.client.post(self.url, incomplete_data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["message"], "An error occurred when creating the opportunity")
        self.assertIn("data", response.data)  # Should contain validation errors

    def test_create_opportunity_as_non_organization(self):
        self.client.force_authenticate(user=self.volunteer_account)
        response = self.client.post(self.url, self.opportunity_data, format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Only organizations can create opportunities.")

    def test_create_opportunity_no_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, self.opportunity_data, format="json")
        self.assertEqual(response.status_code, 403)  # Should require authentication

class GetOrganizationOpportunityAPITest(APITestCase):
        @classmethod
        def setUpTestData(cls):
            cls.client = APIClient()

            # Create two organization accounts
            cls.org_account1 = Account.objects.create_user(
                email_address='org1@example.com',
                password='password123',
                user_type='organization',
                contact_number='+35612345678'
            )
            cls.org_account2 = Account.objects.create_user(
                email_address='org2@example.com',
                password='password123',
                user_type='organization',
                contact_number='+35687654321'
            )

            # Create organizations
            cls.organization1 = Organization.objects.create(
                account=cls.org_account1,
                organization_name="Org One",
                organization_description="First test organization.",
                organization_address={"raw": "Address 1"}
            )

            cls.organization2 = Organization.objects.create(
                account=cls.org_account2,
                organization_name="Org Two",
                organization_description="Second test organization.",
                organization_address={"raw": "Address 2"}
            )

            # Create two opportunities per organization
            cls.opportunity1_org1 = VolunteerOpportunity.objects.create(
                organization=cls.organization1,
                title="Org1 Opportunity 1",
                description="Description 1",
                work_basis="in-person",
                duration="short-term",
                ongoing=False,
                opportunity_date=date.today() + timedelta(days=10),
                opportunity_time_from="09:00:00",
                opportunity_time_to="12:00:00",
                area_of_work="education",
                requirements=["teaching"],
                languages=["English"],
                status="upcoming"
            )

            cls.opportunity2_org1 = VolunteerOpportunity.objects.create(
                organization=cls.organization1,
                title="Org1 Opportunity 2",
                description="Description 2",
                work_basis="online",
                duration="long-term",
                ongoing=True,
                days_of_week=["monday", "wednesday"],
                area_of_work="technology",
                requirements=["coding"],
                languages=["French"],
                status="upcoming"
            )

            cls.opportunity1_org2 = VolunteerOpportunity.objects.create(
                organization=cls.organization2,
                title="Org2 Opportunity 1",
                description="Description 3",
                work_basis="both",
                duration="medium-term",
                ongoing=False,
                opportunity_date=date.today() + timedelta(days=7),
                opportunity_time_from="10:00:00",
                opportunity_time_to="14:00:00",
                area_of_work="health",
                requirements=["public speaking"],
                languages=["Spanish"],
                status="upcoming"
            )

            cls.opportunity2_org2 = VolunteerOpportunity.objects.create(
                organization=cls.organization2,
                title="Org2 Opportunity 2",
                description="Description 4",
                work_basis="in-person",
                duration="short-term",
                ongoing=True,
                days_of_week=["tuesday", "thursday"],
                area_of_work="sports",
                requirements=["teamwork"],
                languages=["Italian"],
                status="upcoming"
            )

            cls.url = reverse("opportunities_engagements:get_organization_opportunities")

        def setUp(self):
            self.client.force_authenticate(user=self.org_account1)

        # Ensure an organization gets only its opportunities.
        def test_get_own_opportunities(self):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 2)

            returned_titles = [opp["title"] for opp in response.data]
            expected_titles = ["Org1 Opportunity 1", "Org1 Opportunity 2"]

            self.assertEqual(set(returned_titles), set(expected_titles))

        # Ensure one organization does not see another organization's opportunities.
        def test_cannot_access_another_org_opportunities(self):
            self.client.force_authenticate(user=self.org_account2)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data), 2)

            returned_titles = [opp["title"] for opp in response.data]
            expected_titles = ["Org2 Opportunity 1", "Org2 Opportunity 2"]

            self.assertEqual(set(returned_titles), set(expected_titles))

        # Ensure unauthorized users cannot access organization opportunities.
        def test_unauthorized_access(self):
            self.client.force_authenticate(user=None)
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 403)

class UpdateOpportunityStatusAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()

        # Create two organizations
        cls.org_account1 = Account.objects.create_user(
            email_address="org1@example.com",
            password="password123",
            user_type="organization",
            contact_number="+35612345678"
        )
        cls.org_account2 = Account.objects.create_user(
            email_address="org2@example.com",
            password="password123",
            user_type="organization",
            contact_number="+35687654321"
        )

        cls.organization1 = Organization.objects.create(
            account=cls.org_account1,
            organization_name="Org One",
            organization_description="First test organization.",
            organization_address={"raw": "Address 1"}
        )

        cls.organization2 = Organization.objects.create(
            account=cls.org_account2,
            organization_name="Org Two",
            organization_description="Second test organization.",
            organization_address={"raw": "Address 2"}
        )

        # Create upcoming opportunities
        cls.opportunity_org1 = VolunteerOpportunity.objects.create(
            organization=cls.organization1,
            title="Org1 Opportunity",
            description="Description 1",
            work_basis="in-person",
            duration="short-term",
            opportunity_date=date.today() + timedelta(days=10),
            opportunity_time_from="09:00:00",
            opportunity_time_to="12:00:00",
            area_of_work="education",
            requirements=["teaching"],
            languages=["English"],
            status="upcoming"
        )

        cls.opportunity_org2 = VolunteerOpportunity.objects.create(
            organization=cls.organization2,
            title="Org2 Opportunity",
            description="Description 2",
            work_basis="online",
            duration="long-term",
            ongoing=True,
            days_of_week=["monday", "wednesday"],
            area_of_work="technology",
            requirements=["coding"],
            languages=["French"],
            status="upcoming"
        )

        cls.cancel_url = lambda obj_id: reverse("opportunities_engagements:cancel_opportunity", args=[obj_id])
        cls.complete_url = lambda obj_id: reverse("opportunities_engagements:complete_opportunity", args=[obj_id])

    def setUp(self):
        self.client.force_authenticate(user=self.org_account1)

    # An organization can cancel its own opportunity.
    def test_cancel_own_opportunity(self):
        response = self.client.patch(self.cancel_url(self.opportunity_org1.volunteer_opportunity_id), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Opportunity successfully marked as cancelled.")

        self.opportunity_org1.refresh_from_db()
        self.assertEqual(self.opportunity_org1.status, "cancelled")

    # An organization can complete its own opportunity.
    def test_complete_own_opportunity(self):
        response = self.client.patch(self.complete_url(self.opportunity_org1.volunteer_opportunity_id), format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Opportunity successfully marked as completed.")

        self.opportunity_org1.refresh_from_db()
        self.assertEqual(self.opportunity_org1.status, "completed")

    # An organization cannot cancel another organization's opportunity.
    def test_cannot_cancel_another_orgs_opportunity(self):
        self.client.force_authenticate(user=self.org_account2)  # Authenticate as Org2
        response = self.client.patch(self.cancel_url(self.opportunity_org1.volunteer_opportunity_id), format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Unauthorized to update this opportunity.")

    # An organization cannot complete another organization's opportunity.
    def test_cannot_complete_another_orgs_opportunity(self):
        self.client.force_authenticate(user=self.org_account2)  # Authenticate as Org2
        response = self.client.patch(self.complete_url(self.opportunity_org1.volunteer_opportunity_id), format="json")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Unauthorized to update this opportunity.")

    # An organization cannot update an opportunity that is not 'upcoming'.
    def test_cannot_update_non_upcoming_opportunity(self):
        self.opportunity_org1.status = "completed"
        self.opportunity_org1.save()

        response = self.client.patch(self.cancel_url(self.opportunity_org1.volunteer_opportunity_id), format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Only upcoming opportunities can be modified.")

    # Trying to update a non-existent opportunity should return a 404.
    def test_cannot_update_nonexistent_opportunity(self):
        fake_uuid = str(uuid.uuid4())
        response = self.client.patch(self.cancel_url(fake_uuid), format="json")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data["error"], "Opportunity not found.")

    # Ensure unauthorized users cannot access this endpoint.
    def test_unauthorized_access(self):
        self.client.force_authenticate(user=None)  # No authentication
        response = self.client.patch(self.cancel_url(self.opportunity_org1.volunteer_opportunity_id), format="json")
        self.assertEqual(response.status_code, 403)  # Permission denied

class VolunteerOpportunityApplicationAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.volunteer_account, cls.organization_account = create_common_objects()

        # Create a volunteer
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

        # Create a volunteer opportunity
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Community Cleanup",
            description="Help clean up the park!",
            work_basis="in-person",
            duration="short-term",
            opportunity_date=timezone.now().date() + timedelta(days=7),
            opportunity_time_from="10:00:00",
            opportunity_time_to="14:00:00",
            area_of_work="community",
            requirements=["teamwork"],
            ongoing=False,
            slots=5,
            status="upcoming"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.volunteer_account)

    def test_create_application_success(self):
        create_application_url = reverse("opportunities_engagements:create_application", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.post(create_application_url, {}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Successfully applied for opportunity.")
    
    def test_accept_application_individual(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="pending",
            as_group=False,
            no_of_additional_volunteers=0
        )
        accept_application_url = reverse("opportunities_engagements:accept_application", args=[application.volunteer_opportunity_application_id])
        self.client.force_authenticate(user=self.organization_account)
        response = self.client.patch(accept_application_url, {}, format="json")
        self.opportunity.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.opportunity.slots, 4)

    def test_accept_application_group(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="pending",
            as_group=True,
            no_of_additional_volunteers=2
        )
        accept_application_url = reverse("opportunities_engagements:accept_application", args=[application.volunteer_opportunity_application_id])
        self.client.force_authenticate(user=self.organization_account)
        response = self.client.patch(accept_application_url, {}, format="json")
        self.opportunity.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.opportunity.slots, 2)

    def test_reject_application_success(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="pending",
            as_group=False,
            no_of_additional_volunteers=0
        )
        reject_application_url = reverse("opportunities_engagements:reject_application", args=[application.volunteer_opportunity_application_id])
        self.client.force_authenticate(user=self.organization_account)
        response = self.client.patch(reject_application_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.application_status, "rejected")

    def test_cancel_application_success(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="pending",
            as_group=False,
            no_of_additional_volunteers=0
        )
        cancel_application_url = reverse("opportunities_engagements:cancel_application", args=[application.volunteer_opportunity_application_id])
        response = self.client.patch(cancel_application_url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.application_status, "cancelled")

    def test_cannot_cancel_non_pending_application(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="accepted",
            as_group=False,
            no_of_additional_volunteers=0
        )
        cancel_application_url = reverse("opportunities_engagements:cancel_application", args=[application.volunteer_opportunity_application_id])
        response = self.client.patch(cancel_application_url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Only pending applications can be canceled.")

    def test_get_volunteer_applications(self):
        VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="accepted",
            as_group=False,
            no_of_additional_volunteers=0
        )
        get_volunteer_apps_url = reverse("opportunities_engagements:get_volunteer_applications", args=[self.volunteer.account.account_uuid])
        self.client.force_authenticate(user=self.volunteer_account)
        response = self.client.get(get_volunteer_apps_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_organization_applications(self):
        VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="accepted",
            as_group=False,
            no_of_additional_volunteers=0
        )
        get_org_apps_url = reverse("opportunities_engagements:get_organization_applications", args=[self.organization.account.account_uuid])
        self.client.force_authenticate(user=self.organization_account)
        response = self.client.get(get_org_apps_url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

class VolunteerEngagementAPITestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()

        cls.volunteer_account, cls.organization_account = create_common_objects()

        # Create organization and volunteer profiles
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

        # Create a volunteer opportunity
        cls.opportunity = VolunteerOpportunity.objects.create(
                organization=cls.organization,
                title="Org1 Opportunity 1",
                description="Description 1",
                work_basis="in-person",
                duration="short-term",
                ongoing=False,
                opportunity_date=date.today() + timedelta(days=10),
                opportunity_time_from="09:00:00",
                opportunity_time_to="12:00:00",
                area_of_work="education",
                requirements=["teaching"],
                languages=["English"],
                status="upcoming"
            )


        # Create a volunteer application (PENDING)
        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity, volunteer=cls.volunteer,
            application_status="pending", as_group=False
        )

        # Accept the application (organization action)
        cls.application.application_status = "accepted"
        cls.application.save()

    def setUp(self):
        self.client.force_authenticate(user=self.volunteer_account)  # Default: Volunteer logged in

    # Test Creating an Engagement (Organization Only)
    def test_create_engagement_success(self):
        create_engagement_url = reverse("opportunities_engagements:create_engagement", args=[self.application.volunteer_opportunity_application_id])
        self.client.force_authenticate(user=self.organization_account)  # Switch to organization
        response = self.client.post(create_engagement_url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Engagement successfully created.")

    def test_create_engagement_unauthorized(self):
        create_engagement_url = reverse("opportunities_engagements:create_engagement", args=[self.application.volunteer_opportunity_application_id])
        response = self.client.post(create_engagement_url)
        self.assertEqual(response.status_code, 403)

    # Test Get Engagements (Only Volunteers Can Fetch)
    def test_get_engagements_success(self):
        get_engagements_url = reverse("opportunities_engagements:get_engagements", args=[self.volunteer_account.account_uuid])
        VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )
        response = self.client.get(get_engagements_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)  # Should return 1 engagement

    def test_get_engagements_unauthorized(self):
        get_engagements_url = reverse("opportunities_engagements:get_engagements", args=[self.volunteer_account.account_uuid])
        VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )
        self.client.force_authenticate(user=self.organization_account)  # Switch to organization
        response = self.client.get(get_engagements_url)
        self.assertEqual(response.status_code, 403)

    # Test Completing Engagements (Only Organization Can Complete)
    def test_complete_engagements_success(self):
        complete_engagements_org_url = reverse("opportunities_engagements:complete_engagements_organization", args=[self.opportunity.volunteer_opportunity_id])
        VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )
        self.client.force_authenticate(user=self.organization_account)  # Switch to organization
        response = self.client.patch(complete_engagements_org_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "All engagements for this opportunity marked as completed.")

    def test_complete_engagements_unauthorized(self):
        complete_engagements_org_url = reverse("opportunities_engagements:complete_engagements_organization", args=[self.opportunity.volunteer_opportunity_id])
        VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )
        response = self.client.patch(complete_engagements_org_url)
        self.assertEqual(response.status_code, 403)

    # Test Volunteer Cancelling Their Own Engagement
    def test_cancel_engagement_volunteer_success(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )
        cancel_engagement_volunteer_url = reverse("opportunities_engagements:cancel_engagement_volunteer", args=[str(engagement.volunteer_engagement_id)])
        response = self.client.patch(cancel_engagement_volunteer_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Engagement successfully canceled.")

    def test_cancel_engagement_volunteer_unauthorized(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )
        cancel_engagement_volunteer_url = reverse("opportunities_engagements:cancel_engagement_volunteer", args=[engagement.volunteer_engagement_id])
        self.client.force_authenticate(user=self.organization_account)  # Switch to organization
        response = self.client.patch(cancel_engagement_volunteer_url)
        self.assertEqual(response.status_code, 403)

    def test_cannot_cancel_completed_engagement(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="completed"
        )
        engagement.save()
        cancel_engagement_volunteer_url = reverse("opportunities_engagements:cancel_engagement_volunteer", args=[engagement.volunteer_engagement_id])
        response = self.client.patch(cancel_engagement_volunteer_url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["error"], "Only ongoing engagements can be canceled.")

    # Test Organization Cancelling All Engagements for an Opportunity
    def test_cancel_engagements_org_success(self):
        cancel_engagements_org_url = reverse("opportunities_engagements:cancel_engagements_organization", args=[self.opportunity.volunteer_opportunity_id])
        VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )
        self.client.force_authenticate(user=self.organization_account)  # Switch to organization
        response = self.client.patch(cancel_engagements_org_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "All engagements for this opportunity marked as cancelled.")

    def test_cancel_engagements_org_unauthorized(self):
        cancel_engagements_org_url = reverse("opportunities_engagements:cancel_engagements_organization", args=[self.opportunity.volunteer_opportunity_id])
        VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )
        response = self.client.patch(cancel_engagements_org_url)
        self.assertEqual(response.status_code, 403)

    # Tests that cancelling an engagement re-increments the slots count correctly.
    def test_cancel_engagement_reincrements_slots(self):
        # Set slots initially
        self.opportunity.slots = 5
        self.opportunity.save()

        # Create an accepted volunteer application
        self.application.as_group = True  # Simulating a group application
        self.application.no_of_additional_volunteers = 2  # Applying with two extra volunteers
        self.application.application_status = "accepted"
        self.application.save()

        # Create an engagement linked to the accepted application
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application,
            volunteer=self.volunteer,
            organization=self.organization,
            engagement_status="ongoing"
        )

        cancel_engagement_volunteer_url = reverse("opportunities_engagements:cancel_engagement_volunteer", args=[str(engagement.volunteer_engagement_id)])

        self.client.force_authenticate(user=self.volunteer_account)  # Volunteer initiates cancel
        initial_slots = self.opportunity.slots

        response = self.client.patch(cancel_engagement_volunteer_url)
        self.opportunity.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Engagement successfully canceled.")
        self.assertEqual(self.opportunity.slots, initial_slots + 3)

class VolunteerOpportunitySessionAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()

        cls.volunteer_account, cls.organization_account = create_common_objects()

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

        # Create an ongoing opportunity (valid for session creation)
        cls.ongoing_opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Tree Planting",
            description="Plant trees in the community.",
            work_basis="in-person",
            duration="long-term",
            ongoing=True,
            area_of_work="education",
            requirements=["teaching"],
            languages=["English"],
            status="upcoming",
            days_of_week=["monday", "wednesday"]
        )

        # Create a non-ongoing opportunity (invalid for session creation)
        cls.non_ongoing_opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Org1 Opportunity 1",
            description="Description 1",
            work_basis="in-person",
            duration="short-term",
            ongoing=False,
            opportunity_date=date.today() + timedelta(days=10),
            opportunity_time_from="09:00:00",
            opportunity_time_to="12:00:00",
            area_of_work="education",
            requirements=["teaching"],
            languages=["English"],
            status="upcoming"
        )

        # Create a session for testing get, complete, and cancel operations
        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.ongoing_opportunity,
            title="Tree Planting Session 1",
            description="Planting session at a local park.",
            session_date=date.today() + timedelta(days=3),
            session_start_time=time(9, 0),
            session_end_time=time(12, 0),
            status="upcoming"
        )

        # Define endpoint URLs
        cls.create_session_url = reverse(
            "opportunities_engagements:create_session",
            args=[str(cls.ongoing_opportunity.volunteer_opportunity_id)]
        )
        cls.get_sessions_url = reverse(
            "opportunities_engagements:get_sessions",
            args=[str(cls.ongoing_opportunity.volunteer_opportunity_id)]
        )
        cls.complete_session_url = reverse(
            "opportunities_engagements:complete_session",
            args=[str(cls.session.session_id)]
        )
        cls.cancel_session_url = reverse(
            "opportunities_engagements:cancel_session",
            args=[str(cls.session.session_id)]
        )

    def setUp(self):
        self.client.force_authenticate(user=self.organization_account)

    ## CREATE SESSION TESTS
    def test_create_session_success(self):
        data = {
            "title": "New Session",
            "description": "Session for tree planting",
            "session_date": str(date.today() + timedelta(days=5)),
            "session_start_time": "10:00:00",
            "session_end_time": "12:00:00",
            "status": "upcoming"
        }
        response = self.client.post(self.create_session_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Session created successfully.")

    def test_create_session_unauthorized(self):
        self.client.force_authenticate(user=self.volunteer_account)
        data = {
            "title": "Unauthorized Session",
            "session_date": str(date.today() + timedelta(days=5)),
            "session_start_time": "10:00:00",
            "session_end_time": "12:00:00"
        }
        response = self.client.post(self.create_session_url, data, format="json")
        self.assertEqual(response.status_code, 403)

    def test_create_session_non_ongoing_opportunity(self):
        url = reverse(
            "opportunities_engagements:create_session",
            args=[str(self.non_ongoing_opportunity.volunteer_opportunity_id)]
        )
        data = {
            "title": "Invalid Session",
            "session_date": str(date.today() + timedelta(days=5)),
            "session_start_time": "10:00:00",
            "session_end_time": "12:00:00"
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, 400)

    ## GET SESSIONS TEST
    def test_get_sessions(self):
        response = self.client.get(self.get_sessions_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_sessions_invalid_opportunity(self):
        url = reverse(
            "opportunities_engagements:get_sessions",
            args=["123e4567-e89b-12d3-a456-426614174000"]
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    ## COMPLETE SESSION TESTS
    def test_complete_session_success(self):
        response = self.client.patch(self.complete_session_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Session marked as completed.")

    def test_complete_session_unauthorized(self):
        self.client.force_authenticate(user=self.volunteer_account)
        response = self.client.patch(self.complete_session_url)
        self.assertEqual(response.status_code, 403)

    def test_complete_session_already_completed(self):
        self.session.status = "completed"
        self.session.save()

        response = self.client.patch(self.complete_session_url)
        self.assertEqual(response.status_code, 400)

    ## CANCEL SESSION TESTS
    def test_cancel_session_success(self):
        response = self.client.patch(self.cancel_session_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Session successfully cancelled.")

    def test_cancel_session_unauthorized(self):
        self.client.force_authenticate(user=self.volunteer_account)
        response = self.client.patch(self.cancel_session_url)
        self.assertEqual(response.status_code, 403)

    def test_cancel_session_already_cancelled(self):
        self.session.status = "cancelled"
        self.session.save()

        response = self.client.patch(self.cancel_session_url)
        self.assertEqual(response.status_code, 400)

class VolunteerSessionEngagementAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()

        cls.organization_account = Account.objects.create_user(
            email_address="org@example.com",
            password="password123",
            user_type="organization",
            contact_number="+35612345678"
        )
        cls.volunteer_account = Account.objects.create_user(
            email_address="volunteer@example.com",
            password="password123",
            user_type="volunteer",
            contact_number="+35698765432"
        )

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Green Earth",
            organization_description="A non-profit for environmental projects",
        )
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )

        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Tree Planting",
            description="Plant trees in the community.",
            work_basis="in-person",
            duration="long-term",
            ongoing=True,
            area_of_work="education",
            requirements=["teaching"],
            languages=["English"],
            status="upcoming",
            days_of_week=["monday", "wednesday"]
        )

        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application,
            volunteer=cls.volunteer,
            organization=cls.organization
        )

        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.opportunity,
            title="Weekly Tree Planting",
            description="Join us every Saturday!",
            session_date=timezone.now().date() + timedelta(days=3),
            session_start_time="09:00:00",
            session_end_time="12:00:00",
            status="upcoming",
            slots=5
        )

        cls.create_session_engagements_for_session_url = reverse(
            "opportunities_engagements:create_session_engagements_for_session",
            args=[str(cls.session.session_id)]
        )

    def setUp(self):
        self.client.force_authenticate(user=self.organization_account)

    # Organization creates session engagements for a session
    def test_create_session_engagements_for_session_success(self):
        response = self.client.post(self.create_session_engagements_for_session_url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Session engagements created successfully.")

    # Organization creates session engagements for a volunteer
    def test_create_session_engagements_for_volunteer_success(self):
        create_session_engagements_for_volunteer_url = reverse(
            "opportunities_engagements:create_session_engagements_for_volunteer",
            args=[str(self.volunteer.account.account_uuid), str(self.opportunity.volunteer_opportunity_id)]
        )

        response = self.client.post(create_session_engagements_for_volunteer_url)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Session engagements created successfully.")

        # Ensure session engagements were created for all upcoming sessions in the opportunity
        created_session_engagements = VolunteerSessionEngagement.objects.filter(
            volunteer_engagement=self.engagement
        )
        self.assertTrue(created_session_engagements.exists())
        self.assertEqual(created_session_engagements.count(), 1)  # Should match the number of upcoming sessions

        # Ensure the correct status was assigned
        for session_engagement in created_session_engagements:
            self.assertEqual(session_engagement.status, "cant_go")

    # Volunteer confirms attendance
    def test_confirm_attendance_success(self):
        session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="cant_go"
        )
        confirm_attendance_url = reverse(
            "opportunities_engagements:confirm_attendance",
            args=[str(session_engagement.session_engagement_id)]
        )

        self.client.force_authenticate(user=self.volunteer_account)
        response = self.client.patch(confirm_attendance_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Attendance confirmed.")

    # Volunteer cancels attendance
    def test_cancel_attendance_success(self):
        session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="can_go"
        )
        cancel_attendance_url = reverse(
            "opportunities_engagements:cancel_attendance",
            args=[str(session_engagement.session_engagement_id)]
        )

        self.client.force_authenticate(user=self.volunteer_account)
        response = self.client.patch(cancel_attendance_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Attendance canceled.")

    # Volunteer confirms attendance - Slot should decrement
    def test_confirm_attendance_reduces_slots(self):
        session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="cant_go"
        )
        confirm_attendance_url = reverse(
            "opportunities_engagements:confirm_attendance",
            args=[str(session_engagement.session_engagement_id)]
        )

        self.client.force_authenticate(user=self.volunteer_account)

        # Get initial slots
        initial_slots = self.session.slots
        response = self.client.patch(confirm_attendance_url)
        self.session.refresh_from_db()  # Refresh from DB to check slot count update

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Attendance confirmed.")
        self.assertEqual(self.session.slots, initial_slots - 1)  # Slots should decrement

    # Volunteer cancels attendance - Slot should increment
    def test_cancel_attendance_increases_slots(self):
        session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="can_go"
        )
        cancel_attendance_url = reverse(
            "opportunities_engagements:cancel_attendance",
            args=[str(session_engagement.session_engagement_id)]
        )

        self.client.force_authenticate(user=self.volunteer_account)

        # Get initial slots
        initial_slots = self.session.slots
        response = self.client.patch(cancel_attendance_url)
        self.session.refresh_from_db()  # Refresh from DB to check slot count update

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Attendance canceled.")
        self.assertEqual(self.session.slots, initial_slots + 1)  # Slots should increment

    # Organization retrieves session engagements
    def test_get_session_engagements_success(self):
        session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="can_go"
        )
        get_session_engagements_url = reverse(
            "opportunities_engagements:get_session_engagements",
            args=[str(self.session.session_id)]
        )

        response = self.client.get(get_session_engagements_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_get_volunteer_session_engagements_success(self):
        session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="can_go"
        )
        get_volunteer_session_engagements_url = reverse(
            "opportunities_engagements:get_volunteer_session_engagements",
            args=[str(self.volunteer.account.account_uuid)]
        )

        self.client.force_authenticate(user=self.volunteer_account)
        response = self.client.get(get_volunteer_session_engagements_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["session_engagement_id"], str(session_engagement.session_engagement_id))

class VolunteerEngagementLogAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.client = APIClient()
        cls.volunteer_account, cls.organization_account = create_common_objects()

        # Create volunteer and organization profiles
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )
        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="Non-profit organization."
        )

        # One-time opportunity (for one-time engagement logs)
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="One-Time Cleanup",
            description="A one-time beach cleanup event.",
            work_basis="in-person",
            duration="short-term",
            ongoing=False,
            opportunity_date=date.today() - timedelta(days=2),  # Past event
            opportunity_time_from=time(9, 0),
            opportunity_time_to=time(12, 0),
            slots=10,
            area_of_work="environment",
            requirements=["physical fitness"],
            status="completed"
        )

        cls.application_one_time = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        cls.engagement_one_time = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application_one_time,
            volunteer=cls.volunteer,
            organization=cls.organization,
            engagement_status="completed"
        )

        # Ongoing opportunity (for session engagement logs)
        cls.ongoing_opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Ongoing Teaching",
            description="Teaching English weekly.",
            work_basis="in-person",
            duration="long-term",
            ongoing=True,
            slots=None,
            area_of_work="education",
            requirements=["teaching"],
            status="upcoming"
        )

        cls.application_ongoing = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.ongoing_opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        cls.engagement_ongoing = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application_ongoing,
            volunteer=cls.volunteer,
            organization=cls.organization,
            engagement_status="ongoing"
        )

        # Create a session for the ongoing opportunity
        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.ongoing_opportunity,
            title="Teaching Session",
            description="Weekly session for teaching English.",
            session_date=date.today() - timedelta(days=1),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            status="completed"
        )

        cls.session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=cls.engagement_ongoing,
            session=cls.session,
            status="can_go"
        )

    def setUp(self):
        self.client.force_authenticate(user=self.volunteer_account)  # Default: Volunteer logged in

    # Test Creating Engagement Logs for a One-Time Opportunity
    def test_create_opportunity_engagement_logs_success(self):
        create_logs_url = reverse("opportunities_engagements:create_opportunity_engagement_logs", args=[self.opportunity.volunteer_opportunity_id])
        self.client.force_authenticate(user=self.organization_account)

        response = self.client.post(create_logs_url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Engagement logs created successfully.")

    def test_create_opportunity_engagement_logs_unauthorized(self):
        create_logs_url = reverse("opportunities_engagements:create_opportunity_engagement_logs", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.post(create_logs_url)
        self.assertEqual(response.status_code, 403)  # Volunteers can't create logs for others

    # Test Creating Session Engagement Logs for a Completed Session
    def test_create_session_engagement_logs_success(self):
        create_session_logs_url = reverse("opportunities_engagements:create_session_engagement_logs", args=[self.session.session_id])
        self.client.force_authenticate(user=self.organization_account)

        response = self.client.post(create_session_logs_url)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Session engagement logs created successfully.")

    def test_create_session_engagement_logs_unauthorized(self):
        create_session_logs_url = reverse("opportunities_engagements:create_session_engagement_logs", args=[self.session.session_id])
        response = self.client.post(create_session_logs_url)
        self.assertEqual(response.status_code, 403)  # Volunteers can't create logs for sessions

    # Test Volunteers Creating Their Own Logs for an Ongoing Opportunity
    def test_create_engagement_log_volunteer_success(self):
        create_log_url = reverse("opportunities_engagements:create_engagement_log_volunteer", args=[self.ongoing_opportunity.volunteer_opportunity_id])

        data = {
            "volunteer_engagement_id": self.engagement_ongoing.pk,
            "no_of_hours": 2,
            "log_notes": "Tutored students in English"
        }
        response = self.client.post(create_log_url, data, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["message"], "Engagement log submitted for approval.")

    def test_create_engagement_log_volunteer_invalid_hours(self):
        create_log_url = reverse("opportunities_engagements:create_engagement_log_volunteer", args=[self.ongoing_opportunity.volunteer_opportunity_id])

        data = {
            "volunteer_engagement_id": self.engagement_ongoing.pk,
            "no_of_hours": -1,  # Invalid hours
            "log_notes": "Tutored students in English"
        }
        response = self.client.post(create_log_url, data)
        self.assertEqual(response.status_code, 400)  # Validation error

    # Test Approving an Engagement Log
    def test_approve_engagement_log_success(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement_ongoing,
            no_of_hours=2,
            status="pending",
            log_notes="Tutored students in English",
            is_volunteer_request=True
        )

        approve_log_url = reverse("opportunities_engagements:approve_engagement_log", args=[log.volunteer_engagement_log_id])
        self.client.force_authenticate(user=self.organization_account)

        response = self.client.patch(approve_log_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Engagement log approved.")

    def test_approve_engagement_log_unauthorized(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement_ongoing,
            no_of_hours=2,
            status="pending",
            log_notes="Tutored students in English",
            is_volunteer_request=True
        )

        approve_log_url = reverse("opportunities_engagements:approve_engagement_log", args=[log.volunteer_engagement_log_id])
        response = self.client.patch(approve_log_url)
        self.assertEqual(response.status_code, 403)  # Volunteers can't approve logs

    # Test Rejecting an Engagement Log
    def test_reject_engagement_log_success(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement_ongoing,
            no_of_hours=2,
            status="pending",
            log_notes="Tutored students in English",
            is_volunteer_request=True
        )

        reject_log_url = reverse("opportunities_engagements:reject_engagement_log", args=[log.volunteer_engagement_log_id])
        self.client.force_authenticate(user=self.organization_account)

        response = self.client.patch(reject_log_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["message"], "Engagement log rejected successfully.")

class GetPendingOrganizationLogRequestsAPITest(APITestCase):
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

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="Non-profit organization."
        )

        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Ongoing Teaching",
            description="Teaching English weekly.",
            work_basis="in-person",
            duration="long-term",
            ongoing=True,
            slots=None,
            area_of_work="education",
            requirements=["teaching"],
            status="upcoming"
        )

        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application,
            volunteer=cls.volunteer,
            organization=cls.organization,
            engagement_status="ongoing"
        )

        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.opportunity,
            title="Teaching Session",
            description="Weekly session for teaching English.",
            session_date=date.today() - timedelta(days=1),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            status="completed"
        )

        cls.session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=cls.engagement,
            session=cls.session,
            status="can_go"
        )

        cls.pending_log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=cls.engagement,
            no_of_hours=2,
            status="pending",
            log_notes="Tutored students.",
            is_volunteer_request=True
        )

        cls.approved_log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=cls.engagement,
            session=cls.session_engagement,
            no_of_hours=3,
            status="approved",
            log_notes="Assisted in classroom activities."
        )

    def setUp(self):
        self.client.force_authenticate(user=self.organization_account)

    # Organization should successfully retrieve pending engagement log requests.
    def test_get_organization_log_requests_success(self):
        get_logs_url = reverse("opportunities_engagements:get_organization_log_requests", args=[self.organization.account.account_uuid])
        response = self.client.get(get_logs_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)  # Only pending logs should be returned
        self.assertEqual(response.data[0]["status"], "pending")

    # Volunteers should not be able to access organization log requests.
    def test_get_organization_log_requests_unauthorized(self):
        self.client.force_authenticate(user=self.volunteer_account)  # Switch to volunteer
        get_logs_url = reverse("opportunities_engagements:get_organization_log_requests", args=[self.organization.account.account_uuid])
        response = self.client.get(get_logs_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Only organizations can view log requests.")

class GetVolunteerEngagementLogsAPITest(APITestCase):
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

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="Non-profit organization."
        )

        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Ongoing Teaching",
            description="Teaching English weekly.",
            work_basis="in-person",
            duration="long-term",
            ongoing=True,
            slots=None,
            area_of_work="education",
            requirements=["teaching"],
            status="upcoming"
        )

        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application,
            volunteer=cls.volunteer,
            organization=cls.organization,
            engagement_status="ongoing"
        )
        
        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.opportunity,
            title="Teaching Session",
            description="Weekly session for teaching English.",
            session_date=date.today() - timedelta(days=1),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            status="completed"
        )

        cls.session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=cls.engagement,
            session=cls.session,
            status="can_go"
        )

        cls.approved_log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=cls.engagement,
            session=cls.session_engagement,
            no_of_hours=3,
            status="approved",
            log_notes="Assisted in classroom activities."
        )

        cls.rejected_log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=cls.engagement,
            no_of_hours=2,
            status="rejected",
            log_notes="Tutored students.",
            is_volunteer_request=True
        )

    def setUp(self):
        self.client.force_authenticate(user=self.volunteer_account)

    # Volunteers should successfully retrieve only their approved engagement logs.
    def test_get_engagement_logs_success(self):
        get_logs_url = reverse("opportunities_engagements:get_engagement_logs", args=[self.volunteer_account.account_uuid])
        response = self.client.get(get_logs_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)  # Only approved logs should be returned
        self.assertEqual(response.data[0]["status"], "approved")

    # Organizations should not be able to fetch engagement logs for volunteers.
    def test_get_engagement_logs_unauthorized(self):
        self.client.force_authenticate(user=self.organization_account)  # Switch to organization
        get_logs_url = reverse("opportunities_engagements:get_engagement_logs", args=[self.volunteer_account.account_uuid])
        response = self.client.get(get_logs_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Only volunteers can view their engagement logs.")

class GetVolunteerLogRequestsAPITest(APITestCase):
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

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="Non-profit organization."
        )

        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Ongoing Teaching",
            description="Teaching English weekly.",
            work_basis="in-person",
            duration="long-term",
            ongoing=True,
            slots=None,
            area_of_work="education",
            requirements=["teaching"],
            status="upcoming"
        )

        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application,
            volunteer=cls.volunteer,
            organization=cls.organization,
            engagement_status="completed"
        )

        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.opportunity,
            title="Neighborhood Cleanup",
            description="Cleaning parks and streets.",
            session_date=date.today() - timedelta(days=1),
            session_start_time=time(10, 0),
            session_end_time=time(14, 0),
            status="completed"
        )

        cls.session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=cls.engagement,
            session=cls.session,
            status="can_go"
        )

        # Log request made by volunteer (Pending)
        cls.pending_log_request = VolunteerEngagementLog.objects.create(
            volunteer_engagement=cls.engagement,
            session=cls.session_engagement,
            no_of_hours=4,
            status="pending",
            log_notes="Helped clean the main street.",
            is_volunteer_request=True
        )

        # Organization-approved log (should NOT be returned in the request)
        cls.approved_log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=cls.engagement,
            session=cls.session_engagement,
            no_of_hours=3,
            status="approved",
            log_notes="Assisted in park cleanup."
        )

    def setUp(self):
        self.client.force_authenticate(user=self.volunteer_account)

    # Volunteers should successfully retrieve only their pending log requests.
    def test_get_volunteer_log_requests_success(self):
        get_log_requests_url = reverse("opportunities_engagements:get_volunteer_log_requests", args=[self.volunteer_account.account_uuid])
        response = self.client.get(get_log_requests_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)  # Only pending volunteer-requested logs should be returned
        self.assertEqual(response.data[0]["status"], "pending")
        self.assertTrue(response.data[0]["is_volunteer_request"])

    # Organizations should not be able to fetch volunteer log requests.
    def test_get_volunteer_log_requests_unauthorized(self):
        self.client.force_authenticate(user=self.organization_account)  # Switch to organization
        get_log_requests_url = reverse("opportunities_engagements:get_volunteer_log_requests", args=[self.volunteer_account.account_uuid])
        response = self.client.get(get_log_requests_url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.data["error"], "Only volunteers can view their engagement log requests.")