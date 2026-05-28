from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0008_demandecandidature_image_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="electeur",
            name="notification_ouverture_envoyee",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
