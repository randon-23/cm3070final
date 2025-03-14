from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from accounts_notifs.tasks import send_notification
from .models import VolunteerOpportunityApplication, VolunteerEngagementLog, VolunteerEngagement, VolunteerOpportunitySession, VolunteerOpportunity, VolunteerSessionEngagement

@receiver(post_save, sender=VolunteerOpportunityApplication)
def notify_application_submitted(sender, instance, created, **kwargs):
    if created:
        opportunity = instance.volunteer_opportunity
        organization = opportunity.organization  # Organization that owns the opportunity
        volunteer = instance.volunteer.account  # The volunteer who applied

        message = f"{volunteer.volunteer.first_name} {volunteer.volunteer.last_name} has applied to {opportunity.title}."
        
        send_notification.delay(
            recipient_id=str(organization.account.account_uuid),
            notification_type="application_submitted",
            message=message
        )

# Notify volunteer when their application is accepted
@receiver(post_save, sender=VolunteerOpportunityApplication)
def notify_application_accepted(sender, instance, **kwargs):
    if instance.application_status == "accepted":
        volunteer = instance.volunteer.account  # Get the volunteer's account

        # Build notification message
        opportunity_title = instance.volunteer_opportunity.title
        message = f"Your application for '{opportunity_title}' has been accepted!"

        # Send notification
        send_notification.delay(
            recipient_id=str(volunteer.account_uuid),
            notification_type="application_accepted",
            message=message
        )


# Notify volunteer when their application is rejected
@receiver(post_save, sender=VolunteerOpportunityApplication)
def notify_application_rejected(sender, instance, **kwargs):
    if instance.application_status == "rejected":
        volunteer = instance.volunteer.account  # Get the volunteer's account

        # Build notification message
        opportunity_title = instance.volunteer_opportunity.title
        message = f"Unfortunately, your application for '{opportunity_title}' was rejected."

        # Send notification
        send_notification.delay(
            recipient_id=str(volunteer.account_uuid),
            notification_type="application_rejected",
            message=message
        )

# Sends a notification to the organization when a volunteer submits a log request.
@receiver(post_save, sender=VolunteerEngagementLog)
def notify_new_log_request(sender, instance, created, **kwargs):
    if created and instance.is_volunteer_request:  # Ensure it's a new log request from a volunteer
        opportunity = instance.volunteer_engagement.volunteer_opportunity_application.volunteer_opportunity
        organization_account = opportunity.organization.account  # Get the organization owner
        
        volunteer = instance.volunteer_engagement.volunteer
        volunteer_name = f"{volunteer.first_name} {volunteer.last_name}"
        message = f"{volunteer_name} has submitted a new engagement log request for {opportunity.title}."

        send_notification.delay(
            recipient_id=str(organization_account.account_uuid),
            notification_type="log_request_submitted",
            message=message
        )

# Opportunity Cancelled or completed - Notify engaged volunteers
@receiver(post_save, sender=VolunteerOpportunity)
def notify_opportunity_status_change(sender, instance, **kwargs):
    if instance.status in ["cancelled", "completed"]:
        # Get engaged volunteers
        engaged_volunteers = VolunteerEngagement.objects.filter(
            volunteer_opportunity_application__volunteer_opportunity=instance
        ).values_list("volunteer__account__account_uuid", flat=True)

        # Set notification type & message
        notification_type = "opportunity_cancelled" if instance.status == "cancelled" else "opportunity_completed"
        message = (
            f"The opportunity {instance.title} has been cancelled."
            if instance.status == "cancelled"
            else f"The opportunity {instance.title} has been successfully completed!"
        )

        # Send notifications
        for volunteer_id in engaged_volunteers:
            send_notification.delay(
                recipient_id=str(volunteer_id),
                notification_type=notification_type,
                message=message
            )

# New Session Created - Notify engaged volunteers
@receiver(post_save, sender=VolunteerOpportunitySession)
def notify_new_session_created(sender, instance, created, **kwargs):
    if created:  # Ensure it's only triggered on creation, not updates
        opportunity = instance.opportunity

        # Get engaged volunteers
        engaged_volunteers = VolunteerEngagement.objects.filter(
            volunteer_opportunity_application__volunteer_opportunity=opportunity
        ).values_list("volunteer__account__account_uuid", flat=True)

        # Notification message
        message = f"A new session for {opportunity.title} has been scheduled. Check it out!"

        # Send notifications
        for volunteer_id in engaged_volunteers:
            send_notification.delay(
                recipient_id=str(volunteer_id),
                notification_type="new_opportunity_session",
                message=message
            )

# Session Cancelled or completed - Notify attendees
@receiver(post_save, sender=VolunteerOpportunitySession)
def notify_session_status_change(sender, instance, **kwargs):
    if instance.status in ["cancelled", "completed"]:
        # Get only the volunteers who marked themselves as `can_go`
        attendees = VolunteerSessionEngagement.objects.filter(
            session=instance, status="can_go"
        ).values_list("volunteer_engagement__volunteer__account__account_uuid", flat=True)

        # Define message based on status
        notification_type = "session_cancelled" if instance.status == "cancelled" else "session_completed"
        message = (
            f"The session {instance.title} has been cancelled."
            if instance.status == "cancelled"
            else f"The session {instance.title} has been completed!"
        )

        # Send notifications to `can_go` attendees
        for volunteer_id in attendees:
            send_notification.delay(
                recipient_id=str(volunteer_id),
                notification_type=notification_type,
                message=message
            )