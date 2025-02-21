from django.test import TestCase
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from ..models import VolunteerOpportunity, VolunteerOpportunityApplication, VolunteerEngagement, VolunteerEngagementLog
from volunteers_organizations.models import Volunteer, Organization
from accounts_notifs.models import Account
from datetime import date
from dateutil.relativedelta import relativedelta

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
            area_of_work="Environment",
            requirements=["Able to work outdoors"],
            application_deadline=date.today() + relativedelta(days=5),
            ongoing=False,
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
            area_of_work="Education",
            requirements=["Good communication skills"],
            application_deadline=None,
            ongoing=True,
        )
        self.assertTrue(opportunity.ongoing)
        self.assertIsNone(opportunity.opportunity_date)
        self.assertEqual(opportunity.days_of_week, ["monday", "wednesday"])

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
                area_of_work="Community",
                requirements=["Basic computer skills"],
                application_deadline=date.today() + relativedelta(days=5),
                ongoing=True,
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
            )
            opportunity.full_clean()
        self.assertIn("Invalid choices in days_of_week", str(context.exception))

    def test_empty_days_of_week_for_ongoing(self):
        with self.assertRaises(ValidationError) as context:
            opportunity = VolunteerOpportunity.objects.create(
                organization=self.organization,
                title="Empty Days of Week",
                description="An ongoing opportunity with empty days of the week.",
                work_basis="both",
                duration="long-term",
                days_of_week=[],
                area_of_work="Technology",
                requirements=["Tech knowledge"],
                ongoing=True,
            )
            opportunity.full_clean()
        self.assertIn("Days of week must have at least one day for ongoing", str(context.exception.message_dict["__all__"]))

    def test_empty_requirements(self):
        opportunity = VolunteerOpportunity.objects.create(
            organization=self.organization,
            title="No Requirements",
            description="Opportunity without requirements.",
            work_basis="online",
            duration="short-term",
            opportunity_date=date.today() + relativedelta(days=10),
            area_of_work="Technology",
            requirements=[],
            ongoing=False,
        )
        self.assertEqual(opportunity.requirements, [])

    def test_application_deadline_in_past(self):
        with self.assertRaises(ValidationError) as context:
            opportunity = VolunteerOpportunity.objects.create(
                organization=self.organization,
                title="Past Deadline",
                description="Opportunity with past application deadline.",
                work_basis="in-person",
                duration="short-term",
                opportunity_date=date.today() + relativedelta(days=5),
                area_of_work="Community",
                requirements=["Community knowledge"],
                application_deadline=date.today() - relativedelta(days=1),
                ongoing=False
            )
            opportunity.full_clean()
        self.assertIn("Opportunity date must be in the future.", str(context.exception))

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
            area_of_work="Education",
            opportunity_date=date.today() + relativedelta(days=10),
            application_deadline=date.today() + relativedelta(days=5)
        )

    def test_valid_application_creation(self):
        application=VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            organization=self.organization,
            selected_work_basis="online",
            selected_duration="short-term",
        )
        self.assertEqual(application.application_status, "pending")
        self.assertEqual(application.no_of_additional_volunteers, 0)
        self.assertEqual(application.as_group, False)

    def test_invalid_days_of_week(self):
        with self.assertRaises(ValidationError) as context:
            application = VolunteerOpportunityApplication.objects.create(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
                organization=self.organization,
                selected_work_basis="online",
                selected_duration="short-term",
                selected_days_of_week=["invalid_day"],
            )
            application.full_clean()
        self.assertIn("Invalid choices in days_of_week", str(context.exception))

    def test_invalid_application_status(self):
        with self.assertRaises(ValidationError) as context:
            application = VolunteerOpportunityApplication(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
                organization=self.organization,
                selected_work_basis="online",
                selected_duration="short-term",
                selected_days_of_week=["monday", "wednesday"],
                application_status="invalid_status",
            )
            application.full_clean()
        self.assertIn("Invalid application status", str(context.exception))

    def test_as_group_false_requires_no_additional_volunteers(self):
        with self.assertRaises(ValidationError) as context:
            application = VolunteerOpportunityApplication(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
                organization=self.organization,
                selected_work_basis="online",
                selected_duration="short-term",
                selected_days_of_week=["monday"],
                application_status="pending",
                as_group=False,
                no_of_additional_volunteers=3,
            )
            application.full_clean()
        self.assertIn("Number of additional volunteers must be zero", str(context.exception))
    
    def test_as_group_true_requires_additional_volunteers(self):
        with self.assertRaises(ValidationError) as context:
            application = VolunteerOpportunityApplication(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
                organization=self.organization,
                selected_work_basis="online",
                selected_duration="short-term",
                selected_days_of_week=["monday"],
                application_status="pending",
                as_group=True,
                no_of_additional_volunteers=0,
            )
            application.full_clean()
        self.assertIn("Number of additional volunteers must be greater than zero if applying as a group", str(context.exception))

    def test_unique_volunteer_opportunity_application(self):
        VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            organization=self.organization,
            selected_work_basis="online",
            selected_duration="short-term",
            selected_days_of_week=["monday"],
            application_status="pending",
        )
        with self.assertRaises(IntegrityError):
            VolunteerOpportunityApplication.objects.create(
                volunteer_opportunity=self.opportunity,
                volunteer=self.volunteer,
                organization=self.organization,
                selected_work_basis="online",
                selected_duration="short-term",
                selected_days_of_week=["monday"],
                application_status="pending",
            )

    def test_application_status_change(self):
        application=VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=self.opportunity,
            volunteer=self.volunteer,
            organization=self.organization,
            selected_work_basis="online",
            selected_duration="short-term",
            selected_days_of_week=["monday"],
            application_status="pending",
        )
        application.application_status="accepted"
        application.save()
        self.assertEqual(application.application_status, "accepted")

