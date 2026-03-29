from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_drop_old_mti_tables'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_submission',
            field=models.BooleanField(default=False),
        ),
    ]
