from django.db import migrations, models


def backfill_flames_course_display_order(apps, schema_editor):
    FlamesCourse = apps.get_model('home', 'FlamesCourse')

    edition_ids = (
        FlamesCourse.objects.order_by()
        .values_list('edition_id', flat=True)
        .distinct()
    )

    for edition_id in edition_ids:
        courses = list(
            FlamesCourse.objects.filter(edition_id=edition_id)
            .order_by('title', 'id')
        )
        for index, course in enumerate(courses, start=1):
            course.display_order = index
        FlamesCourse.objects.bulk_update(courses, ['display_order'])


def reset_flames_course_display_order(apps, schema_editor):
    FlamesCourse = apps.get_model('home', 'FlamesCourse')
    FlamesCourse.objects.all().update(display_order=0)


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_drop_rogue_instructor_column'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='flamescourse',
            options={
                'ordering': ['edition', 'display_order', 'id'],
                'verbose_name': 'Flames Course',
                'verbose_name_plural': 'Flames Courses',
            },
        ),
        migrations.AddField(
            model_name='flamescourse',
            name='display_order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(
            backfill_flames_course_display_order,
            reset_flames_course_display_order,
        ),
    ]
