from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch
from datetime import date, timedelta
from volunteers_organizations.models import Organization, Volunteer, VolunteerMatchingPreferences
from opportunities_engagements.models import VolunteerOpportunity, VolunteerOpportunityApplication, VolunteerEngagement, VolunteerEngagementLog, VolunteerOpportunitySession, VolunteerSessionEngagement
from accounts_notifs.tasks import send_notification
from accounts_notifs.models import Notification
from unittest.mock import call
from datetime import date, time

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

class ApplicationSubmittedSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create base accounts
        cls.volunteer_account, cls.organization_account = create_common_objects()

        # Create a volunteer profile
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="Jane",
            last_name="Doe",
            dob=date(1990, 1, 1)
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
            title="Community Cleanup",
            description="Help clean up the local park!",
            organization=cls.organization,
            work_basis="in-person",
            duration="short-term",
            opportunity_date="2025-04-01",
            opportunity_time_from="09:00:00",
            opportunity_time_to="12:00:00",
            area_of_work="environment",
            requirements=["teamwork"],
            ongoing=False,
            status="upcoming"
        )

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.volunteer_account)

    # Test that submitting an application triggers the notification
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_application_submitted_triggers_notification(self, mock_task):
        url = reverse("opportunities_engagements:create_application", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(VolunteerOpportunityApplication.objects.filter(volunteer=self.volunteer, volunteer_opportunity=self.opportunity).exists())

        # Ensure Celery task was triggered with correct parameters
        mock_task.assert_called_once_with(
            recipient_id=str(self.organization.account.account_uuid),
            notification_type="application_submitted",
            message="Jane Doe has applied to Community Cleanup."
        )

    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_application_accepted_triggers_notification(self, mock_task):
        # Volunteer applies for opportunity
        self.client.force_authenticate(user=self.volunteer_account)
        application_url = reverse("opportunities_engagements:create_application", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.post(application_url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get the created application
        application = VolunteerOpportunityApplication.objects.first()
        self.assertEqual(application.application_status, "pending")  # Should initially be pending

        # Accept the application
        self.client.force_authenticate(user=self.organization_account)
        accept_url = reverse("opportunities_engagements:accept_application", args=[application.volunteer_opportunity_application_id])
        response = self.client.patch(accept_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.application_status, "accepted")

        mock_task.assert_has_calls([
            call(
                recipient_id=str(self.organization.account.account_uuid),
                notification_type="application_submitted",
                message="Jane Doe has applied to Community Cleanup."
            ),
            call(
                recipient_id=str(self.volunteer_account.account_uuid),
                notification_type="application_accepted",
                message="Your application for 'Community Cleanup' has been accepted!"
            )
        ], any_order=True)

    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_application_rejected_triggers_notification(self, mock_task):
        # Volunteer applies for opportunity
        self.client.force_authenticate(user=self.volunteer_account)
        application_url = reverse("opportunities_engagements:create_application", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.post(application_url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Get the created application
        application = VolunteerOpportunityApplication.objects.first()
        self.assertEqual(application.application_status, "pending")  # Should initially be pending

        # Reject the application
        self.client.force_authenticate(user=self.organization_account)
        reject_url = reverse("opportunities_engagements:reject_application", args=[application.volunteer_opportunity_application_id])
        response = self.client.patch(reject_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.application_status, "rejected")

        # Ensure Celery task was triggered
        mock_task.assert_has_calls([
            call(
                recipient_id=str(self.organization.account.account_uuid),
                notification_type="application_submitted",
                message="Jane Doe has applied to Community Cleanup."
            ),
            call(
                recipient_id=str(self.volunteer_account.account_uuid),
                notification_type="application_rejected",
                message="Unfortunately, your application for 'Community Cleanup' was rejected."
            )
        ], any_order=True)

class EngagementLogSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
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
            organization_description="A non-profit organization.",
            organization_address={'raw': '123 Help St, Kindness City, US'}
        )

        cls.opportunity = VolunteerOpportunity.objects.create(
            title="Community Cleanup",
            description="Help clean up the local park!",
            organization=cls.organization,
            work_basis="in-person",
            duration="short-term",
            area_of_work="environment",
            requirements=["teamwork"],
            ongoing=True,
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

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.volunteer_account)

    # Test if a log request submission triggers a notification to the organization.
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_log_request_triggers_notification(self, mock_task):
        url = reverse("opportunities_engagements:create_engagement_log_volunteer", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.post(url, {"no_of_hours": 3, "log_notes": "Gathered 10 garbage bags!"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(VolunteerEngagementLog.objects.filter(volunteer_engagement=self.engagement).exists())

        # Ensure Celery task was triggered with correct parameters
        mock_task.assert_called_once_with(
            recipient_id=str(self.organization_account.account_uuid),
            notification_type="log_request_submitted",
            message="John Doe has submitted a new engagement log request for Community Cleanup."
        )

class OpportunityActionsSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create base users
        cls.volunteer_account_1, cls.organization_account = create_common_objects()

        cls.volunteer_account_2 = Account.objects.create(
            email_address='volunteer2@test.com',
            password='testerpassword',
            user_type='volunteer',
            contact_number="+35612345672"
        )

        cls.volunteer_account_3 = Account.objects.create(
            email_address='volunteer3@test.com',
            password='testerpassword',
            user_type='volunteer',
            contact_number="+35612345673"
        )

        cls.volunteer_1 = Volunteer.objects.create(
            account=cls.volunteer_account_1,
            first_name="Alice",
            last_name="Smith",
            dob=date(1996, 2, 2)
        )

        cls.volunteer_2 = Volunteer.objects.create(
            account=cls.volunteer_account_2,
            first_name="Bob",
            last_name="Johnson",
            dob=date(1997, 3, 3)
        )

        cls.volunteer_3 = Volunteer.objects.create(
            account=cls.volunteer_account_3,
            first_name="Charlie",
            last_name="Brown",
            dob=date(1998, 4, 4)
        )

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="A non-profit organization.",
            organization_address={'raw': '456 Charity Rd, Kindness City, US'}
        )

        # Create an ongoing volunteer opportunity
        cls.opportunity = VolunteerOpportunity.objects.create(
            title="Community Cleanup",
            description="Help clean up the local park!",
            organization=cls.organization,
            work_basis="in-person",
            duration="short-term",
            opportunity_date="2025-04-01",
            opportunity_time_from="09:00:00",
            opportunity_time_to="12:00:00",
            area_of_work="environment",
            requirements=["teamwork"],
            ongoing=True,  # This makes it an ongoing opportunity (so sessions can exist)
            status="upcoming"
        )

        # Create applications & accept them
        for volunteer in [cls.volunteer_1, cls.volunteer_2, cls.volunteer_3]:
            application = VolunteerOpportunityApplication.objects.create(
                volunteer=volunteer,
                volunteer_opportunity=cls.opportunity,
                application_status="accepted"
            )
            VolunteerEngagement.objects.create(
                volunteer_opportunity_application=application,
                engagement_status="ongoing"
            )

    def setUp(self):
        self.client = APIClient()

    # Test that cancelling an opportunity notifies engaged volunteers
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_opportunity_cancelled_triggers_notification(self, mock_task):
        self.client.force_authenticate(user=self.organization_account)
        url = reverse("opportunities_engagements:cancel_opportunity", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.patch(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.opportunity.refresh_from_db()
        self.assertEqual(self.opportunity.status, "cancelled")

        # Ensure notification was sent to each engaged volunteer
        self.assertEqual(mock_task.call_count, 3)
        for volunteer in [self.volunteer_account_1, self.volunteer_account_2, self.volunteer_account_3]:
            mock_task.assert_any_call(
                recipient_id=str(volunteer.account_uuid),
                notification_type="opportunity_cancelled",
                message="The opportunity Community Cleanup has been cancelled."
            )

    # Test that completing an opportunity notifies engaged volunteers
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_opportunity_completed_triggers_notification(self, mock_task):
        self.client.force_authenticate(user=self.organization_account)
        url = reverse("opportunities_engagements:complete_opportunity", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.opportunity.refresh_from_db()
        self.assertEqual(self.opportunity.status, "completed")

        # Ensure notification was sent to each engaged volunteer
        self.assertEqual(mock_task.call_count, 3)
        for volunteer in [self.volunteer_account_1, self.volunteer_account_2, self.volunteer_account_3]:
            mock_task.assert_any_call(
                recipient_id=str(volunteer.account_uuid),
                notification_type="opportunity_completed",
                message="The opportunity Community Cleanup has been successfully completed!"
            )

    # Test that creating a session notifies engaged volunteers
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_new_session_triggers_notification(self, mock_task):
        self.client.force_authenticate(user=self.organization_account)
        url = reverse("opportunities_engagements:create_session", args=[self.opportunity.volunteer_opportunity_id])
        response = self.client.post(url, {"title": "Park Cleanup - Week 2", "description": "Next cleanup", "session_date": "2025-04-09", "session_start_time": "10:00", "session_end_time": "12:00", "status": "upcoming"})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(VolunteerOpportunitySession.objects.filter(title="Park Cleanup - Week 2").exists())

        # Ensure notification was sent to each engaged volunteer
        self.assertEqual(mock_task.call_count, 3)
        for volunteer in [self.volunteer_account_1, self.volunteer_account_2, self.volunteer_account_3]:
            mock_task.assert_any_call(
                recipient_id=str(volunteer.account_uuid),
                notification_type="new_opportunity_session",
                message="A new session for Community Cleanup has been scheduled. Check it out!"
            )

class SessionActionSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create base accounts
        cls.volunteer_account_1, cls.organization_account = create_common_objects()

        cls.volunteer_account_2 = Account.objects.create(email_address="volunteer2@test.com", password="password", user_type="volunteer", contact_number="+35612345672")
        cls.volunteer_account_3 = Account.objects.create(email_address="volunteer3@test.com", password="password", user_type="volunteer", contact_number="+35612345673")
        
        cls.volunteer_1 = Volunteer.objects.create(account=cls.volunteer_account_1, first_name="Alice", last_name="Smith", dob=date(1996, 2, 2))
        cls.volunteer_2 = Volunteer.objects.create(account=cls.volunteer_account_2, first_name="Bob", last_name="Johnson", dob=date(1997, 3, 3))
        cls.volunteer_3 = Volunteer.objects.create(account=cls.volunteer_account_3, first_name="Charlie", last_name="Brown", dob=date(1998, 4, 4))

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="A non-profit organization.",
            organization_address={'raw': '456 Charity Rd, Kindness City, US'}
        )

        cls.opportunity = VolunteerOpportunity.objects.create(
            title="Beach Cleanup",
            description="Clean up the beach!",
            organization=cls.organization,
            work_basis="in-person",
            duration="long-term",
            area_of_work="environment",
            requirements=["teamwork"],
            ongoing=True,
            status="upcoming",
        )

        cls.application_1 = VolunteerOpportunityApplication.objects.create(volunteer=cls.volunteer_1, volunteer_opportunity=cls.opportunity, application_status="accepted")
        cls.application_2 = VolunteerOpportunityApplication.objects.create(volunteer=cls.volunteer_2, volunteer_opportunity=cls.opportunity, application_status="accepted")
        cls.application_3 = VolunteerOpportunityApplication.objects.create(volunteer=cls.volunteer_3, volunteer_opportunity=cls.opportunity, application_status="accepted")

        cls.engagement_1 = VolunteerEngagement.objects.create(volunteer_opportunity_application=cls.application_1, volunteer=cls.volunteer_1, engagement_status="ongoing")
        cls.engagement_2 = VolunteerEngagement.objects.create(volunteer_opportunity_application=cls.application_2, volunteer=cls.volunteer_2, engagement_status="ongoing")
        cls.engagement_3 = VolunteerEngagement.objects.create(volunteer_opportunity_application=cls.application_3, volunteer=cls.volunteer_3, engagement_status="ongoing")
    
        # Create a session for the opportunity
        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.opportunity,
            title="Beach Cleanup Session 1",
            description="Join us for a cleanup!",
            session_date=date(2025, 4, 1),
            session_start_time=time(9, 0),
            session_end_time=time(12, 0),
            status="upcoming",
        )

        # Create session engagements
        cls.session_engagement_1 = VolunteerSessionEngagement.objects.create(session=cls.session, volunteer_engagement=cls.engagement_1, status="can_go")
        cls.session_engagement_2 = VolunteerSessionEngagement.objects.create(session=cls.session, volunteer_engagement=cls.engagement_2, status="can_go")
        cls.session_engagement_3 = VolunteerSessionEngagement.objects.create(session=cls.session, volunteer_engagement=cls.engagement_3, status="cant_go")  # This volunteer should NOT be notified

    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.organization_account)

    # Test Session Completion Notification
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_session_completed_triggers_notification(self, mock_task):
        url = reverse("opportunities_engagements:complete_session", args=[self.session.session_id])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "completed")

        # Ensure only `can_go` attendees were notified
        self.assertEqual(mock_task.call_count, 2)  # Only 2 attendees marked as `can_go`

        mock_task.assert_any_call(
            recipient_id=str(self.volunteer_account_1.account_uuid),
            notification_type="session_completed",
            message="The session Beach Cleanup Session 1 has been completed!"
        )

        mock_task.assert_any_call(
            recipient_id=str(self.volunteer_account_2.account_uuid),
            notification_type="session_completed",
            message="The session Beach Cleanup Session 1 has been completed!"
        )

    # Test Session Cancellation Notification
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_session_cancelled_triggers_notification(self, mock_task):
        url = reverse("opportunities_engagements:cancel_session", args=[self.session.session_id])
        response = self.client.patch(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.session.refresh_from_db()
        self.assertEqual(self.session.status, "cancelled")

        # Ensure only `can_go` attendees were notified
        self.assertEqual(mock_task.call_count, 2)  # Only 2 attendees marked as `can_go`

        mock_task.assert_any_call(
            recipient_id=str(self.volunteer_account_1.account_uuid),
            notification_type="session_cancelled",
            message="The session Beach Cleanup Session 1 has been cancelled."
        )

        mock_task.assert_any_call(
            recipient_id=str(self.volunteer_account_2.account_uuid),
            notification_type="session_cancelled",
            message="The session Beach Cleanup Session 1 has been cancelled."
        )

### SMART MATCHING ALGORITHM TESTING ###
class SmartMatchingSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account_1, cls.organization_account = create_common_objects()
        cls.volunteer_account_2 = Account.objects.create(email_address="volunteer2@test.com", password="password", user_type="volunteer", contact_number="+35612345272")    
        cls.volunteer_account_3 = Account.objects.create(email_address="volunteer3@test.com", password="password", user_type="volunteer", contact_number="+35612345973")

        cls.volunteer_1 = Volunteer.objects.create(account=cls.volunteer_account_1, first_name="Alice", last_name="Smith", dob=date(1996, 2, 2))
        cls.volunteer_2 = Volunteer.objects.create(account=cls.volunteer_account_2, first_name="Bob", last_name="Johnson", dob=date(1997, 3, 3))
        cls.volunteer_3 = Volunteer.objects.create(account=cls.volunteer_account_3, first_name="Charlie", last_name="Brown", dob=date(1998, 4, 4))

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="Non-profit organization.",
            organization_address={'raw': '123 Help St, Kindness City, US'}
        )

        cls.volunteer_preference_1 = VolunteerMatchingPreferences.objects.create(
            volunteer=cls.volunteer_1,
            availability=["monday"],
            preferred_work_types="in-person",
            preferred_duration=["short-term"],
            fields_of_interest=["environment"],
            skills=["teamwork"],
            languages=["English"],
            location={"lat": 35.9, "lon": 14.5, "formatted_address": "Kindness City", "city": "Kindness City"}
        )

        cls.volunteer_preference_2 = VolunteerMatchingPreferences.objects.create(
            volunteer=cls.volunteer_2,
            availability=["friday"],
            preferred_work_types="online",
            preferred_duration=["long-term"],
            fields_of_interest=["health", "education"],
            skills=["communication"],
            languages=["French"],
            location={"lat": 36.0, "lon": 14.7, "formatted_address": "Different City", "city": "Different City"}
        )

        cls.volunteer_preference_3 = VolunteerMatchingPreferences.objects.create(
            volunteer=cls.volunteer_3,
            availability=["sunday"],
            preferred_work_types="both",
            preferred_duration=["medium-term"],
            fields_of_interest=["arts"],
            skills=["photography"],
            languages=["Spanish"],
            location={"lat": 37.0, "lon": 14.8, "formatted_address": "Far Away", "city": "Far Away"}
        )
    
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(user=self.organization_account)

    # Test that opportunity 1 triggers a match for volunteer 1 with partial matching.
    @patch("opportunities_engagements.signals.send_mail") 
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_opportunity_1_triggers_matching_for_volunteer_1(self, mock_notification, mock_mail):
        url = reverse("opportunities_engagements:create_opportunity")
        data = {
            "title": "Beach Cleanup",
            "description": "Join us to clean the beach!",
            "work_basis": "in-person",  # Matches Volunteer 1
            "duration": "medium-term",  # Volunteer 1 prefers short-term
            "area_of_work": "environment",  # Matches Volunteer 1
            "requirements": ["teamwork", "leadership"],  # Matches (teamwork), extra (leadership)
            "required_location": {"lat": 36.0, "lon": 14.6, "formatted_address": "Nearby City", "city": "Nearby City"},
            "languages": ["English", "French"],  # Matches one language
            "days_of_week": ["tuesday"],  # Volunteer 1 is available on Monday
            "status": "upcoming",
            "ongoing": True    
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        opportunity_id = response.data.get("data", {}).get("volunteer_opportunity_id")
        self.assertIsNotNone(opportunity_id, "Opportunity ID should not be None!")

        # Expected match percentages
        expected_match_v1 = 80  # Volunteer 1 (above 65%, so notified)
        expected_match_v2 = 55  # Volunteer 2 (below 65%, so not notified)
        expected_match_v3 = 50  # Volunteer 3 (below 65%, so not notified)

        # Only Volunteer 1 should be notified
        mock_notification.assert_called_once_with(
            recipient_id=str(self.volunteer_account_1.account_uuid),
            notification_type="opportunity_match",
            message=f"You are a {expected_match_v1}% match for 'Beach Cleanup' (14.3 km away) by Helping Hands. Check it out!"
        )

        mock_mail.assert_called_once()
        mock_mail.assert_called_with(
            f"You're a great match ({expected_match_v1}%) for a new opportunity!",
            (
                f"Hi {self.volunteer_1.first_name} {self.volunteer_1.last_name},\n\n"
                "We found a new volunteering opportunity that matches your interests!\n\n"
                f"[View Opportunity & Apply](https://volontera.com/opportunity/{response.data['data']['volunteer_opportunity_id']})\n\n"
                "Happy Volunteering!"
            ),
            "volonteracm3070@gmail.com",
            [self.volunteer_account_1.email_address],
            fail_silently=False,
        )

    # Test that opportunity 2 triggers a match for volunteer 2 with partial matching.
    @patch("opportunities_engagements.signals.send_mail") 
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_opportunity_2_triggers_matching_for_volunteer_2(self, mock_notification, mock_mail):
        url = reverse("opportunities_engagements:create_opportunity")
        data = {
            "title": "Health Awareness",
            "description": "Help spread health awareness in the community!",
            "work_basis": "online",  # Matches Volunteer 2
            "duration": "long-term",  # Matches Volunteer 2
            "area_of_work": "education",  # Volunteer 2 prefers health
            "requirements": ["communication", "public speaking"],  # Matches (communication)
            "required_location": {"lat": 37.0, "lon": 15.0, "formatted_address": "Far City", "city": "Far City"},
            "languages": ["Spanish", "French"],  # Matches one language
            "days_of_week": ["friday"],  # Matches availability
            "status": "upcoming",
            "ongoing": True
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        opportunity_id = response.data.get("data", {}).get("volunteer_opportunity_id")
        self.assertIsNotNone(opportunity_id, "Opportunity ID should not be None!")

        # Expected match percentages
        expected_match_v1 = 50  # Volunteer 1 (below 65%, so not notified)
        expected_match_v2 = 75  # Volunteer 2 (above 65%, so notified)
        expected_match_v3 = 55  # Volunteer 3 (below 65%, so not notified)

        # Only Volunteer 2 should be notified
        mock_notification.assert_called_once_with(
            recipient_id=str(self.volunteer_account_2.account_uuid),
            notification_type="opportunity_match",
            message=f"You are a {expected_match_v2}% match for 'Health Awareness' (114.18 km away) by Helping Hands. Check it out!"
        )

        mock_mail.assert_called_with(
            f"You're a great match ({expected_match_v2}%) for a new opportunity!",
            (
                f"Hi {self.volunteer_2.first_name} {self.volunteer_2.last_name},\n\n"
                "We found a new volunteering opportunity that matches your interests!\n\n"
                f"[View Opportunity & Apply](https://volontera.com/opportunity/{response.data['data']['volunteer_opportunity_id']})\n\n"
                "Happy Volunteering!"
            ),
            "volonteracm3070@gmail.com",
            [self.volunteer_account_2.email_address],
            fail_silently=False,
        )

    # Test that opportunity 3 triggers a match for volunteer 3 with partial matching.
    @patch("opportunities_engagements.signals.send_mail") 
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_opportunity_3_triggers_matching_for_volunteer_3(self, mock_notification, mock_mail):
        url = reverse("opportunities_engagements:create_opportunity")
        data = {
            "title": "Photography Workshop",
            "description": "A hands-on workshop for aspiring photographers.",
            "work_basis": "both",  # Matches Volunteer 3
            "duration": "medium-term",  # Matches Volunteer 3
            "area_of_work": "arts",  # Matches Volunteer 3
            "requirements": ["photography", "creativity"],  # Matches (photography)
            "required_location": {"lat": 37.5, "lon": 15.5, "formatted_address": "Distant City", "city": "Distant City"},
            "languages": ["English"],  # Volunteer 3 prefers Spanish
            "days_of_week": ["sunday"],  # Matches availability
            "status": "upcoming",
            "ongoing": True
        }
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        opportunity_id = response.data.get("data", {}).get("volunteer_opportunity_id")
        self.assertIsNotNone(opportunity_id, "Opportunity ID should not be None!")

        # Expected match percentages
        expected_match_v1 = 55  # Volunteer 1 (below 65%, so not notified)
        expected_match_v2 = 60  # Volunteer 2 (below 65%, so not notified)
        expected_match_v3 = 95  # Volunteer 3 (above 65%, so notified)

        # Only Volunteer 3 should be notified
        mock_notification.assert_called_once_with(
            recipient_id=str(self.volunteer_account_3.account_uuid),
            notification_type="opportunity_match",
            message=f"You are a {expected_match_v3}% match for 'Photography Workshop' (83.28 km away) by Helping Hands. Check it out!"
        )

        mock_mail.assert_called_with(
            f"You're a great match ({expected_match_v3}%) for a new opportunity!",
            (
                f"Hi {self.volunteer_3.first_name} {self.volunteer_3.last_name},\n\n"
                "We found a new volunteering opportunity that matches your interests!\n\n"
                f"[View Opportunity & Apply](https://volontera.com/opportunity/{response.data['data']['volunteer_opportunity_id']})\n\n"
                "Happy Volunteering!"
            ),
            "volonteracm3070@gmail.com",
            [self.volunteer_account_3.email_address],
            fail_silently=False,
        )

class EngagementLogVolonteraPointSignalTest(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        self.client = APIClient()
        self.client.force_authenticate(user=self.organization_account)

    # Test engagement log creation for opportunity engagement sends notification.
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_create_opportunity_engagement_log_triggers_notification(self, mock_notification_task):
        url = reverse("opportunities_engagements:create_opportunity_engagement_logs", args=[self.opportunity.volunteer_opportunity_id])
        self.client.force_authenticate(user=self.organization_account)
        
        response = self.client.post(url)
        # Check if API returned success
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify notification was triggered
        mock_notification_task.assert_called_once_with(
            recipient_id=str(self.volunteer_account.account_uuid),
            notification_type="new_volontera_points",
            message=f"You have earned 3.0 Volontera points for your volunteer engagement!"
        )

        # Check if Volontera points increased
        self.volunteer.refresh_from_db()
        self.assertEqual(self.volunteer.volontera_points, 3.0)

    # Test engagement log creation for session engagement sends notification.
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_create_session_engagement_log_triggers_notification(self, mock_notification_task):
        url = reverse("opportunities_engagements:create_session_engagement_logs", args=[self.session.session_id])

        response = self.client.post(url)

        # Check if API returned success
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify notification was triggered
        mock_notification_task.assert_called_once_with(
            recipient_id=str(self.volunteer_account.account_uuid),
            notification_type="new_volontera_points",
            message=f"You have earned 2.0 Volontera points for your volunteer engagement!"
        )

        # Check if Volontera points increased
        self.volunteer.refresh_from_db()
        self.assertEqual(self.volunteer.volontera_points, 2.0)

    # Test approving an engagement log sends notification.
    @patch("accounts_notifs.tasks.send_notification.delay")
    def test_approve_engagement_log_triggers_notification(self, mock_notification_task):
        # Step 1: Create the engagement log (pending)
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement_ongoing,
            no_of_hours=2,
            status="pending",
            log_notes="Tutored students in English",
            is_volunteer_request=True
        )

        # Assert log request submission triggered a notification
        mock_notification_task.assert_called_once_with(
            recipient_id=str(self.organization_account.account_uuid),  # Assuming org gets notified
            notification_type="log_request_submitted",
            message=f"{self.volunteer.first_name} {self.volunteer.last_name} has submitted a new engagement log request for {self.ongoing_opportunity.title}."
        )

        # Reset mock to avoid interference with approval step
        mock_notification_task.reset_mock()

        # Step 2: Approve the engagement log
        url = reverse("opportunities_engagements:approve_engagement_log", args=[log.volunteer_engagement_log_id])
        response = self.client.patch(url)  

        # Check API success
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify that new_volontera_points notification was sent
        mock_notification_task.assert_called_once_with(
            recipient_id=str(self.volunteer_account.account_uuid),
            notification_type="new_volontera_points",
            message=f"You have earned 2.0 Volontera points for your volunteer engagement!"
        )

        # Check if Volontera points increased
        self.volunteer.refresh_from_db()
        self.assertEqual(self.volunteer.volontera_points, 2)