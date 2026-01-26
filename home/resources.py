from import_export import resources, fields
from import_export.widgets import JSONWidget, BooleanWidget
from .flareModel import FlareRegistration


class FlareRegistrationResource(resources.ModelResource):
    courses_interested = fields.Field(
        column_name='courses_interested',
        attribute='courses_interested',
        widget=JSONWidget()
    )

    career_goals = fields.Field(
        column_name='career_goals',
        attribute='career_goals',
        widget=JSONWidget()
    )

    commitment = fields.Field(
        column_name='commitment',
        attribute='commitment',
        widget=BooleanWidget()
    )

    class Meta:
        model = FlareRegistration
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

        fields = (
            'id',
            'full_name',
            'email',
            'phone_number',
            'occupation_status',
            'current_year',
            'courses_interested',
            'career_goals',
            'motivation',
            'commitment',
            'created_at',
        )

        export_order = fields

    def dehydrate_courses_interested(self, obj):
        return ", ".join(obj.get_courses_list())

    def dehydrate_career_goals(self, obj):
        return ", ".join(obj.get_career_goals_list())