class TestVolunteerEngagementModel(TestCase):
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
            area_of_work="Education",
            opportunity_date=date.today() + relativedelta(days=10),
            application_deadline=date.today() + relativedelta(days=5)
        )
        cls.application=VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            organization=cls.organization,
            selected_work_basis="online",
            selected_duration="short-term",
            application_status="accepted"
        )

    def test_create_engagement_from_application(self):
        engagement=VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )
        self.assertEqual(engagement.volunteer, self.volunteer)
        self.assertEqual(engagement.organization, self.organization)
        self.assertEqual(engagement.work_basis, "online")
        self.assertEqual(engagement.duration, "short-term")
        self.assertEqual(engagement.days_of_week, [])
        self.assertFalse(engagement.as_group)
        self.assertEqual(engagement.no_of_additional_volunteers, 0)
        self.assertEqual(engagement.engagement_status, "ongoing")
        self.assertIsNotNone(engagement.start_date)
        self.assertIsNone(engagement.end_date)
    
    def test_completed_engagement_sets_end_date(self):
        engagement=VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )
        engagement.engagement_status="completed"
        engagement.save()
        self.assertEqual(engagement.engagement_status, "completed")
        self.assertIsNotNone(engagement.end_date)

    def test_cancelled_engagement_sets_end_date(self):
        engagement=VolunteerEngagement.objects.create(
            volunteer_opportunity_application=self.application
        )
        engagement.engagement_status="cancelled"
        engagement.save()
        self.assertEqual(engagement.engagement_status, "cancelled")
        self.assertIsNotNone(engagement.end_date)

    def test_engagement_without_application_raises_error(self):
        with self.assertRaises(Exception):
            VolunteerEngagement.objects.create(
                volunteer=self.volunteer,
                organization=self.organization,
                work_basis="online",
                duration="short-term",
                engagement_status="ongoing"
            )
    
    def test_engagement_creation_with_rejected_application(self):
        self.application.application_status="rejected"
        self.application.save()

        with self.assertRaises(ValidationError) as context:
            engagement=VolunteerEngagement.objects.create(
                volunteer_opportunity_application=self.application
            )
            engagement.full_clean()
        self.assertIn("Volunteer engagement must be created from an accepted application.", str(context.exception))

    def test_engagement_creation_with_pending_application(self):
        self.application.application_status="pending"
        self.application.save()

        with self.assertRaises(ValidationError) as context:
            engagement=VolunteerEngagement.objects.create(
                volunteer_opportunity_application=self.application
            )
            engagement.full_clean()
        self.assertIn("Volunteer engagement must be created from an accepted application.", str(context.exception))
        
class TestVolunteerEngagementLogModel(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Set up data for Volunteer and Organization
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
        cls.opportunity = VolunteerOpportunity.objects.create(
            organization=cls.organization,
            title="Teach Kids Coding",
            description="Help kids learn basic programming.",
            work_basis="online",
            duration="short-term",
            area_of_work="Education",
            opportunity_date=date.today() + relativedelta(days=10),
            application_deadline=date.today() + relativedelta(days=5)
        )
        cls.application = VolunteerOpportunityApplication.objects.create(
            volunteer_opportunity=cls.opportunity,
            volunteer=cls.volunteer,
            organization=cls.organization,
            selected_work_basis="online",
            selected_duration="short-term",
            application_status="accepted"
        )
        cls.engagement = VolunteerEngagement.objects.create(
            volunteer_opportunity_application=cls.application
        )
    
    def test_valid_log_creation(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement,
            no_of_hours=5.5,
            log_notes="Passed out food to the homeless."
        )
        self.assertEqual(log.volunteer_engagement, self.engagement)
        self.assertEqual(log.no_of_hours, 5.5)
        self.assertEqual(log.log_notes, "Passed out food to the homeless.")
        self.assertEqual(log.status, "pending")
    
    def test_invalid_creation(self):
        log=VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement,
            no_of_hours=-5.5,
            log_notes="Invalid log creation."
        )
        with self.assertRaises(ValidationError) as context:
            log.status="invalid_status"
            log.full_clean()
        self.assertIn("Invalid status", str(context.exception))
    
    def test_no_of_hours_zero_or_negative(self):
        log = VolunteerEngagementLog(
            volunteer_engagement=self.engagement,
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

    def test_default_values(self):
        log = VolunteerEngagementLog.objects.create(
            volunteer_engagement=self.engagement
        )
        self.assertEqual(log.no_of_hours, 0.5)
        self.assertEqual(log.log_notes, "")
        self.assertEqual(log.status, "pending")