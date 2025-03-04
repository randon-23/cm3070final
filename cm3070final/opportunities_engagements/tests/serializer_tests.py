from django.test import TestCase
from rest_framework.exceptions import ValidationError
from ..serializers import VolunteerOpportunitySerializer, VolunteerOpportunityApplicationSerializer, VolunteerEngagementSerializer, VolunteerOpportunitySessionSerializer, VolunteerSessionEngagementSerializer, VolunteerEngagementLogSerializer
from ..models import VolunteerOpportunity, VolunteerOpportunityApplication, VolunteerOpportunitySession, VolunteerEngagement, VolunteerEngagementLog, VolunteerSessionEngagement
from volunteers_organizations.models import Organization, Volunteer
from accounts_notifs.models import Account
from datetime import date, time, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth import get_user_model
from unittest.mock import Mock
from django.utils.timezone import now

Account = get_user_model()

class TestVolunteerOpportunitySerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization_account = Account.objects.create_user(
            email_address='org@example.com',
            password='password123',
            user_type='organization',
            contact_number='+35612345678'
        )

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Planet",
            organization_description="A non-profit focused on environmental conservation",
            organization_address={
                'raw': '123 Green Street, Valletta, Malta',
                'street_number': '123',
                'route': 'Green Street',
                'locality': 'Valletta',
                'postal_code': 'VLT1234',
                'state': 'Valletta',
                'state_code': 'VLT',
                'country': 'Malta',
                'country_code': 'MT'
            }
        )

    def setUp(self):
        self.mock_request = Mock()
        self.mock_request.user = self.organization

    # Test successful creation of a one-time volunteer opportunity
    def test_create_one_time_opportunity(self):
        data = {
            "organization": self.organization.pk,
            "title": "Beach Cleanup",
            "description": "Help clean up the beach!",
            "work_basis": "in-person",
            "duration": "short-term",
            "opportunity_date": date.today() + relativedelta(days=7),
            "opportunity_time_from": time(9, 0),
            "opportunity_time_to": time(12, 0),
            "area_of_work": "environment",
            "requirements": ["physical fitness"],
            "ongoing": False,
            "application_deadline": date.today() + relativedelta(days=3),
            "slots": 20
        }

        serializer = VolunteerOpportunitySerializer(data=data, context={'request': self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        opportunity = serializer.save()
        self.assertEqual(opportunity.title, "Beach Cleanup")
        self.assertEqual(opportunity.ongoing, False)
        self.assertEqual(opportunity.slots, 20)

    # Test successful creation of an ongoing volunteer opportunity
    def test_create_ongoing_opportunity(self):
        data = {
            "organization": self.organization.pk,
            "title": "Weekly Tree Planting",
            "description": "Plant trees every week.",
            "work_basis": "both",
            "duration": "long-term",
            "days_of_week": ["saturday"],
            "area_of_work": "environment",
            "requirements": ["physical fitness"],
            "ongoing": True
        }

        serializer = VolunteerOpportunitySerializer(data=data, context={'request': self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        opportunity = serializer.save()
        self.assertTrue(opportunity.ongoing)
        self.assertEqual(opportunity.days_of_week, ["saturday"])
        self.assertIsNone(opportunity.application_deadline)

    # Test that a one-time opportunity must have slots defined
    def test_slots_required_for_one_time(self):
        data = {
            "organization": self.organization.pk,
            "title": "One-time Event",
            "description": "An event that requires slots.",
            "work_basis": "in-person",
            "duration": "short-term",
            "opportunity_date": date.today() + relativedelta(days=10),
            "opportunity_time_from": time(9, 0),
            "opportunity_time_to": time(12, 0),
            "area_of_work": "sports",
            "requirements": ["physical fitness"],
            "ongoing": False,
            "application_deadline": date.today() + relativedelta(days=5),
            "slots": None  # Missing slots
        }

        serializer = VolunteerOpportunitySerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Slots must be set for one-time opportunities.", serializer.errors["non_field_errors"])

    # Test that an ongoing opportunity cannot have slots defined
    def test_slots_not_allowed_for_ongoing(self):
        data = {
            "organization": self.organization.pk,
            "title": "Weekly Event",
            "description": "An ongoing event that should not have slots.",
            "work_basis": "both",
            "duration": "long-term",
            "days_of_week": ["saturday"],
            "area_of_work": "technology",
            "requirements": ["coding"],
            "ongoing": True,
            "slots": 5  # Should not be allowed
        }

        serializer = VolunteerOpportunitySerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Ongoing opportunities cannot have slots.", serializer.errors["non_field_errors"])

    # Test that contribution_hours is correctly calculated from logs
    def test_contribution_hours_calculation(self):
        opportunity = VolunteerOpportunity.objects.create(
            organization=self.organization,
            title="Programming Workshop",
            description="Teach kids programming.",
            work_basis="online",
            duration="short-term",
            opportunity_date=date.today() + relativedelta(days=5),
            opportunity_time_from=time(10, 0),
            opportunity_time_to=time(12, 0),  # 2-hour opportunity
            area_of_work="education",
            requirements=["coding"],
            ongoing=False,
            application_deadline=date.today() + relativedelta(days=3),
            slots=10
        )

        # Create volunteer and engagement log to track hours
        volunteer_account = Account.objects.create_user(
            email_address="volunteer@example.com",
            password="password123",
            user_type="volunteer",
            contact_number="+35698765432"
        )
        volunteer = Volunteer.objects.create(account=volunteer_account, first_name="John", last_name="Doe", dob=date(1995, 1, 1))
        application = VolunteerOpportunityApplication.objects.create(volunteer_opportunity=opportunity, volunteer=volunteer, application_status="accepted")
        engagement = VolunteerEngagement.objects.create(volunteer_opportunity_application=application)

        # Add logs
        VolunteerEngagementLog.objects.create(volunteer_engagement=engagement, no_of_hours=2.0, status="approved")
        VolunteerEngagementLog.objects.create(volunteer_engagement=engagement, no_of_hours=1.5, status="approved")

        serializer = VolunteerOpportunitySerializer(opportunity, context={'request': self.mock_request})
        self.assertEqual(serializer.data["contribution_hours"], 3.5)  # 2.0 + 1.5 = 3.5

    # Test that an invalid area_of_work is rejected
    def test_invalid_area_of_work(self):
        data = {
            "organization": self.organization.pk,
            "title": "Invalid Area",
            "description": "An invalid area of work.",
            "work_basis": "in-person",
            "duration": "short-term",
            "opportunity_date": date.today() + relativedelta(days=10),
            "opportunity_time_from": time(9, 0),
            "opportunity_time_to": time(12, 0),
            "area_of_work": "invalid_category",  # Not a valid area
            "requirements": ["physical fitness"],
            "ongoing": False,
            "application_deadline": date.today() + relativedelta(days=5),
            "slots": 20
        }

        serializer = VolunteerOpportunitySerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("area_of_work", serializer.errors)

class TestVolunteerOpportunityApplicationSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account = Account.objects.create_user(
            email_address='volunteer@example.com',
            password='password123',
            user_type='volunteer',
            contact_number='+35612345678'
        )
        cls.organization_account = Account.objects.create_user(
            email_address='org@example.com',
            password='password123',
            user_type='organization',
            contact_number='+35612345679'
        )

        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Planet",
            organization_description="A non-profit focused on environmental conservation",
            organization_address={
                'raw': '123 Green Street, Valletta, Malta',
                'street_number': '123',
                'route': 'Green Street',
                'locality': 'Valletta',
                'postal_code': 'VLT1234',
                'state': 'Valletta',
                'state_code': 'VLT',
                'country': 'Malta',
                'country_code': 'MT'
            }
        )

        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Beach Cleanup",
            description="Help clean up the beach!",
            work_basis="in-person",
            duration="short-term",
            opportunity_date=date.today() + relativedelta(days=7),
            opportunity_time_from=time(9, 0),
            opportunity_time_to=time(12, 0),
            area_of_work="environment",
            requirements=["physical fitness"],
            ongoing=False,
            application_deadline=date.today() + relativedelta(days=3),
            slots=10  # Limited slots
        )

    def setUp(self):
        self.mock_request = Mock()
        self.mock_request.user = self.volunteer

    # Test successful creation of an application.
    def test_create_valid_application(self):
        data = {
            "volunteer_opportunity": self.opportunity.pk,
            "volunteer": self.volunteer.pk,
            "as_group": False,
            "no_of_additional_volunteers": 0
        }
        serializer = VolunteerOpportunityApplicationSerializer(data=data, context={'request': self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        application = serializer.save()
        self.assertEqual(application.application_status, "pending")
        self.assertEqual(application.no_of_additional_volunteers, 0)
        self.assertFalse(application.as_group)

    # Ensure a volunteer cannot apply twice for the same opportunity.
    def test_prevent_duplicate_application(self):
        VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="pending"
        )

        data = {
            "volunteer_opportunity": self.opportunity.pk,
            "volunteer": self.volunteer.pk,
            "as_group": False,
            "no_of_additional_volunteers": 0
        }

        serializer = VolunteerOpportunityApplicationSerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("The fields volunteer_opportunity, volunteer must make a unique set.", serializer.errors["non_field_errors"][0])

    # Test that group applications must have at least one additional volunteer.
    def test_group_application_validations(self):
        data = {
            "volunteer_opportunity": self.opportunity.pk,
            "volunteer": self.volunteer.pk,
            "as_group": True,
            "no_of_additional_volunteers": 0  # Invalid case
        }
        serializer = VolunteerOpportunityApplicationSerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Group applications must have at least one additional volunteer.", serializer.errors["non_field_errors"][0])

    # Test that applying alone must not have additional volunteers.
    def test_solo_application_cannot_have_additional_volunteers(self):
        data = {
            "volunteer_opportunity": self.opportunity.pk,
            "volunteer": self.volunteer.pk,
            "as_group": False,
            "no_of_additional_volunteers": 2  # Invalid case
        }
        serializer = VolunteerOpportunityApplicationSerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Number of additional volunteers must be zero if applying alone.", serializer.errors["non_field_errors"][0])

    # Ensure slots are only deducted when application moves to 'accepted'.
    def test_slots_deducted_only_when_application_is_accepted(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="pending",
            as_group=True,
            no_of_additional_volunteers=3
        )
        initial_slots = self.opportunity.slots  # Expecting 10 initially

        # Try updating status to accepted
        serializer = VolunteerOpportunityApplicationSerializer(
            instance=application, data={"application_status": "accepted"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.opportunity.refresh_from_db()
        self.assertEqual(self.opportunity.slots, initial_slots - 4)  # 1 volunteer + 3 additional

    # Ensure that slots are not deducted for ongoing opportunities.
    def test_slots_not_deducted_for_ongoing_opportunities(self):
        ongoing_opportunity = VolunteerOpportunity.objects.create(
            organization=self.organization,
            title="Long-Term Teaching",
            description="Teach coding over multiple sessions.",
            work_basis="in-person",
            duration="long-term",
            days_of_week=["monday", "wednesday"],
            area_of_work="education",
            requirements=["teaching"],
            ongoing=True,  # Ongoing opportunity
            application_deadline=None,
            slots=None  # Unlimited slots
        )

        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=ongoing_opportunity,
            volunteer=self.volunteer,
            application_status="pending"
        )

        # Change status to accepted
        serializer = VolunteerOpportunityApplicationSerializer(
            instance=application, data={"application_status": "accepted"}, partial=True
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        ongoing_opportunity.refresh_from_db()
        self.assertIsNone(ongoing_opportunity.slots)  # Should still be None

    # Ensure an accepted application cannot be modified.
    def test_cannot_modify_accepted_application(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            application_status="accepted"
        )

        serializer = VolunteerOpportunityApplicationSerializer(
            instance=application, data={"application_status": "pending"}, partial=True
        )
        self.assertTrue(serializer.is_valid())  # This checks if it passes validation

        # Now trigger the update method by calling `save()`
        with self.assertRaises(ValidationError) as context:
            serializer.save()

        self.assertIn("Cannot modify an already accepted application.", str(context.exception))

class TestVolunteerEngagementSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account = Account.objects.create_user(
            email_address='volunteer@example.com',
            password='password123',
            user_type='volunteer',
            contact_number='+35612345678'
        )
        cls.organization_account = Account.objects.create_user(
            email_address='org@example.com',
            password='password123',
            user_type='organization',
            contact_number='+35612345679'
        )
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )
        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Planet",
            organization_description="A non-profit focused on environmental conservation",
            organization_address={
                'raw': '123 Green Street, Valletta, Malta',
                'street_number': '123',
                'route': 'Green Street',
                'locality': 'Valletta',
                'postal_code': 'VLT1234',
                'state': 'Valletta',
                'state_code': 'VLT',
                'country': 'Malta',
                'country_code': 'MT'
            }
        )
        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.organization.volunteeropportunity_set.create(
                title="Tree Planting",
                description="Plant trees to save the environment.",
                work_basis="in-person",
                duration="short-term",
                area_of_work="environment",
                opportunity_date=date.today(),
                application_deadline=date.today(),
                slots=5
            ),
            volunteer=cls.volunteer,
            application_status="accepted"
        )

    def setUp(self):
        self.mock_request = Mock()
        self.mock_request.user = self.volunteer

    def test_create_engagement_successfully(self):
        data = {
            "volunteer_opportunity_application": self.application.pk,
            "engagement_status": "ongoing"
        }

        serializer = VolunteerEngagementSerializer(data=data, context={"request": self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        engagement = serializer.save()

        self.assertEqual(engagement.volunteer, self.volunteer)
        self.assertEqual(engagement.organization, self.organization)
        self.assertEqual(engagement.engagement_status, "ongoing")
        self.assertIsNotNone(engagement.start_date)

    def test_cannot_create_engagement_if_application_not_accepted(self):
        self.application.application_status = "pending"
        self.application.save()

        data = {
            "volunteer_opportunity_application": self.application.pk,
            "engagement_status": "ongoing"
        }

        serializer = VolunteerEngagementSerializer(data=data, context={"request": self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Volunteer engagement must be created from an accepted application.", serializer.errors["non_field_errors"])

    def test_cannot_set_end_date_before_start_date(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )

        data = {"end_date": engagement.start_date - relativedelta(days=1), "engagement_status": "completed"}
        serializer = VolunteerEngagementSerializer(engagement, data=data, partial=True)

        self.assertFalse(serializer.is_valid())
        self.assertIn("End date cannot be before the start date.", serializer.errors["non_field_errors"])

    def test_marking_completed_sets_end_date(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )

        data = {"engagement_status": "completed"}
        serializer = VolunteerEngagementSerializer(engagement, data=data, partial=True)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        engagement.refresh_from_db()
        self.assertEqual(engagement.engagement_status, "completed")
        self.assertIsNotNone(engagement.end_date)

class TestVolunteerOpportunitySessionSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization_account = Account.objects.create_user(
            email_address='org@example.com',
            password='password123',
            user_type='organization',
            contact_number='+35612345679'
        )
        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Planet",
            organization_description="A non-profit focused on environmental conservation",
            organization_address={
                'raw': '123 Green Street, Valletta, Malta',
                'street_number': '123',
                'route': 'Green Street',
                'locality': 'Valletta',
                'postal_code': 'VLT1234',
                'state': 'Valletta',
                'state_code': 'VLT',
                'country': 'Malta',
                'country_code': 'MT'
            }
        )
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Beach Cleanup",
            description="Help clean the beach!",
            work_basis="in-person",
            duration="short-term",
            area_of_work="environment",
            ongoing=True
        )

    def setUp(self):
        self.mock_request = Mock()
        self.mock_request.user = self.organization

    # Ensure a valid session can be created.
    def test_create_valid_session(self):
        data = {
            "opportunity": self.opportunity.pk,
            "title": "Python Workshop",
            "description": "Learn Python basics.",
            "session_date": date.today() + relativedelta(days=10),
            "session_start_time": time(10, 0),
            "session_end_time": time(12, 0),
            "slots": 15
        }

        serializer = VolunteerOpportunitySessionSerializer(data=data, context={'request': self.mock_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        session = serializer.save()
        self.assertEqual(session.title, "Python Workshop")
        self.assertEqual(session.status, "upcoming")
        self.assertEqual(session.slots, 15)

    # Ensure that sessions cannot be created for one-time opportunities.
    def test_cannot_create_session_for_non_ongoing_opportunity(self):
        self.opportunity.ongoing = False  # Make sure it's a one-time opportunity
        self.opportunity.opportunity_date = date.today() + relativedelta(days=5)
        self.opportunity.application_deadline = date.today() + relativedelta(days=3)
        self.opportunity.opportunity_time_from = time(9, 0)
        self.opportunity.opportunity_time_to = time(12, 0)
        self.opportunity.save()

        data = {
            "opportunity": self.opportunity.pk,
            "title": "Invalid Session",
            "description": "This should not be allowed.",
            "session_date": date.today() + relativedelta(days=10),
            "session_start_time": time(10, 0),
            "session_end_time": time(12, 0),
            "slots": 10
        }

        serializer = VolunteerOpportunitySessionSerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Sessions can only be created for ongoing opportunities.", serializer.errors["non_field_errors"])

    # Ensure session start time cannot be after or equal to end time.
    def test_session_start_must_be_before_end(self):
        data = {
            "opportunity": self.opportunity.pk,
            "title": "Time Conflict Session",
            "session_date": date.today() + relativedelta(days=5),
            "session_start_time": time(14, 0),
            "session_end_time": time(13, 0),
        }

        serializer = VolunteerOpportunitySessionSerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Session start time must be before end time.", serializer.errors["non_field_errors"])

    # Ensure slots cannot be negative or zero.
    def test_slots_must_be_positive(self):
        data = {
            "opportunity": self.opportunity.pk,
            "title": "Slots Test",
            "session_date": date.today() + relativedelta(days=3),
            "session_start_time": time(9, 0),
            "session_end_time": time(11, 0),
            "slots": 0
        }

        serializer = VolunteerOpportunitySessionSerializer(data=data, context={'request': self.mock_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Slots must be a positive integer if set.", serializer.errors["non_field_errors"])

    # Ensure that a session marked as completed or cancelled cannot be modified.
    def test_prevent_modification_if_completed_or_cancelled(self):
        session = VolunteerOpportunitySession.objects.create(
            opportunity=self.opportunity,
            title="Immutable Session",
            session_date=date.today() + relativedelta(days=7),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            status="completed"
        )

        data = {"title": "Updated Title"}
        serializer = VolunteerOpportunitySessionSerializer(session, data=data, context={"request": self.mock_request}, partial=True)

        self.assertFalse(serializer.is_valid())
        self.assertIn("Cannot modify a session that is completed or cancelled.", serializer.errors["non_field_errors"])

class TestVolunteerSessionEngagementSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account = Account.objects.create_user(
            email_address="volunteer@example.com",
            password="password123",
            user_type="volunteer",
            contact_number="+35698765432"
        )
        cls.organization_account = Account.objects.create_user(
            email_address='org@example.com',
            password='password123',
            user_type='organization',
            contact_number='+35612345678'
        )
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account, first_name="John", last_name="Doe", dob=date(1995, 1, 1)
        )
        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="Non-profit organization.",
            organization_address={"raw": "123 Help St, Kindness City, US"},
        )
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Teach Kids Coding",
            description="Help kids learn basic programming.",
            work_basis="online",
            duration="short-term",
            area_of_work="education",
            ongoing=True,
        )
        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.opportunity,
            title="Intro to Python",
            description="Session for teaching Python basics.",
            session_date=now().date() + timedelta(days=5),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            slots=2,
        )
        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )
        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application
        )

    # Ensure that a valid session engagement can be created
    def test_create_valid_session_engagement(self):
        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": self.session.pk,
            "status": "can_go"
        }
        serializer = VolunteerSessionEngagementSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        session_engagement = serializer.save()
        self.assertEqual(session_engagement.status, "can_go")

    # Ensure that a session engagement cannot be created if the session is for a different opportunity.
    def test_cannot_create_session_engagement_for_wrong_opportunity(self):
        wrong_opportunity = VolunteerOpportunity.objects.create(
            organization=self.organization,
            title="Wrong Opportunity",
            description="A different one.",
            work_basis="in-person",
            duration="short-term",
            area_of_work="health",
            ongoing=True,
        )
        wrong_session = VolunteerOpportunitySession.objects.create(
            opportunity=wrong_opportunity,
            title="Different Session",
            session_date=now().date() + timedelta(days=7),
            session_start_time=time(14, 0),
            session_end_time=time(16, 0),
        )

        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": wrong_session.pk,
            "status": "can_go"
        }
        serializer = VolunteerSessionEngagementSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("Session does not belong to the same opportunity as the engagement.", serializer.errors["non_field_errors"])

    # Ensure that a session engagement cannot be created if the session is fully booked.
    def test_cannot_attend_full_session(self):
        # Fill up the session
        VolunteerSessionEngagement.objects.create(volunteer_engagement=self.engagement, session=self.session, status="can_go")
        another_volunteer = Volunteer.objects.create(
            account=Account.objects.create_user(email_address="test2@example.com", password="password123", user_type="volunteer"),
            first_name="Jane",
            last_name="Doe",
            dob=date(1998, 2, 2),
        )
        another_application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=another_volunteer,
            application_status="accepted"
        )
        another_engagement = VolunteerEngagement.objects.create(volunteer_opportunity_application=another_application)

        VolunteerSessionEngagement.objects.create(volunteer_engagement=another_engagement, session=self.session, status="can_go")

        # Try adding a third engagement when session is already full
        third_volunteer = Volunteer.objects.create(
            account=Account.objects.create_user(email_address="test3@example.com", password="password123", user_type="volunteer", contact_number="+123667477"),
            first_name="Mike",
            last_name="Smith",
            dob=date(2000, 5, 5),
        )
        third_application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=third_volunteer,
            application_status="accepted"
        )
        third_engagement = VolunteerEngagement.objects.create(volunteer_opportunity_application=third_application)

        # This third person should not be able to join the full session
        data = {
            "volunteer_engagement": third_engagement.pk,
            "session": self.session.pk,
            "status": "can_go"
        }
        serializer = VolunteerSessionEngagementSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("This session is fully booked.", serializer.errors["non_field_errors"])

    # Ensure that a volunteer cannot cancel on the day of the session.
    def test_cannot_cancel_last_minute(self):
        past_session = VolunteerOpportunitySession.objects.create(
            opportunity=self.opportunity,
            title="Past Session",
            session_date=now().date(),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            slots=10,
        )
        engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement, session=past_session, status="can_go"
        )

        data = {"status": "cant_go"}
        serializer = VolunteerSessionEngagementSerializer(engagement, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(ValidationError) as context:
            serializer.save()
        self.assertIn("You cannot cancel your attendance on the day of the session.", str(context.exception))

class TestVolunteerEngagementLogSerializer(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up test data for engagement logs
        cls.organization_account = Account.objects.create_user(
            email_address="org@example.com",
            password="password123",
            user_type="organization",
            contact_number="+356123667551"
        )
        cls.volunteer_account = Account.objects.create_user(
            email_address="volunteer@example.com",
            password="password123",
            user_type="volunteer",
            contact_number="+356123667552"
        )

        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Helping Hands",
            organization_description="Non-profit organization.",
            organization_address={"raw": "123 Help St, City"}
        )
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )

        # One-time opportunity (specific date)
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Beach Cleanup",
            description="Help clean the beach.",
            work_basis="in-person",
            duration="short-term",
            opportunity_date=now().date(),
            opportunity_time_from=time(9, 0),
            opportunity_time_to=time(12, 0),
            area_of_work="environment",
            ongoing=False
        )

        # Ongoing opportunity (no specific date, has sessions)
        cls.ongoing_opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Community Teaching",
            description="Teach children basic math skills.",
            work_basis="both",
            duration="long-term",
            area_of_work="education",
            ongoing=True
        )

        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )
        cls.ongoing_application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.ongoing_opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application
        )
        cls.ongoing_engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.ongoing_application
        )

        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.ongoing_opportunity,
            title="Weekly Tutoring",
            session_date=now().date() - relativedelta(days=1),  # Past session
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            slots=10
        )

        cls.session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=cls.ongoing_engagement,
            session=cls.session,
            status="can_go"
        )

    # Set up mock requests for volunteers & organizations.
    def setUp(self):
        self.org_request = Mock()
        self.org_request.user = self.organization_account

        self.volunteer_request = Mock()
        self.volunteer_request.user = self.volunteer_account

    # Ensure valid logs can be created for a session
    def test_create_log_for_session(self):
        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": self.session_engagement.pk,
            "no_of_hours": 1.5,
            "log_notes": "Helped teach Python."
        }
        serializer = VolunteerEngagementLogSerializer(data=data, context={"request": self.volunteer_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()
        self.assertEqual(log.no_of_hours, 1.5)

    # Ensure valid logs can be created for a one-time opportunity
    def test_create_log_for_opportunity(self):
        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": None,
            "no_of_hours": 2.5,
            "log_notes": "Worked on cleanup."
        }
        serializer = VolunteerEngagementLogSerializer(data=data, context={"request": self.volunteer_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()
        self.assertEqual(log.no_of_hours, 2.5)

    # Ensure valid logs can be created for an **ongoing** opportunity without a session
    def test_create_log_for_ongoing_opportunity_without_session(self):
        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": None,  # No session, but allowed for ongoing opps
            "no_of_hours": 2.0,
            "log_notes": "Extra tutoring session."
        }
        serializer = VolunteerEngagementLogSerializer(data=data, context={"request": self.volunteer_request})
        self.assertTrue(serializer.is_valid(), serializer.errors)
        log = serializer.save()
        self.assertEqual(log.no_of_hours, 2.0)

    # Prevent logs for future sessions/opportunities
    def test_no_future_logs(self):
        future_session = VolunteerOpportunitySession.objects.create(
            opportunity=self.ongoing_opportunity,
            title="Future Session",
            session_date=now().date() + relativedelta(days=5),
            session_start_time=time(9, 0),
            session_end_time=time(11, 0),
            slots=10
        )
        future_session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.ongoing_engagement,
            session=future_session,
            status="can_go"
        )
        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": future_session_engagement.pk,
            "no_of_hours": 2
        }
        serializer = VolunteerEngagementLogSerializer(data=data, context={"request": self.volunteer_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("You cannot create logs for a session that has not yet happened.", serializer.errors["non_field_errors"])

    # Prevent duplicate logs
    def test_duplicate_logs_not_allowed(self):
        VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session_engagement,
            no_of_hours=1.5
        )
        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": self.session_engagement.pk,
            "no_of_hours": 1.0
        }
        serializer = VolunteerEngagementLogSerializer(data=data, context={"request": self.volunteer_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("The fields volunteer_engagement, session must make a unique set.", serializer.errors["non_field_errors"])

    # Organizations can approve logs
    def test_organization_can_approve_log(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session_engagement,
            no_of_hours=2.0,
            log_notes="Taught kids math.",
            status="pending"
        )
        serializer = VolunteerEngagementLogSerializer(
            instance=log,
            data={"status": "approved"},
            partial=True,
            context={"request": self.org_request}
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        updated_log = serializer.save()
        self.assertEqual(updated_log.status, "approved")

    # Volunteers cannot approve logs
    def test_volunteer_cannot_approve_log(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session_engagement,
            no_of_hours=2.0,
            log_notes="Taught kids math.",
            status="pending"
        )
        serializer = VolunteerEngagementLogSerializer(
            instance=log,
            data={"status": "approved"},
            partial=True,
            context={"request": self.volunteer_request}
        )
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(ValidationError) as context:
            serializer.save()
        self.assertIn("Only organizations can approve or reject logs.", str(context.exception))

    # Approved logs cannot be modified
    def test_approved_logs_cannot_be_modified(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session_engagement,
            no_of_hours=2.0,
            log_notes="Taught kids math.",
            status="pending"
        )

        log.status = "approved"
        log.save()

        serializer = VolunteerEngagementLogSerializer(
            instance=log,
            data={"status": "pending"},
            partial=True,
            context={"request": self.org_request}
        )
        self.assertTrue(serializer.is_valid())
        with self.assertRaises(ValidationError) as context:
            serializer.save()
        self.assertIn("Approved logs cannot be modified.", str(context.exception))

    # Ensure `no_of_hours` cannot be zero or negative
    def test_no_of_hours_cannot_be_zero_or_negative(self):
        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": self.session_engagement.pk,
            "no_of_hours": 0,
            "log_notes": "Invalid log."
        }
        serializer = VolunteerEngagementLogSerializer(data=data, context={"request": self.volunteer_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Logged hours must be greater than zero.", serializer.errors["non_field_errors"])

    # Ensure logs cannot exceed max duration of session/opportunity
    def test_no_of_hours_exceeds_session_duration(self):
        data = {
            "volunteer_engagement": self.engagement.pk,
            "session": self.session_engagement.pk,
            "no_of_hours": 5,  # Exceeds the 2-hour session
            "log_notes": "Too many hours."
        }
        serializer = VolunteerEngagementLogSerializer(data=data, context={"request": self.volunteer_request})
        self.assertFalse(serializer.is_valid())
        self.assertIn("Logged hours exceed session duration.", serializer.errors["non_field_errors"])