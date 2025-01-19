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

    volunteer_opportunity_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(max_length=500)
    work_basis = models.CharField(max_length=10, choices=WORK_BASIS_TYPES)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    opportunity_date = models.DateField(null=True, blank=True)
    days_of_week = models.JSONField(default=list, null=True, blank=True)
    area_of_work = models.CharField(max_length=100)
    requirements = models.JSONField(default=list)
    ongoing = models.BooleanField(default=False)
    application_deadline = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    can_apply_as_group = models.BooleanField(default=False)

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
             
        # Validate 'days_of_week'
        if not isinstance(self.days_of_week, list):
            raise ValidationError("Days of week must be a list.")
        
        days_choices = [choice[0] for choice in self.DAYS_OF_WEEK_CHOICES]
        invalid_days = [day for day in self.days_of_week if day not in days_choices]
        
        if invalid_days:
            raise ValidationError(f"Invalid choices in days_of_week: {invalid_days}")

        # Additional validations for 'ongoing', 'opportunity_date', and 'days_of_week'
        if self.ongoing:
            if self.application_deadline is not None:
                raise ValidationError("Application deadline must be null for ongoing opportunities.")
            if self.opportunity_date is not None:
                raise ValidationError("Opportunity date must be null for ongoing opportunities.")
            if not self.days_of_week:
                raise ValidationError("Days of week must have at least one day for ongoing opportunities.")
        else:  # If not ongoing
            if self.opportunity_date is None:
                raise ValidationError("Opportunity date must not be null for one-time opportunities.")
            if self.application_deadline is not None and self.application_deadline < now().date():
                raise ValidationError("Opportunity date must be in the future.")
            if self.days_of_week:
                raise ValidationError("Days of week must be empty for one-time opportunities.")

class VolunteerOpportunityApplication(models.Model):
    APPLICATION_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    )

    volunteer_opportunity_application_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volunteer_opportunity = models.ForeignKey(VolunteerOpportunity, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    selected_work_basis = models.CharField(max_length=10, choices=VolunteerOpportunity.WORK_BASIS_TYPES)
    selected_duration = models.CharField(max_length=20, choices=VolunteerOpportunity.DURATION_CHOICES)
    selected_days_of_week = models.JSONField(default=list, null=True, blank=True)
    application_status = models.CharField(max_length=20, default='pending')
    as_group = models.BooleanField(default=False)
    no_of_additional_volunteers = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['volunteer_opportunity', 'volunteer'],
                name='unique_volunteer_opportunity_application'
            )
        ]
    
    def clean(self):
         # Validate 'days_of_week'
        if not isinstance(self.selected_days_of_week, list):
            raise ValidationError("Days of week must be a list.")
        
        days_choices = [choice[0] for choice in VolunteerOpportunity.DAYS_OF_WEEK_CHOICES]
        invalid_days = [day for day in self.selected_days_of_week if day not in days_choices]
        
        if invalid_days:
            raise ValidationError(f"Invalid choices in days_of_week: {invalid_days}")
        
        # Validate 'application_status
        if self.application_status not in [choice[0] for choice in self.APPLICATION_STATUS_CHOICES]:
            raise ValidationError(f"Invalid application status: {self.application_status}")
        
        # Ensure no_of_additional_volunteers is zero if as_group is False
        if not self.as_group and self.no_of_additional_volunteers != 0:
            raise ValidationError("Number of additional volunteers must be zero if applying as an individual.")

        if self.as_group and self.no_of_additional_volunteers < 1:
            raise ValidationError("Number of additional volunteers must be greater than zero if applying as a group.")

class VolunteerEngagement(models.Model):
    ENGAGEMENT_STATUS_CHOICES = (
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    )

    volunteer_engagement_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False),
    volunteer_opportunity_application = models.OneToOneField(VolunteerOpportunityApplication, on_delete=models.CASCADE)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)   # This is the volunteer who applied for the opportunity
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)   # This is the organization that posted the opportunity
    work_basis = models.CharField(max_length=10, choices=VolunteerOpportunity.WORK_BASIS_TYPES)
    duration = models.CharField(max_length=20, choices=VolunteerOpportunity.DURATION_CHOICES)
    days_of_week = models.JSONField(default=list)
    as_group = models.BooleanField(default=False)
    no_of_additional_volunteers = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    engagement_status = models.CharField(max_length=20, default='ongoing', choices=ENGAGEMENT_STATUS_CHOICES)
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.volunteer_opportunity_application:
            self.volunteer = self.volunteer_opportunity_application.volunteer
            self.organization = self.volunteer_opportunity_application.organization
            self.work_basis = self.volunteer_opportunity_application.selected_work_basis
            self.duration = self.volunteer_opportunity_application.selected_duration
            self.days_of_week = self.volunteer_opportunity_application.selected_days_of_week
            self.as_group = self.volunteer_opportunity_application.as_group
            self.no_of_additional_volunteers = self.volunteer_opportunity_application.no_of_additional_volunteers

        if self.engagement_status in ['completed', 'cancelled'] and not self.end_date:
            self.end_date = now().date()

        # Call the parent class's save() method
        super().save(*args, **kwargs)
    
    def clean(self):
        if self.volunteer_opportunity_application and self.volunteer_opportunity_application.application_status != 'accepted':
            raise ValidationError("Volunteer engagement must be created from an accepted application.")
        
        super().clean()

class VolunteerEngagementLog(models.Model):
    ENGAGEMENT_STATUS_LOG_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    )

    volunteer_engagement_log_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    volunteer_engagement = models.ForeignKey(VolunteerEngagement, on_delete=models.CASCADE)
    no_of_hours = models.FloatField(default=0.5)
    log_notes = models.TextField(max_length=500, default='')
    status = models.CharField(max_length=20, default='pending', choices=ENGAGEMENT_STATUS_LOG_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.status not in [choice[0] for choice in self.ENGAGEMENT_STATUS_LOG_CHOICES]:
            raise ValidationError(f"Invalid status: {self.status}")
        
        if self.no_of_hours <= 0:
            raise ValidationError("Number of hours must be greater than zero.")
        
    # NEED TO ADD VALIDATION IN API/SERIALIZER WIHCH CHECK  S THAT THE PROPOSED NUMBER OF HOURS 
    # DOES NOT OVERLAP WITH THE PREVIOUSLY LOGGED HOURS

    # Requirement to be added to Volunteer model OR skills attribute in the VolunteerMatchingPreferences model would have acceptable
    # choices which from opotrunity side will be validated

    # If ongoing, then end_date would be null. Additionally, users trigger engagement logs themselves,
    # Otherwise, a non-ongoing enegagement will trigger the engagement log automatically