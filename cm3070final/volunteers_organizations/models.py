from django.db import models
from accounts_notifs.models import Account
from datetime import datetime
from django.core.exceptions import ValidationError

class Volunteer(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    dob = models.DateField()
    bio = models.CharField(max_length=500, default='', blank=True)
    profile_img = models.ImageField(blank=True, null=True)
    volontera_points = models.IntegerField(default=0)
    followers = models.IntegerField(default=0)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class VolunteerMatchingPreferences(models.Model):
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
    
    WORK_TYPE_CHOICES = (
        ('online', 'Online'),
        ('in-person', 'In-Person'),
        ('both', 'Both')
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

    volunteer_preference_id = models.AutoField(primary_key=True)
    volunteer = models.OneToOneField(Volunteer, on_delete=models.CASCADE)
    availability = models.JSONField(default=list, blank=True)
    preferred_work_types = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES, default='both')
    preferred_duration = models.JSONField(default=list, blank=True)
    fields_of_interest = models.JSONField(default=list, blank=True)
    skills = models.JSONField(default=list, blank=True)

    def clean(self):
        super().clean()

        #Validate 'preferred_duration'
        if not isinstance(self.preferred_duration, list):
            raise ValidationError({"preferred_duration": "Preferred duration must be a list."})
        allowed_choices = [choice[0] for choice in self.DURATION_CHOICES]
        invalid_choices = [choice for choice in self.preferred_duration if choice not in allowed_choices]
        if invalid_choices:
            raise ValidationError({"preferred_duration": f"Invalid choices: {invalid_choices}"})
        
        # Validate 'availability'
        if not isinstance(self.availability, list):
            raise ValidationError({"availability": "Availability must be a list."})
        days_choices = [choice[0] for choice in self.DAYS_OF_WEEK_CHOICES]
        invalid_days = [day for day in self.availability if day not in days_choices]
        if invalid_days:
            raise ValidationError({"availability": f"Invalid choices: {invalid_days}"})
        
        # Validate fields_of_interest
        if not isinstance(self.fields_of_interest, list):
            raise ValidationError({"fields_of_interest": "Fields of interest must be a list."})
        valid_interests = [choice[0] for choice in self.FIELDS_OF_INTEREST_CHOICES]
        invalid_interests = [field for field in self.fields_of_interest if field not in valid_interests]
        if invalid_interests:
            raise ValidationError({"fields_of_interest": f"Invalid choices: {invalid_interests}"})
        if len(self.fields_of_interest) > 5:
            raise ValidationError({"fields_of_interest": "Fields of interest must be at most 5."})
        if not self.fields_of_interest:
            raise ValidationError({"fields_of_interest": "Fields of interest must not be empty."})
        
        # Validate skills
        if not isinstance(self.skills, list):
            raise ValidationError({"skills": "Skills must be a list."})
        valid_skills = [choice[0] for choice in self.SKILLS_CHOICES]
        invalid_skills = [skill for skill in self.skills if skill not in valid_skills]
        if invalid_skills:
            raise ValidationError({"skills": f"Invalid choices: {invalid_skills}"})
        if len(self.skills) > 10:
            raise ValidationError({"skills": "Skills must be at most 10."})
        if not self.skills:
            raise ValidationError({"skills": "Skills must not be empty."})

class Organization(models.Model):
    account = models.OneToOneField(Account, on_delete=models.CASCADE, primary_key=True)
    organization_name = models.CharField(max_length=100, unique=True)
    organization_description = models.CharField(max_length=500)
    organization_address = models.JSONField(default=dict)
    organization_website=models.URLField(blank=True, null=True)
    organization_profile_img = models.ImageField(blank=True, null=True)
    followers = models.IntegerField(default=0)

    def clean(self):
        if self.followers < 0:
            raise ValidationError("Followers cannot be negative.")
            

class Following(models.Model):
    follower = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='account_following')
    followed_volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE, related_name='volunteer_followee', null=True, blank=True)
    followed_organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='organization_followee', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Ensure that a follower can only follow a volunteer once
            models.UniqueConstraint(
                fields=['follower', 'followed_volunteer'],
                name='unique_follower_volunteer'
            ),

            # Ensure that a follower can only follow an organization once
            models.UniqueConstraint(
                fields=['follower', 'followed_organization'],
                name='unique_follower_organization'
            ),

            # Ensure that either followed_volunteer or followed_organization is set, but not both.
            models.CheckConstraint(
                check=(
                    models.Q(followed_volunteer__isnull=False, followed_organization__isnull=True) |
                    models.Q(followed_volunteer__isnull=True, followed_organization__isnull=False)
                ),
                name='followed_volunteer_or_organization'
            ),
            # Ensure that a follower cannot follow themselves
            models.CheckConstraint(
                check=~models.Q(follower=models.F('followed_volunteer')),
                name='prevent_self_following'
            ),
        ]

    def save(self, *args, **kwargs):
        # Enforce that organizations cannot follow anyone
        if self.follower.is_organization():
            raise ValidationError("Organizations cannot follow anyone.")
        
        super().save(*args, **kwargs)

class Membership(models.Model):
    ROLE_TYPES = (
        ('admin', 'Admin'),
        ('opportunity leader', 'Opportunity Leader'),
        ('member', 'Member'),
    )

    membership_id = models.AutoField(primary_key=True)
    volunteer = models.ForeignKey(Volunteer, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_TYPES, default='member')

    class Meta:
        constraints = [
            # Ensure a volunteer can only belong to an organization once
            models.UniqueConstraint(
                fields=['volunteer', 'organization'],
                name='unique_volunteer_per_organization'
            ),
            # Ensure that an organization can only have one admin
            models.UniqueConstraint(
                fields=['organization', 'role'],
                condition=models.Q(role='admin'),
                name='unique_admin_per_organization'
            ),
            # Ensure that role is one of the valid choices
            models.CheckConstraint(
                check=models.Q(role__in=['admin', 'opportunity leader', 'member']),
                name='valid_role_check'
            )
        ]
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)