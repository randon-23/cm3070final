from django.db import models
from volunteers_organizations.models import Organization, Volunteer
import uuid
from django.utils.timezone import now
from django.core.exceptions import ValidationError

class VolunteerOpportunity(models.Model):
    WORK_BASIS_TYPES = (
        ('online', 'Online'),
        ('in-person', 'In-Person'),
        ('both', 'Both'),
    )

    DURATION_CHOICES = (
        ('short-term', 'Short-Term'),
        ('medium-term', 'Medium-Term'),
        ('long-term', 'Long-Term')
    )

    DAYS_OF_WEEK_CHOICES = (
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday')
    )

    FIELDS_OF_INTEREST_CHOICES=[
        ('education', 'Education'),
        ('health', 'Health'),
        ('environment', 'Environment'),
        ('animals', 'Animals'),
        ('arts', 'Arts'),
        ('community', 'Community'),
        ('sports', 'Sports'),
        ('technology', 'Technology'),
        ('other', 'Other')
    ]

    SKILLS_CHOICES = [
        ('communication', 'Communication'),
        ('public speaking', 'Public Speaking'),
        ('leadership', 'Leadership'),
        ('teamwork', 'Teamwork'),
        ('physical fitness', 'Physical Fitness'),
        ('able to work outdoors', 'Able to Work Outdoors'),
        ('time management', 'Time Management'),
        ('problem solving', 'Problem Solving'),
        ('organization', 'Organization'),
        ('creativity', 'Creativity'),
        ('writing', 'Writing'),
        ('editing', 'Editing'),
        ('graphic design', 'Graphic Design'),
        ('photography', 'Photography'),
        ('videography', 'Videography'),
        ('fundraising', 'Fundraising'),
        ('marketing', 'Marketing'),
        ('event planning', 'Event Planning'),
        ('data analysis', 'Data Analysis'),
        ('coding', 'Coding'),
        ('web development', 'Web Development'),
        ('it support', 'IT Support'),
        ('social media management', 'Social Media Management'),
        ('first aid', 'First Aid'),
        ('teaching', 'Teaching'),
        ('coaching', 'Coaching'),
        ('research', 'Research'),
        ('translation', 'Translation'),
        ('budget management', 'Budget Management'),
        ('conflict resolution', 'Conflict Resolution'),
        ('counseling', 'Counseling'),
        ('mentoring', 'Mentoring'),
        ('advocacy', 'Advocacy'),
        ('crisis management', 'Crisis Management'),
        ('volunteer coordination', 'Volunteer Coordination'),
        ('environmental conservation', 'Environmental Conservation'),
        ('community outreach', 'Community Outreach'),
        ('food preparation', 'Food Preparation'),
        ('medical assistance', 'Medical Assistance'),
        ('legal assistance', 'Legal Assistance'),
        ('accounting', 'Accounting'),
        ('language proficiency', 'Language Proficiency'),
        ('project management', 'Project Management'),
    ]

    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    volunteer_opportunity_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    work_basis = models.CharField(max_length=10, choices=WORK_BASIS_TYPES)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES, default='short-term')
    # One-time opportunities must have a date/time, ongoing ones should not
    opportunity_date = models.DateField(null=True, blank=True)
    opportunity_time_from = models.TimeField(null=True, blank=True)
    opportunity_time_to = models.TimeField(null=True, blank=True)
    # Ongoing opportunities must have days of the week, one-time should not
    days_of_week = models.JSONField(default=list, null=True, blank=True)
    # Fields of interest must be chosen from predefined categories
    area_of_work = models.CharField(max_length=100, choices=FIELDS_OF_INTEREST_CHOICES)
    # Requirements must be JSON but validated in the serializer
    requirements = models.JSONField(default=list) # Validated in serializer
    # Ongoing = true means it runs indefinitely
    ongoing = models.BooleanField(default=False)
    # Application deadline is only relevant for one-time opportunities
    application_deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    can_apply_as_group = models.BooleanField(default=False)
    # Location field (set to organization location by default in serializer)
    required_location = models.JSONField(default=dict)
     # Contribution hours are calculated dynamically in the serializer
    status = models.CharField(max_length=20, default='upcoming', choices=STATUS_CHOICES)
    # Slots are only used for one-time opportunities
    slots = models.IntegerField(default=None, blank=True, null=True) # Available slots for one-time opportunities, None for ongoing

    class Meta:
        ordering = ['created_at']
        constraints = [
            #If ongoing is true, then application_deadline must be null   
            models.CheckConstraint(
                check=models.Q(ongoing=False) | models.Q(application_deadline__isnull=True),
                name='check_application_deadline_null_if_ongoing'
            )
        ]

    def clean(self):
        super().clean()

        ### 1. Data Integrity: Days of Week must be a valid list ###
        if not isinstance(self.days_of_week, list):
            raise ValidationError("Days of week must be a list.")
        days_choices = [choice[0] for choice in self.DAYS_OF_WEEK_CHOICES]
        invalid_days = [day for day in self.days_of_week if day not in days_choices]
        if invalid_days:
            raise ValidationError(f"Invalid choices in days_of_week: {invalid_days}")

        ### 2. Data Integrity: Required Location must be a valid JSON object ###
        if not isinstance(self.required_location, dict):
            raise ValidationError("Required location must be a valid JSON object.")

        ### 3. Data Integrity: Area of Work must be one of the predefined choices ###
        valid_fields = [choice[0] for choice in self.FIELDS_OF_INTEREST_CHOICES]
        if self.area_of_work not in valid_fields:
            raise ValidationError(f"Area of work must be one of {valid_fields}.")

    ### Business Logic to be moved to the serializer ###

    # Move to serializer: Enforcing required fields based on `ongoing` status
    # If ongoing, ensure days_of_week is required, opportunity_date is null.
    # If one-time, ensure opportunity_date, start time, and end time are required.
    # Check that requirements match the predefined skills list.

    # test_one_day_opportunity_without_slots and test_ongoing_opportunity_with_slots and test_conflicting_date_and_days_of_week

    # Move to serializer: Checking that application_deadline is null for ongoing opportunities.
    # Check that the application deadline is in the future for one-time opportunities.
    # This is an API validation rule rather than a strict database constraint.
            
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class VolunteerOpportunityApplication(models.Model):
    APPLICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    )

    volunteer_opportunity_application_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volunteer_opportunity = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    application_status = models.CharField(max_length=20, default='pending', choices=APPLICATION_STATUS_CHOICES)
    as_group = models.BooleanField(default=False)
    no_of_additional_volunteers = models.IntegerField(default=0)
    rationale = models.TextField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['volunteer_opportunity', 'volunteer'],
                name='unique_volunteer_opportunity_application'
            )
        ]

    # Enforces constraints at model level but doesn't modify data.
    def clean(self):
        if not self.volunteer_opportunity.ongoing and self.volunteer_opportunity.slots is not None and self.volunteer_opportunity.slots <= 0:
            raise ValidationError("No slots available for this opportunity.")
        if not self.as_group and self.no_of_additional_volunteers != 0:
            raise ValidationError("Number of additional volunteers must be zero if applying alone.")
        if self.as_group and self.no_of_additional_volunteers < 1:
            raise ValidationError("Group applications must have at least one additional volunteer.")
        
    # Logic for serializer: 
    # Deducting slots only when application is accepted

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class VolunteerOpportunitySession(models.Model):
    STATUS_CHOICES = [
        ('upcoming', 'Upcoming'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    session_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    opportunity = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500, blank=True)
    session_date = models.DateField()
    session_start_time = models.TimeField()
    session_end_time = models.TimeField()
    status = models.CharField(max_length=20, default='upcoming', choices=STATUS_CHOICES)
    slots = models.PositiveIntegerField(null=True, blank=True)  # Optional limitation on slots

    class Meta:
        ordering = ['session_date', 'session_start_time']

    def clean(self):
        if self.slots is not None and self.slots < 1:
            raise ValidationError("Slots must be a positive integer if set.")
        if self.session_start_time >= self.session_end_time:
            raise ValidationError("Session start time must be before end time.")

    # Logic for serializer:
    # Enforce available slots before accepting a volunteer for a session
    # Automatically create VolunteerSessionEngagement for all engaged volunteers
    # Volunteers should only be able to attend sessions/have session engagements be created if they are engaged with the related opportunity
    # For users being engaged with an opportunity, they should have session engagements created automatically

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class VolunteerEngagement(models.Model):
    ENGAGEMENT_STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    )

    volunteer_engagement_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
    volunteer_opportunity_application = models.OneToOneField(VolunteerOpportunityApplication, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)  # Redundant FK for easier queries
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)  # Redundant FK for easier queries
    engagement_status = models.CharField(max_length=20, default='ongoing', choices=ENGAGEMENT_STATUS_CHOICES)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensure only one engagement per application
        constraints = [
            models.UniqueConstraint(
                fields=['volunteer_opportunity_application'],
                name='unique_engagement_per_application'
            )
        ]

    def clean(self):
        # Volunteer must be engaged in the opportunity before attending a session.
        # The session must belong to the same opportunity the volunteer is engaged with.
        # If the session has a slot limit, prevent overbooking.
        if self.volunteer_opportunity_application.application_status != 'accepted':
            raise ValidationError("Volunteer engagement must be created from an accepted application.")
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
        
        super().clean()

    # Logic for serializer:
    # Restricting status changes (e.g., cannot manually mark ongoing → completed if logs aren't done).
    # Triggering automatic engagement logs when marking completed.
    # Validating if all required volunteer sessions are completed before allowing completed status.

    def save(self, *args, **kwargs):
        if self.engagement_status in ['completed', 'cancelled'] and not self.end_date:
            self.end_date = now().date()

        self.organization = self.volunteer_opportunity_application.volunteer_opportunity.organization
        self.volunteer = self.volunteer_opportunity_application.volunteer

        super().save(*args, **kwargs)

