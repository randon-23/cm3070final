from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from phonenumber_field.modelfields import PhoneNumberField
import uuid

class AccountManager(BaseUserManager):
    use_in_migrations = True

    # https://simpleisbetterthancomplex.com/tutorial/2016/07/22/how-to-extend-django-user-model.html
    def _create_user(self, email_address, password, **extra_fields):
        if not email_address:
            raise ValueError("The Email Address must be set")
        email_address = self.normalize_email(email_address)
        user = self.model(email_address=email_address, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email_address, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email_address, password, **extra_fields)

    def create_superuser(self, email_address, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email_address, password, **extra_fields)

class Account(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('volunteer', 'Volunteer'),
        ('organization', 'Organization'),
    )

    account_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email_address = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    contact_number = models.CharField(max_length=15, unique=True)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    #Removing username field
    username = None

    USERNAME_FIELD = 'email_address'
    REQUIRED_FIELDS = ['user_type']

    objects = AccountManager() # Using custom manager

    def is_volunteer(self):
        return self.user_type == 'volunteer'
    
    def is_organization(self):
        return self.user_type == 'organization'
    
    def is_admin(self):
        return self.user_type == 'admin'
    
    def save(self, *args, **kwargs):
        # Call the original save method
        super(Account, self).save(*args, **kwargs)

        Group.objects.get_or_create(name='Volunteer')
        Group.objects.get_or_create(name='Organization')
        Group.objects.get_or_create(name='Admin')

        # Add the user to the appropriate group based on their user_type
        if self.user_type == 'volunteer':
            volunteers = Group.objects.get(name='Volunteer')
            self.groups.add(volunteers)
        elif self.user_type == 'organization':
            organizations = Group.objects.get(name='Organization')
            self.groups.add(organizations)
        elif self.user_type == 'admin':
            admins = Group.objects.get(name='Admin')
            self.groups.add(admins)

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = (
        ('new_follower', 'New Follower'),
        ('new_endorsement', 'New Endorsement'),
        ('new_status_post', 'New Status Post'),
        ('application_submitted', 'Application Submitted'),
        ('application_accepted', 'Application Accepted'),
        ('application_rejected', 'Application Rejected'),
        ('log_request_submitted', 'New Log Request'),
        ('opportunity_completed', 'Opportunity Completed'),
        ('opportunity_cancelled', 'Opportunity Cancelled'),
        ('new_opportunity_session', 'New Opportunity Session'),
        ('new_message', 'New Message'),
        ('other', 'Other'), 
    )

    notification_id = models.AutoField(primary_key=True)
    recipient = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='notifications')
    # sender in case of message notification
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    notification_message = models.TextField(max_length=500)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def clean(self):
        if self.notification_type not in [choice[0] for choice in self.NOTIFICATION_TYPE_CHOICES]:
            raise ValidationError("Invalid notification type.")

    def __str__(self):
        return f"{self.recipient.email_address} - {self.notification_type} - {self.created_at}"