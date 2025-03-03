from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from ..models import VolunteerOpportunity, VolunteerOpportunityApplication, VolunteerEngagement, VolunteerEngagementLog, VolunteerOpportunitySession, VolunteerSessionEngagement
from volunteers_organizations.models import Volunteer, Organization
from accounts_notifs.models import Account
from datetime import date
from dateutil.relativedelta import relativedelta
from datetime import time

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

class TestVolunteerOpportunityModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        _, cls.organization_account = create_common_objects()
        cls.organization=Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Earth",
            organization_description="An organization dedicated to environmental conservation",
            organization_address={
                'raw': '123 Greenway Blvd, Springfield, US',
                'street_number': '123',
                'route': 'Greenway Blvd',
                'locality': 'Springfield',
                'postal_code': '12345',
                'state': 'Illinois',
                'state_code': 'IL',
                'country': 'United States',
                'country_code': 'US'
            }
        )

    def test_valid_one_day_opportunity_creation(self):
        # Testing a valid one-day volunteer opportunity is created i.e. that opportunity_date is set and ongoing is False
        opportunity = VolunteerOpportunity.objects.create(
            organization=self.organization,
            title="Tree Planting Drive",
            description="Plant trees in the city park.",
            work_basis="in-person",
            duration="short-term",
            opportunity_date=date.today() + relativedelta(days=10),
            area_of_work="environment",
            requirements=["Able to work outdoors"],
            application_deadline=date.today() + relativedelta(days=5),
            ongoing=False,
            required_location={
                "lat": 35.8995,
                "lon": 14.5146,
                "city": "Valletta",
                "formatted_address": "Valletta, Malta"
            }
        )
        self.assertEqual(opportunity.organization, self.organization)
        self.assertEqual(opportunity.opportunity_date, date.today() + relativedelta(days=10))
        self.assertFalse(opportunity.ongoing)

    def test_valid_ongoing_opportunity_creation(self):
        # Testing a valid ongoing volunteer opportunity is created i.e. that ongoing is True and application_deadline is None
        opportunity = VolunteerOpportunity.objects.create(
            organization=self.organization,
            title="Environmental Awareness Campaign",
            description="Spread awareness about climate change.",
            work_basis="both",
            duration="long-term",
            days_of_week=["monday", "wednesday"],
            area_of_work="education",
            requirements=["Good communication skills"],
            application_deadline=None,
            ongoing=True,
            required_location={
                "lat": 35.8995,
                "lon": 14.5146,
                "city": "Valletta",
                "formatted_address": "Valletta, Malta"
            }
        )
        self.assertTrue(opportunity.ongoing)
        self.assertIsNone(opportunity.opportunity_date)
        self.assertEqual(opportunity.days_of_week, ["monday", "wednesday"])
        self.assertIsNone(opportunity.slots)

    def test_ongoing_opportunity_with_application_deadline(self):
        # Testing that an opportunity set to ongoing cannot have an application deadline
        with self.assertRaises(IntegrityError):
            opportunity = VolunteerOpportunity.objects.create(
                organization=self.organization,
                title="Ongoing Opportunity with Deadline",
                description="An invalid ongoing opportunity with a deadline.",
                work_basis="online",
                duration="medium-term",
                days_of_week=["friday"],
                area_of_work="community",
                requirements=["Basic computer skills"],
                application_deadline=date.today() + relativedelta(days=5),
                ongoing=True,
                required_location={
                    "lat": 35.8995,
                    "lon": 14.5146,
                    "city": "Valletta",
                    "formatted_address": "Valletta, Malta"
                }
            )
            opportunity.save()

    def test_one_day_opportunity_with_days_of_week(self):
        # Testing that a one-off opportunity cannot have days of the week
        with self.assertRaises(ValidationError):
            opportunity = VolunteerOpportunity.objects.create(
                organization=self.organization,
                title="One-Day Opportunity with Days",
                description="An invalid one-day opportunity with days of the week.",
                work_basis="in-person",
                duration="short-term",
                opportunity_date=date.today() + relativedelta(days=15),
                days_of_week=["monday"],
                area_of_work="Health",
                requirements=["Medical knowledge"],
                ongoing=False,
                application_deadline=date.today() + relativedelta(days=10),
                required_location={
                    "lat": 35.8995,
                    "lon": 14.5146,
                    "city": "Valletta",
                    "formatted_address": "Valletta, Malta"
                }
            )
            opportunity.full_clean()

    def test_one_day_opportunity_without_application_date(self):
        # Testing that a one-off opportunity must have an opportunity date
        with self.assertRaises(ValidationError):
            opportunity=VolunteerOpportunity.objects.create(
                organization=self.organization,
                title="One-Day Opportunity without Date",
                description="An invalid one-day opportunity without a date.",
                work_basis="in-person",
                duration="short-term",
                area_of_work="Health",
                requirements=["Medical knowledge"],
                ongoing=False,
                required_location={
                    "lat": 35.8995,
                    "lon": 14.5146,
                    "city": "Valletta",
                    "formatted_address": "Valletta, Malta"
                }
            )
            opportunity.full_clean()

    def test_invalid_duration(self):
        with self.assertRaises(ValidationError):
            opportunity = VolunteerOpportunity.objects.create(
                organization=self.organization,
                title="Invalid Duration",
                description="Opportunity with invalid duration.",
                work_basis="online",
                duration="invalid-term",
                opportunity_date=date.today() + relativedelta(days=10),
                area_of_work="Education",
                requirements=["Requirement 1"],
                ongoing=False,
                required_location={
                    "lat": 35.8995,
                    "lon": 14.5146,
                    "city": "Valletta",
                    "formatted_address": "Valletta, Malta"
                }
            )
            opportunity.full_clean()

    def test_invalid_days_of_week(self):
        with self.assertRaises(ValidationError) as context:
            opportunity = VolunteerOpportunity(
                organization=self.organization,
                title="Invalid Days of Week",
                description="Opportunity with invalid days of week.",
                work_basis="in-person",
                duration="short-term",
                days_of_week=["invalid-day"],
                area_of_work="Environment",
                requirements=["Requirement 1"],
                ongoing=True,
                required_location={
                    "lat": 35.8995,
                    "lon": 14.5146,
                    "city": "Valletta",
                    "formatted_address": "Valletta, Malta"
                }
            )
            opportunity.full_clean()
        self.assertIn("Invalid choices in days_of_week", str(context.exception))

    def test_empty_requirements(self):
        with self.assertRaises(ValidationError) as context:
            opportunity = VolunteerOpportunity.objects.create(
                organization=self.organization,
                title="No Requirements",
                description="Opportunity without requirements.",
                work_basis="online",
                duration="short-term",
                opportunity_date=date.today() + relativedelta(days=10),
                area_of_work="technology",
                requirements=[],  # Empty list should not be allowed
                ongoing=False,
                required_location={
                    "lat": 35.8995,
                    "lon": 14.5146,
                    "city": "Valletta",
                    "formatted_address": "Valletta, Malta"
                }
            )
            opportunity.full_clean()
        self.assertIn("This field cannot be blank", str(context.exception))
    
    def test_invalid_required_location(self):
        with self.assertRaises(ValidationError) as context:
            opportunity = VolunteerOpportunity.objects.create(
                organization=self.organization,
                title="Invalid location",
                description="Opportunity with invalid location.",
                work_basis="online",
                duration="short-term",
                opportunity_date=date.today() + relativedelta(days=10),
                area_of_work="community",
                requirements=["Strong communication skills"],
                ongoing=False,
                required_location="Not a JSON"  # Invalid format
            )
            opportunity.full_clean()
        self.assertIn("Required location must be a valid JSON object.", str(context.exception))


class TestVolunteerOpportunityApplicationModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, cls.organization_account = create_common_objects()
        cls.organization=Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Earth",
            organization_description="An organization dedicated to environmental conservation",
            organization_address={
                'raw': '123 Greenway Blvd, Springfield, US',
                'street_number': '123',
                'route': 'Greenway Blvd',
                'locality': 'Springfield',
                'postal_code': '12345',
                'state': 'Illinois',
                'state_code': 'IL',
                'country': 'United States',
                'country_code': 'US'
            }
        )
        cls.volunteer=Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1990, 1, 1)
        )
        cls.opportunity=VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Teach Kids Coding",
            description="A short-term opportunity to teach coding to kids.",
            work_basis="online",
            duration="short-term",
            area_of_work="education",
            opportunity_date=date.today() + relativedelta(days=10),
            application_deadline=date.today() + relativedelta(days=5),
            slots=5
        )

    def test_valid_application_creation(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
        )
        self.assertEqual(application.application_status, "pending")
        self.assertEqual(application.no_of_additional_volunteers, 0)
        self.assertFalse(application.as_group)

    def test_application_status_change(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
        )
        application.application_status = "accepted"
        application.save()
        self.assertEqual(application.application_status, "accepted")

    def test_as_group_false_requires_no_additional_volunteers(self):
        with self.assertRaises(ValidationError) as context:
            application = VolunteerOpportunityApplication(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
                as_group=False,
                no_of_additional_volunteers=3,
            )
            application.full_clean()
        self.assertIn("Number of additional volunteers must be zero if applying alone.", str(context.exception))

    def test_as_group_true_requires_additional_volunteers(self):
        with self.assertRaises(ValidationError) as context:
            application = VolunteerOpportunityApplication(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
                as_group=True,
                no_of_additional_volunteers=0,
            )
            application.full_clean()
        self.assertIn("Group applications must have at least one additional volunteer.",str(context.exception))

    def test_unique_volunteer_opportunity_application(self):
        VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
        )
        with self.assertRaises(IntegrityError):
            VolunteerOpportunityApplication.objects.create(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
            )

    def test_no_slots_available(self):
        # Create an opportunity with no slots left
        self.opportunity.slots = 0
        self.opportunity.save()

        with self.assertRaises(ValidationError) as context:
            application = VolunteerOpportunityApplication(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
            )
            application.full_clean()
        self.assertIn("No slots available for this opportunity.",str(context.exception))

    def test_rationale_optional(self):
        application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            rationale=None  # Should be allowed
        )
        self.assertIsNone(application.rationale)

class TestVolunteerEngagementModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, cls.organization_account = create_common_objects()
        cls.organization = Organization.objects.create(
            account=cls.organization_account,
            organization_name="Save the Earth",
            organization_description="An organization dedicated to environmental conservation",
            organization_address={
                'raw': '123 Greenway Blvd, Springfield, US',
                'street_number': '123',
                'route': 'Greenway Blvd',
                'locality': 'Springfield',
                'postal_code': '12345',
                'state': 'Illinois',
                'state_code': 'IL',
                'country': 'United States',
                'country_code': 'US'
            }
        )
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1990, 1, 1)
        )
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Teach Kids Coding",
            description="A short-term opportunity to teach coding to kids.",
            work_basis="online",
            duration="short-term",
            area_of_work="education",
            opportunity_date=date.today() + relativedelta(days=10),
            application_deadline=date.today() + relativedelta(days=5)
        )
        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

    def test_create_engagement_from_application(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )
        self.assertEqual(engagement.volunteer, self.volunteer)
        self.assertEqual(engagement.organization, self.organization)
        self.assertEqual(engagement.engagement_status, "ongoing")
        self.assertIsNotNone(engagement.start_date)
        self.assertIsNone(engagement.end_date)

    def test_completed_engagement_sets_end_date(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )
        engagement.engagement_status = "completed"
        engagement.save()
        self.assertEqual(engagement.engagement_status, "completed")
        self.assertIsNotNone(engagement.end_date)

    def test_cancelled_engagement_sets_end_date(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )
        engagement.engagement_status = "cancelled"
        engagement.save()
        self.assertEqual(engagement.engagement_status, "cancelled")
        self.assertIsNotNone(engagement.end_date)

    def test_engagement_creation_with_rejected_application(self):
        self.application.application_status = "rejected"
        self.application.save()

        with self.assertRaises(ValidationError) as context:
            engagement = VolunteerEngagement.objects.create(
                volunteer_opportunity_application=self.application
            )
            engagement.full_clean()
        self.assertIn(
            "Volunteer engagement must be created from an accepted application.",
            str(context.exception)
        )

    def test_engagement_creation_with_pending_application(self):
        self.application.application_status = "pending"
        self.application.save()

        with self.assertRaises(ValidationError) as context:
            engagement = VolunteerEngagement.objects.create(
                volunteer_opportunity_application=self.application
            )
            engagement.full_clean()
        self.assertIn(
            "Volunteer engagement must be created from an accepted application.",
            str(context.exception)
        )

    def test_end_date_cannot_be_before_start_date(self):
        engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )
        engagement.end_date = engagement.start_date - relativedelta(days=1)

        with self.assertRaises(ValidationError) as context:
            engagement.full_clean()
        self.assertIn("End date cannot be before start date.", str(context.exception))

    def test_unique_engagement_per_application(self):
        VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )
        with self.assertRaises(IntegrityError):
            VolunteerEngagement.objects.create(
                volunteer_opportunity_application=self.application
            )

class TestVolunteerEngagementLogModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, cls.organization_account = create_common_objects()
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

        # Set up an Ongoing Volunteer Opportunity
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Weekly Coding Workshop",
            description="Teach coding to beginners.",
            work_basis="in-person",
            duration="long-term",
            area_of_work="education",
            ongoing=True,
            days_of_week=["saturday", "sunday"]
        )

        # Volunteer Application (Accepted)
        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        # Volunteer Engagement
        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application
        )

        # Create a Session under the Opportunity
        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.opportunity,
            title="Intro to Python",
            description="Session for teaching Python basics.",
            session_date=date.today() + relativedelta(days=12),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),  # 2-hour session
            slots=10
        )

        # Volunteer Session Engagement (Default: cant_go)
        cls.session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=cls.engagement,
            session=cls.session,
            status="can_go"
        )

    # Ensure a valid engagement log can be created
    def test_valid_log_creation(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session_engagement,
            no_of_hours=1.5,
            log_notes="Helped teach Python basics."
        )
        self.assertEqual(log.volunteer_engagement, self.engagement)
        self.assertEqual(log.session, self.session_engagement)
        self.assertEqual(log.no_of_hours, 1.5)
        self.assertEqual(log.log_notes, "Helped teach Python basics.")
        self.assertEqual(log.status, "pending")

    # Ensure an invalid status raises a ValidationError
    def test_invalid_status(self):
        with self.assertRaises(ValidationError) as context:
            log = VolunteerEngagementLog(
                volunteer_engagement=self.engagement,
                session=self.session_engagement,
                no_of_hours=1.5,
                status="invalid_status"
            )
            log.full_clean()
        self.assertIn("Invalid status", str(context.exception))

    # Ensure `no_of_hours` cannot be zero or negative
    def test_no_of_hours_zero_or_negative(self):
        log = VolunteerEngagementLog(
            volunteer_engagement=self.engagement,
            session=self.session_engagement,
            no_of_hours=0,
            log_notes="Invalid hours test.",
            status="pending"
        )
        with self.assertRaises(ValidationError) as context:
            log.full_clean()
        self.assertIn("Number of hours must be greater than zero.", str(context.exception))

        log.no_of_hours = -1.0
        with self.assertRaises(ValidationError) as context:
            log.full_clean()
        self.assertIn("Number of hours must be greater than zero.", str(context.exception))

    # Ensure ongoing opportunities require logs to be linked to a session engagement
    def test_ongoing_opportunity_log_must_have_session_engagement(self):
        self.opportunity.ongoing = True
        self.opportunity.application_deadline = None
        self.opportunity.days_of_week = ["monday", "wednesday"]
        self.opportunity.save()

        with self.assertRaises(ValidationError) as context:
            log = VolunteerEngagementLog.objects.create(
                volunteer_engagement=self.engagement,
                session=None,  # No session engagement
                no_of_hours=2.0,
                log_notes="Should be linked to a session engagement."
            )
            log.full_clean()
        self.assertIn("Ongoing opportunities require logs to be linked to a session.", str(context.exception))

    # Ensure duplicate logs for the same engagement & session are not allowed
    def test_prevent_duplicate_logs_for_same_engagement_and_session(self):
        
        log1 = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session_engagement,
            no_of_hours=1.5,
            log_notes="First log."
        )

        with self.assertRaises(IntegrityError):
            VolunteerEngagementLog.objects.create(
                volunteer_engagement=self.engagement,
                session=self.session_engagement,  # Same session engagement
                no_of_hours=1.0,
                log_notes="Duplicate log."
            )

class TestVolunteerOpportunitySessionModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, cls.organization_account = create_common_objects()

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

        # Set up Volunteer Opportunity (ongoing)
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Weekly Coding Workshop",
            description="Teach coding to beginners.",
            work_basis="in-person",
            duration="long-term",
            area_of_work="education",
            ongoing=True,
            days_of_week=["saturday", "sunday"]
        )

    # Ensure a valid session can be created
    def test_valid_session_creation(self):
        session = VolunteerOpportunitySession.objects.create(
            opportunity=self.opportunity,
            title="Intro to Python",
            description="Learn the basics of Python.",
            session_date=date.today() + relativedelta(days=7),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            slots=10
        )
        self.assertEqual(session.opportunity, self.opportunity)
        self.assertEqual(session.title, "Intro to Python")
        self.assertEqual(session.session_date, date.today() + relativedelta(days=7))
        self.assertEqual(session.slots, 10)

    # Session start time must be before the end time
    def test_invalid_session_start_time_after_end_time(self):
        with self.assertRaises(ValidationError) as context:
            session = VolunteerOpportunitySession(
                opportunity=self.opportunity,
                title="Invalid Time Session",
                session_date=date.today() + relativedelta(days=7),
                session_start_time=time(15, 0),
                session_end_time=time(14, 0),
                slots=5
            )
            session.full_clean()
        self.assertIn("Session start time must be before end time.", str(context.exception))

    # Slots must be a positive integer if set
    def test_invalid_negative_slots(self):
        with self.assertRaises(ValidationError) as context:
            session = VolunteerOpportunitySession(
                opportunity=self.opportunity,
                title="Negative Slots",
                session_date=date.today() + relativedelta(days=7),
                session_start_time=time(10, 0),
                session_end_time=time(12, 0),
                slots=-5
            )
            session.full_clean()
        self.assertIn("Slots must be a positive integer if set.", str(context.exception))

    # Ensure session can be created without specifying slots
    def test_optional_slots(self):
        session = VolunteerOpportunitySession.objects.create(
            opportunity=self.opportunity,
            title="Session Without Slots",
            session_date=date.today() + relativedelta(days=7),
            session_start_time=time(14, 0),
            session_end_time=time(16, 0)
        )
        self.assertIsNone(session.slots)  # Slots should be None if not set

    # Ensure sessions are ordered by session_date and session_start_time
    def test_sessions_are_ordered_correctly(self):
        session1 = VolunteerOpportunitySession.objects.create(
            opportunity=self.opportunity,
            title="Morning Session",
            session_date=date.today() + relativedelta(days=10),
            session_start_time=time(9, 0),
            session_end_time=time(11, 0)
        )

        session2 = VolunteerOpportunitySession.objects.create(
            opportunity=self.opportunity,
            title="Afternoon Session",
            session_date=date.today() + relativedelta(days=10),
            session_start_time=time(14, 0),
            session_end_time=time(16, 0)
        )

        session3 = VolunteerOpportunitySession.objects.create(
            opportunity=self.opportunity,
            title="Earlier Date Session",
            session_date=date.today() + relativedelta(days=5),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0)
        )

        sessions = list(VolunteerOpportunitySession.objects.all())
        self.assertEqual(sessions[0], session3)  # Earlier date should come first
        self.assertEqual(sessions[1], session1)  # Then morning session
        self.assertEqual(sessions[2], session2)  # Then afternoon session

    # Ensure session cannot be created without a linked opportunity
    def test_session_must_be_linked_to_valid_opportunity(self):
        with self.assertRaises(ValidationError) as context:
            session = VolunteerOpportunitySession(
                opportunity=None,
                title="Unlinked Session",
                session_date=date.today() + relativedelta(days=7),
                session_start_time=time(10, 0),
                session_end_time=time(12, 0),
                slots=5
            )
            session.full_clean()
        self.assertIn("opportunity", str(context.exception))  # Checking for missing opportunity error

class TestVolunteerSessionEngagementModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.volunteer_account, cls.organization_account = create_common_objects()

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

        # Set up Volunteer
        cls.volunteer = Volunteer.objects.create(
            account=cls.volunteer_account,
            first_name="John",
            last_name="Doe",
            dob=date(1995, 1, 1)
        )

        # Set up an Ongoing Volunteer Opportunity
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Weekly Coding Workshop",
            description="Teach coding to beginners.",
            work_basis="in-person",
            duration="long-term",
            area_of_work="education",
            ongoing=True,
            days_of_week=["saturday", "sunday"]
        )

        # Volunteer Application (Accepted)
        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            application_status="accepted"
        )

        # Volunteer Engagement
        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application
        )

        # Create a Session under the Opportunity
        cls.session = VolunteerOpportunitySession.objects.create(
            opportunity=cls.opportunity,
            title="Intro to Python",
            session_date=date.today() + relativedelta(days=7),
            session_start_time=time(10, 0),
            session_end_time=time(12, 0),
            slots=2  # Limited slots
        )

    # Ensure valid session engagement can be created
    def test_valid_session_engagement_creation(self):
        session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="can_go"
        )
        self.assertEqual(session_engagement.session, self.session)
        self.assertEqual(session_engagement.volunteer_engagement, self.engagement)
        self.assertEqual(session_engagement.status, "can_go")

    # Ensure volunteer cannot engage in sessions outside their opportunity
    def test_session_must_belong_to_opportunity(self):
        another_opportunity = VolunteerOpportunity.objects.create(
            organization=self.organization,
            title="Different Workshop",
            description="A different volunteer opportunity.",
            work_basis="in-person",
            duration="long-term",
            area_of_work="technology",
            ongoing=True,
            days_of_week=["monday", "wednesday"]
        )

        another_session = VolunteerOpportunitySession.objects.create(
            opportunity=another_opportunity,
            title="Unrelated Session",
            session_date=date.today() + relativedelta(days=7),
            session_start_time=time(15, 0),
            session_end_time=time(17, 0),
            slots=5
        )

        with self.assertRaises(ValidationError) as context:
            session_engagement = VolunteerSessionEngagement(
                volunteer_engagement=self.engagement,
                session=another_session,
                status="can_go"
            )
            session_engagement.full_clean()
        self.assertIn("Session does not belong to the same opportunity as the engagement.", str(context.exception))

    # Ensure volunteers cannot join a session if all slots are full
    def test_cannot_join_fully_booked_session(self):
        VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="can_go"
        )

        # Create another volunteer for testing
        another_account = Account.objects.create(
            email_address='test_email_1vol@tester.com',
            password='testerpassword',
            user_type='volunteer',
            contact_number="+35612345675"
        )
        another_volunteer = Volunteer.objects.create(
            account=another_account,
            first_name="Jane",
            last_name="Smith",
            dob=date(1993, 5, 15)
        )

        another_application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=another_volunteer,
            application_status="accepted"
        )

        another_engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=another_application
        )

        VolunteerSessionEngagement.objects.create(
            volunteer_engagement=another_engagement,
            session=self.session,
            status="can_go"
        )

        # Now the session should be full (slots=2)
        third_account = Account.objects.create(
            email_address='test_email_2vol@tester.com',
            password='testerpassword',
            user_type='volunteer',
            contact_number="+35612345671"
        )
        third_volunteer = Volunteer.objects.create(
            account=third_account,
            first_name="Mike",
            last_name="Brown",
            dob=date(1998, 2, 22)
        )

        third_application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=third_volunteer,
            application_status="accepted"
        )

        third_engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=third_application
        )

        with self.assertRaises(ValidationError) as context:
            third_session_engagement = VolunteerSessionEngagement(
                volunteer_engagement=third_engagement,
                session=self.session,
                status="can_go"
            )
            third_session_engagement.full_clean()
        self.assertIn("This session is fully booked.", str(context.exception))

    # Ensure volunteer cannot have multiple engagements for the same session
    def test_unique_session_engagement(self):
        VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session,
            status="can_go"
        )

        with self.assertRaises(ValidationError) as context:
            duplicate_session_engagement = VolunteerSessionEngagement(
                volunteer_engagement=self.engagement,
                session=self.session,
                status="can_go"
            )
            duplicate_session_engagement.full_clean()
        self.assertIn("Volunteer session engagement with this Volunteer engagement and Session already exists.", str(context.exception))

    # Ensure default status is set to 'cant_go'
    def test_default_status_is_cant_go(self):
        session_engagement = VolunteerSessionEngagement.objects.create(
            volunteer_engagement=self.engagement,
            session=self.session
        )
        self.assertEqual(session_engagement.status, "cant_go")

