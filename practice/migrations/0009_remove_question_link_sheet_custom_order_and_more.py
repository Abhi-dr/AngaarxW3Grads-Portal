# Generated by Django 5.0.6 on 2024-12-15 18:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('practice', '0008_remove_question_link_question_parent_id_and_more'),
    ]

    operations = [


        migrations.AddIndex(
            model_name='question',
            index=models.Index(fields=['position'], name='practice_qu_positio_cd3979_idx'),
        ),
        migrations.AddIndex(
            model_name='testcase',
            index=models.Index(fields=['question'], name='practice_te_questio_ff3285_idx'),
        ),
    ]