class VolunteerSessionEngagement(models.Model):
    STATUS_CHOICES = [
        ('cant_go', 'Can\'t Go'),
        ('can_go', 'Can Go'),
    ]

    session_engagement_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volunteer_engagement = models.ForeignKey(VolunteerEngagement, on_delete=models.CASCADE)
    session = models.ForeignKey(VolunteerOpportunitySession, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='cant_go')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['volunteer_engagement', 'session'],
                name='unique_volunteer_session_engagement'
            )
        ]

    def clean(self):
        # Ensure the session belongs to the same opportunity as the engagement
        if self.session.opportunity != self.volunteer_engagement.volunteer_opportunity_application.volunteer_opportunity:
            raise ValidationError("Session does not belong to the same opportunity as the engagement.")

        # Check if session slots are full
        if self.session.slots is not None:  # Only enforce if slots exist
            current_attendees = VolunteerSessionEngagement.objects.filter(session=self.session, status="can_go").count()
            if current_attendees >= self.session.slots:
                raise ValidationError("This session is fully booked.")

    # Logic for serializer:
    # Allow volunteers to update their status (can_go or cant_go).
    # Ensure volunteers can only change their status within a set timeframe (e.g., can’t cancel last minute).
    # Auto-generate session engagements for all volunteers when a session is created (default to cant_go).

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

