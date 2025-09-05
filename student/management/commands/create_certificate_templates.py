from django.core.management.base import BaseCommand
from django.template.loader import get_template
from student.event_models import CertificateTemplate
import os


class Command(BaseCommand):
    help = 'Create certificate templates from HTML files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--template-file',
            type=str,
            help='Path to the HTML template file',
        )
        parser.add_argument(
            '--template-name',
            type=str,
            help='Name for the certificate template',
        )

    def handle(self, *args, **options):
        # Create default templates if no specific file is provided
        if not options['template_file']:
            self.create_default_templates()
        else:
            self.create_template_from_file(
                options['template_file'],
                options['template_name']
            )

    def create_default_templates(self):
        """Create default certificate templates"""
        
        # Default/General template
        default_template_content = self.get_template_content('certificate_base_template.html')
        if default_template_content:
            template, created = CertificateTemplate.objects.get_or_create(
                name="Default Certificate Template",
                defaults={'html_template': default_template_content}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Created default certificate template')
                )
            else:
                self.stdout.write('Default template already exists')

        # GTBIT Workshop template
        gtbit_template_content = self.get_template_content('gtbit_workshop_template.html')
        if gtbit_template_content:
            template, created = CertificateTemplate.objects.get_or_create(
                name="GTBIT Workshop Template",
                defaults={'html_template': gtbit_template_content}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Created GTBIT workshop certificate template')
                )
            else:
                self.stdout.write('GTBIT workshop template already exists')

    def create_template_from_file(self, file_path, template_name):
        """Create a template from a specific file"""
        if not template_name:
            self.stdout.write(
                self.style.ERROR('Template name is required when using --template-file')
            )
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
            template, created = CertificateTemplate.objects.get_or_create(
                name=template_name,
                defaults={'html_template': content}
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created template: {template_name}')
                )
            else:
                # Update existing template
                template.html_template = content
                template.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated template: {template_name}')
                )
                
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File not found: {file_path}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating template: {str(e)}')
            )

    def get_template_content(self, template_name):
        """Get template content from the templates directory"""
        try:
            template_path = f'student/flames/{template_name}'
            template = get_template(template_path)
            # Read the raw content instead of rendering
            with open(template.origin.name, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not load template {template_name}: {str(e)}')
            )
            return None
