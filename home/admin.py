from django.contrib import admin
from .models import Article, Comment, FlamesCourse, FlamesCourseTestimonial, \
    FlamesRegistration, Alumni, ReferralCode, FlamesTeam, FlamesTeamMember, Session, FreeClassWhatsappGroupLink 

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'get_likes_count')
    search_fields = ('title', 'content', 'created_at')
    list_filter = ('title', 'created_at')
    ordering = ('created_at',)
    
    def get_likes_count(self, obj):
        return obj.total_likes()
    get_likes_count.short_description = 'Likes'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('article', 'user', 'content', 'created_at')
    search_fields = ('article__title', 'user__username', 'content')
    list_filter = ('created_at', 'article')
    ordering = ('-created_at',)

# ================== FLAMES ===================

class FlamesCourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title', 'subtitle', 'description')
    prepopulated_fields = {'slug': ('title',)}

class FlamesCourseTestimonialAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'course', 'rating')
    list_filter = ('course', 'rating')

class FlamesRegistrationAdmin(admin.ModelAdmin):
    list_display = ('user', 'course', 'created_at', 'get_payable_amount', 'status')
    list_filter = ('course', 'year', 'created_at', 'registration_mode', 'status')
    search_fields = ('user__username', 'user__email', 'team__name', "payment_id")
    
    def get_team_name(self, obj):
        if obj.registration_mode == 'TEAM' and obj.team:
            return obj.team.name
        return '-'
    get_team_name.short_description = 'Team Name'
    
    def get_payable_amount(self, obj):
        return f'₹{obj.payable_amount}'
    get_payable_amount.short_description = 'Payable Amount'

class AlumniAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'contact_number', 'college', 'batch_year')
    list_filter = ('batch_year', 'college')
    search_fields = ('name', 'email', 'college')

class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'referral_type', 'alumni', 'discount_amount', 'is_active', 'created_at', 'expires_at')
    list_filter = ('referral_type', 'is_active')
    search_fields = ('code', 'alumni__name')
    actions = ['generate_alumni_codes', 'generate_team_codes']
    
    def generate_alumni_codes(self, request, queryset):
        """Admin action to generate referral codes for all alumni who don't have one"""
        from home.models import Alumni, ReferralCode
        
        alumni_without_codes = Alumni.objects.exclude(
            id__in=ReferralCode.objects.filter(referral_type='ALUMNI').values_list('alumni_id', flat=True)
        )
        
        count = 0
        for alumni in alumni_without_codes:
            code = ReferralCode.generate_unique_code(prefix='ALM')
            ReferralCode.objects.create(
                code=code,
                referral_type='ALUMNI',
                alumni=alumni,
                discount_amount=500.00,
                is_active=True
            )
            count += 1
        
        self.message_user(request, f"Successfully generated {count} alumni referral codes.")
    
    generate_alumni_codes.short_description = "Generate referral codes for alumni without codes"
    
    def generate_team_codes(self, request, queryset):
        """Admin action to generate team referral codes"""
        from home.models import ReferralCode
        
        count = int(request.POST.get('count', 5))  # Default to 5 codes
        
        for _ in range(count):
            code = ReferralCode.generate_unique_code(prefix='TEAM')
            ReferralCode.objects.create(
                code=code,
                referral_type='TEAM',
                discount_amount=500.00,
                is_active=True
            )
        
        self.message_user(request, f"Successfully generated {count} team referral codes.")
    
    generate_team_codes.short_description = "Generate team referral codes"

class FlamesTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'team_leader', 'course')
    list_filter = ('course',)
    search_fields = ('name', 'team_leader__username')
    
    
class FlamesTeamMemberAdmin(admin.ModelAdmin):
    list_display = ('team', 'member')
    list_filter = ('team',)
    search_fields = ('team__name', 'student__username')

admin.site.register(FlamesCourse, FlamesCourseAdmin)
admin.site.register(FlamesCourseTestimonial, FlamesCourseTestimonialAdmin)
admin.site.register(FlamesRegistration, FlamesRegistrationAdmin)
admin.site.register(Alumni, AlumniAdmin)
admin.site.register(ReferralCode, ReferralCodeAdmin)
admin.site.register(FlamesTeam, FlamesTeamAdmin)
admin.site.register(FlamesTeamMember, FlamesTeamMemberAdmin)
admin.site.register(Session)


# ================== WHATSAPP GROUP ===================

@admin.register(FreeClassWhatsappGroupLink)
class FreeClassWhatsappGroupLinkAdmin(admin.ModelAdmin):
    list_display = ("course_code", "whatsapp_link", "is_active")
    list_editable = ("whatsapp_link", "is_active")


# ================== FLARE REGISTRATION ===================
from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from .flareModel import FlareRegistration
from .resources import FlareRegistrationResource


@admin.register(FlareRegistration)
class FlareRegistrationAdmin(ImportExportModelAdmin):
    resource_class = FlareRegistrationResource

    list_display = (
        'full_name',
        'email',
        'phone_number',
        'occupation_status',
        'get_courses',
        'commitment',
        'created_at'
    )

    list_filter = (
        'occupation_status',
        'commitment',
        'created_at'
    )

    search_fields = (
        'full_name',
        'email',
        'phone_number'
    )

    readonly_fields = (
        'created_at',
        'updated_at',
        'get_courses_display',
        'get_goals_display'
    )

    ordering = ('-created_at',)

    fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'full_name', 'phone_number')
        }),
        ('Academic / Professional Details', {
            'fields': ('occupation_status', 'current_year')
        }),
        ('Course Interest', {
            'fields': ('get_courses_display', 'courses_interested')
        }),
        ('Career Goals', {
            'fields': ('get_goals_display', 'career_goals')
        }),
        ('Motivation & Commitment', {
            'fields': ('motivation', 'commitment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    # --------------------------
    # Display Helpers
    # --------------------------

    def get_courses(self, obj):
        courses = obj.get_courses_list()
        return ", ".join(courses) if courses else "-"
    get_courses.short_description = "Courses"

    def get_courses_display(self, obj):
        courses = obj.get_courses_list()
        if courses:
            return "\n".join([f"• {course}" for course in courses])
        return "No courses selected"
    get_courses_display.short_description = "Selected Courses"

    def get_goals_display(self, obj):
        goals = obj.get_career_goals_list()
        if goals:
            return "\n".join([f"• {goal}" for goal in goals])
        return "No career goals selected"
    get_goals_display.short_description = "Career Goals"
