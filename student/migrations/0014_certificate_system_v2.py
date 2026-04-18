# student/migrations/0014_certificate_system_v2.py
#
# DEFINITIVE version — written after auditing the exact DB state.
#
# Already in DB (state-only sync needed):
#   student_certificatetemplate: body_text, certificate_type, hours,
#     html_layout, org_logo, org_name, show_batch, show_hours, show_qr,
#     slug (unique), updated_at       ← ALL PRESENT
#   student_certificate: template_snapshot, approved (db_index)
#   student_coursesheet_coding_questions (M2M table)
#   student_coursesheet_mcq_questions   (M2M table)
#   student_cer_student_dbb91a_idx      ← NOT yet created
#   html_template                       ← already REMOVED
#
# NEW tables to create:
#   student_signatory                   ← dropped, now recreate
#   student_templatesignatory           ← dropped, now recreate
#   student_certificatetemplate_signatories (M2M through table)

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('practice', '0013_alter_streak_current_streak_default'),
        ('student', '0013_coursesheet_coding_questions_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [

        # ═══════════════════════════════════════════════════════════════════
        # SECTION A — State-only sync for columns already in DB
        # ═══════════════════════════════════════════════════════════════════

        # A1. html_template removed
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.RemoveField(model_name='certificatetemplate', name='html_template'),
            ],
        ),

        # A2. AlterModelOptions
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterModelOptions(
                    name='certificatetemplate',
                    options={
                        'ordering': ['-created_at'],
                        'verbose_name': 'Certificate Template',
                        'verbose_name_plural': 'Certificate Templates',
                    },
                ),
            ],
        ),

        # A3. certificate.template_snapshot
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='certificate',
                    name='template_snapshot',
                    field=models.JSONField(blank=True, null=True,
                                          help_text='Frozen template state at PDF generation time.'),
                ),
            ],
        ),

        # A4. certificatetemplate — all new fields (already in DB)
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='certificatetemplate', name='body_text',
                    field=models.TextField(
                        default='This is to certify that {student_name} has successfully completed {event_name}.',
                        help_text='Certificate body. Supports {student_name}, {event_name}, {issued_date}, {hours}, {batch_name}.',
                    ),
                    preserve_default=False,
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='certificate_type',
                    field=models.CharField(
                        choices=[('completion','Certificate of Completion'),('excellence','Certificate of Excellence'),
                                 ('participation','Certificate of Participation'),('achievement','Certificate of Achievement')],
                        default='completion', max_length=20,
                    ),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='hours',
                    field=models.PositiveIntegerField(default=0, help_text='Training hours'),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='html_layout',
                    field=models.CharField(
                        choices=[('angaar_dark','Angaar Dark (Fire Theme)'),
                                 ('angaar_light','Angaar Light (Clean)'),('custom','Custom HTML Template')],
                        default='angaar_dark', max_length=20,
                    ),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='org_logo',
                    field=models.ImageField(blank=True, null=True, upload_to='certificates/logos/'),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='org_name',
                    field=models.CharField(default='The Angaar Batch', max_length=255),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='show_batch',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='show_hours',
                    field=models.BooleanField(default=False),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='show_qr',
                    field=models.BooleanField(default=True),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='slug',
                    field=models.SlugField(blank=True, editable=False, unique=True),
                ),
                migrations.AddField(
                    model_name='certificatetemplate', name='updated_at',
                    field=models.DateTimeField(auto_now=True),
                ),
            ],
        ),

        # A5. coursesheet M2M tables (already exist)
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name='coursesheet', name='coding_questions',
                    field=models.ManyToManyField(blank=True, related_name='course_sheets', to='practice.question'),
                ),
                migrations.AddField(
                    model_name='coursesheet', name='mcq_questions',
                    field=models.ManyToManyField(blank=True, related_name='course_sheets', to='practice.mcqquestion'),
                ),
            ],
        ),

        # A6. certificate.approved db_index
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='certificate', name='approved',
                    field=models.BooleanField(db_index=True, default=False),
                ),
            ],
        ),

        # A7. Event FK help_text + related_name updates
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterField(
                    model_name='event', name='certificate_template',
                    field=models.ForeignKey(
                        blank=True, null=True,
                        help_text='Template used for certificates. If blank, default Angaar Dark is used.',
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name='events', to='student.certificatetemplate',
                    ),
                ),
                migrations.AlterField(
                    model_name='event', name='code',
                    field=models.CharField(
                        help_text="Short code used in certificate IDs (e.g. 'FLAMES25MERN')",
                        max_length=20, unique=True,
                    ),
                ),
                migrations.AlterField(
                    model_name='event', name='end_date',
                    field=models.DateField(),
                ),
                migrations.AlterField(
                    model_name='event', name='start_date',
                    field=models.DateField(),
                ),
            ],
        ),

        # ═══════════════════════════════════════════════════════════════════
        # SECTION B — Real DB operations (tables/index not yet created)
        # ═══════════════════════════════════════════════════════════════════

        # B1. Create Signatory table
        migrations.CreateModel(
            name='Signatory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('designation', models.CharField(help_text='e.g. Founder, Director', max_length=255)),
                ('organization', models.CharField(help_text='e.g. The Angaar Batch', max_length=255)),
                ('signature_image', models.ImageField(blank=True, null=True, upload_to='certificates/signatures/')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Signatory',
                'verbose_name_plural': 'Signatories',
                'ordering': ['name'],
            },
        ),

        # B2. Create TemplateSignatory table (through model — no FKs yet)
        migrations.CreateModel(
            name='TemplateSignatory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveSmallIntegerField(default=0)),
            ],
            options={
                'verbose_name': 'Template Signatory',
                'verbose_name_plural': 'Template Signatories',
                'ordering': ['order'],
            },
        ),

        # B3. Add composite index on certificate (student, approved)
        migrations.AddIndex(
            model_name='certificate',
            index=models.Index(fields=['student', 'approved'], name='student_cer_student_dbb91a_idx'),
        ),

        # B4. Add FK fields to TemplateSignatory
        migrations.AddField(
            model_name='templatesignatory', name='signatory',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.signatory'),
        ),
        migrations.AddField(
            model_name='templatesignatory', name='template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='student.certificatetemplate'),
        ),

        # B5. Add signatories M2M field on CertificateTemplate
        migrations.AddField(
            model_name='certificatetemplate', name='signatories',
            field=models.ManyToManyField(
                blank=True, related_name='templates',
                through='student.TemplateSignatory',
                through_fields=('template', 'signatory'),
                to='student.signatory',
            ),
        ),

        # B6. Unique together constraint on TemplateSignatory
        migrations.AlterUniqueTogether(
            name='templatesignatory',
            unique_together={('template', 'signatory')},
        ),
    ]
