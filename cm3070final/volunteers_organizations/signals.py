from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from accounts_notifs.tasks import send_notification
from .models import Endorsement, Following, StatusPost, Organization
from accounts_notifs.tasks import send_notification
from django.db import models

@receiver(post_save, sender=Following)
def increment_follow_count(sender, instance, created, **kwargs):
    if created:
        if instance.followed_volunteer:
            instance.followed_volunteer.followers += 1
            instance.followed_volunteer.save()
        elif instance.followed_organization:
            instance.followed_organization.followers += 1
            instance.followed_organization.save()

@receiver(post_delete, sender=Following)
def decrement_follow_count(sender, instance, **kwargs):
    if instance.followed_volunteer:
        instance.followed_volunteer.followers -= 1
        instance.followed_volunteer.save()
    elif instance.followed_organization:
        instance.followed_organization.followers -= 1
        instance.followed_organization.save()

@receiver(post_save, sender=Following)
def notify_new_follower(sender, instance, created, **kwargs):
    if created:
        followed_user = instance.followed_volunteer.account if instance.followed_volunteer else instance.followed_organization.account
        follower_user = instance.follower

        # Get follower's name
        if follower_user.is_volunteer():
            follower_name = f"{follower_user.volunteer.first_name} {follower_user.volunteer.last_name}"
        else:
            follower_name = follower_user.organization.organization_name

        send_notification.delay(
            recipient_id=str(followed_user.account_uuid),
            notification_type="new_follower",
            message=f"{follower_name} started following you."
        )

@receiver(post_save, sender=Endorsement)
def notify_new_endorsement(sender, instance, created, **kwargs):
    if created:
        recipient = instance.receiver
        giver = instance.giver
        if giver.is_volunteer():
            giver_name = f"{instance.giver.volunteer.first_name} {instance.giver.volunteer.last_name}"
        else:
            giver_name = instance.giver.organization.organization_name
        
        send_notification.delay(
            recipient_id=str(recipient.account_uuid),
            notification_type="new_endorsement",
            message=f"You have received a new endorsement from {giver_name}!"
        )

# Sends notifications to all followers of a user when they post a new status update.
@receiver(post_save, sender=StatusPost)
def notify_new_status_post(sender, instance, created, **kwargs):
    if created:  # Only trigger on new posts
        author = instance.author

        # Determine author's display name
        if author.is_volunteer():
            author_name = f"{author.volunteer.first_name} {author.volunteer.last_name}"
        else:
            author_name = author.organization.organization_name

        author_volunteer = getattr(author, "volunteer", None)
        author_organization = getattr(author, "organization", None)

        # Fetch followers dynamically based on author type
        followers = Following.objects.filter(
            models.Q(followed_volunteer=author_volunteer) |
            models.Q(followed_organization=author_organization)
        ).values_list("follower", flat=True)

        # Notification message
        message = f"{author_name} has posted a new status update!"

        # Send notifications
        for follower_id in followers:
            send_notification.delay(
                recipient_id=str(follower_id),
                notification_type="new_status_post",
                message=message
            )

# Notifies an organization when they receive a Volontera points donation.
@receiver(pre_save, sender=Organization)
def notify_organization_on_donation(sender, instance, **kwargs):
    if instance.pk:  # Ensure it's an update (not a new organization)
        try:
            previous_instance = Organization.objects.get(pk=instance.pk)
            points_received = instance.volontera_points - previous_instance.volontera_points
            
            if points_received > 0:  # Ensure donation happened
                send_notification.delay(
                    recipient_id=str(instance.account.account_uuid),
                    notification_type="new_volontera_points",
                    message=f"Your organization has received a donation of {points_received} Volontera points!"
                )
        except Organization.DoesNotExist:
            pass  # Organization didn't exist before, no notification needed