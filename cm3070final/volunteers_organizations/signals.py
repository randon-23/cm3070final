from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from volunteers_organizations.models import Following

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