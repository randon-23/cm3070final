from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts_notifs.tasks import send_notification
from .models import VolunteerOpportunityApplication, VolunteerEngagementLog, VolunteerEngagement, VolunteerOpportunitySession, VolunteerOpportunity, VolunteerSessionEngagement
from volunteers_organizations.models import VolunteerMatchingPreferences
from django.core.mail import send_mail
from django.conf import settings
from geopy.distance import geodesic

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

# SMART MATCHING ALGORITHM - Triggered when a new VolunteerOpportunity is created. Matches it against volunteers' preferences and sends notifications & emails.
@receiver(post_save, sender=VolunteerOpportunity)
def match_volunteers_to_opportunity(sender, instance, created, **kwargs):
    if not created:
        return

    matched_volunteers = []

    volunteers = VolunteerMatchingPreferences.objects.select_related("volunteer__account").all()

    for preference in volunteers:
        match_score = 0
        max_score = 100  # Total weight sum

        log_details = {
            "volunteer": f"{preference.volunteer.first_name} {preference.volunteer.last_name}",
            "opportunity": instance.title,
            "components": {}
        }

        # Location Matching (25%)**  
        if "lat" in preference.location and "lon" in preference.location:
            if "lat" in instance.required_location and "lon" in instance.required_location:
                volunteer_distance = geodesic(
                    (preference.location["lat"], preference.location["lon"]),
                    (instance.required_location["lat"], instance.required_location["lon"])
                ).km
                if volunteer_distance <= 100:
                    match_score += 25
                    log_details["components"]["location"] = 25
                else:
                    log_details["components"]["location"] = 0

        # Skills Matching (20%)**  
        if preference.skills:
            if any(skill in instance.requirements for skill in preference.skills):
                match_score += 20
                log_details["components"]["skills"] = 20
            else:
                log_details["components"]["skills"] = 0

        # Fields of Interest (20%)**  
        if preference.fields_of_interest:
            if instance.area_of_work in preference.fields_of_interest:
                match_score += 20
                log_details["components"]["fields_of_interest"] = 20
            else:
                log_details["components"]["fields_of_interest"] = 0

        # Duration Matching (10%)**  
        if preference.preferred_duration:
            if instance.duration in preference.preferred_duration:
                match_score += 10
                log_details["components"]["duration"] = 10
            else:
                log_details["components"]["duration"] = 0

        # Availability Matching (10%)**  
        if preference.availability and instance.days_of_week:
            if any(day in preference.availability for day in instance.days_of_week):
                match_score += 10
                log_details["components"]["availability"] = 10
            else:
                log_details["components"]["availability"] = 0

        # Work Type Matching (10%)**  
        if instance.work_basis == preference.preferred_work_types or preference.preferred_work_types == "both":
            match_score += 10
            log_details["components"]["work_type"] = 10
        else:
            log_details["components"]["work_type"] = 0

        # Languages Matching (5%)**  
        if instance.languages:
            if any(lang in instance.languages for lang in preference.languages):
                match_score += 5
                log_details["components"]["languages"] = 5
            else:
                log_details["components"]["languages"] = 0

        # Calculate Final Match Percentage  
        match_percentage = (match_score / max_score) * 100
        log_details["final_match"] = match_percentage

        if match_percentage >= 65:
            matched_volunteers.append((preference.volunteer.account, match_percentage, volunteer_distance))

    # Send Notifications & Emails to Matched Volunteers
    for volunteer, match_percentage, distance in matched_volunteers:
        distance_text = f" ({round(distance, 2)} km away)" if distance is not None else ""
        message = f"You are a {int(match_percentage)}% match for '{instance.title}'{distance_text} by {instance.organization.organization_name}. Check it out!"
        
        # Send Notification
        send_notification.delay(
            recipient_id=str(volunteer.account_uuid),
            notification_type="opportunity_match",
            message=message
        )

        # Send Email - not sure if working
        email_subject = f"You're a great match ({int(match_percentage)}%) for a new opportunity!"
        email_body = (
            f"Hi {volunteer.volunteer.first_name} {volunteer.volunteer.last_name},\n\n"
            "We found a new volunteering opportunity that matches your interests!\n\n"
            f"[View Opportunity & Apply](https://volontera.com/opportunity/{instance.volunteer_opportunity_id})\n\n"
            "Happy Volunteering!"
        )
        send_mail(
            email_subject,
            email_body,
            settings.EMAIL_HOST_USER,
            [volunteer.email_address],
            fail_silently=False,
        )

# Adds Volontera points to a volunteer when their engagement log is approved and/or an engagement log is created for them
@receiver(post_save, sender=VolunteerEngagementLog)
def add_volontera_points(sender, instance, created, **kwargs):
    if instance.status == "approved":  # Ensure log is approved
        volunteer = instance.volunteer_engagement.volunteer
        hours_logged = instance.no_of_hours  # Correct field reference
        points_earned = hours_logged
        
        # Update volunteer points
        volunteer.volontera_points += points_earned
        volunteer.save()

        # Send notification
        send_notification.delay(
            recipient_id=str(volunteer.account.account_uuid),
            notification_type="new_volontera_points",
            message=f"You have earned {points_earned} Volontera points for your volunteer engagement!"
        )