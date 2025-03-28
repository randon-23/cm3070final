# Generated by Django 5.1.4 on 2025-03-14 10:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts_notifs', '0010_remove_accountpreferences_enable_volontera_point_opportunities_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(choices=[('new_follower', 'New Follower'), ('new_endorsement', 'New Endorsement'), ('new_status_post', 'New Status Post'), ('application_submitted', 'Application Submitted'), ('application_accepted', 'Application Accepted'), ('application_rejected', 'Application Rejected'), ('log_request_submitted', 'New Log Request'), ('opportunity_completed', 'Opportunity Completed'), ('opportunity_cancelled', 'Opportunity Cancelled'), ('new_opportunity_session', 'New Opportunity Session'), ('new_message', 'New Message'), ('other', 'Other')], max_length=50),
        ),
    ]