class VolunteerEngagementLog(models.Model):
    ENGAGEMENT_STATUS_LOG_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    )

    volunteer_engagement_log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    # The volunteer engagement that this log is associated with, and if ongoing, the associated session
    volunteer_engagement = models.ForeignKey(VolunteerEngagement, on_delete=models.CASCADE)
    session = models.ForeignKey(VolunteerSessionEngagement, null=True, blank=True, on_delete=models.CASCADE)
    no_of_hours = models.FloatField(default=0.5) # Calculate from api endpoint and validate in serializer
    status = models.CharField(max_length=20, default='pending', choices=ENGAGEMENT_STATUS_LOG_CHOICES)
    log_notes = models.TextField(max_length=500, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['volunteer_engagement', 'session'],
                name='unique_volunteer_log_per_session'
            )
        ]

    def clean(self):
        # Data integrity:
        # Logs must be linked to a valid engagement.
        # No duplicate logs for the same engagement/session per day.
        # Logged hours must be within opportunity/session timeframe.
        
        if self.status not in [choice[0] for choice in self.ENGAGEMENT_STATUS_LOG_CHOICES]:
            raise ValidationError(f"Invalid status: {self.status}")

        if self.no_of_hours <= 0:
            raise ValidationError("Number of hours must be greater than zero.")

        # Ensure log is linked to a session **only if the opportunity is ongoing**
        if not self.session and self.volunteer_engagement.volunteer_opportunity_application.volunteer_opportunity.ongoing:
            raise ValidationError("Ongoing opportunities require logs to be linked to a session.")

        super().clean()

    # Logic for serializer:
    # This logic ensures that the logged hours do not exceed the session or opportunity time duration.
    # If the log is for a session, it checks that logged hours do not exceed `session_end_time - session_start_time`.
    # If the log is for a one-time opportunity, it checks that logged hours do not exceed `opportunity_time_to - opportunity_time_from`.
    # This validation should be performed in the serializer where we handle user input and enforce business rules before saving.
    # Checking that no_of_hours ≤ session/opportunity time range
    # Validating that logs aren’t created in advance for future opportunities
    # Ensure logs cannot be created for opportunities/sessions in the future
    # Prevent volunteers from submitting multiple logs for the same session/day

    def save(self, *args, **kwargs):
        self.clean()  # Ensures data integrity before saving
        super().save(*args, **kwargs)
        
# NEED TO ADD VALIDATION IN API/SERIALIZER WIHCH CHECK  S THAT THE PROPOSED NUMBER OF HOURS 
# DOES NOT OVERLAP WITH THE PREVIOUSLY LOGGED HOURS

# Requirement to be added to Volunteer model OR skills attribute in the VolunteerMatchingPreferences model would have acceptable
# choices which from opotrunity side will be validated

# If ongoing, then end_date would be null. Additionally, users trigger engagement logs themselves,
# Otherwise, a non-ongoing enegagement will trigger the engagement log automatically