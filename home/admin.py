from django.contrib import admin
from .models import Article, Comment, FlamesCourse, FlamesCourseTestimonial, FlamesRegistration, Alumni, ReferralCode, FlamesTeam, FlamesTeamMember

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
    list_display = ('title', 'instructor', 'is_active', 'created_at')
    list_filter = ('is_active', 'instructor')
    search_fields = ('title', 'subtitle', 'description')
    prepopulated_fields = {'slug': ('title',)}

class FlamesCourseTestimonialAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'course', 'rating')
    list_filter = ('course', 'rating')

class FlamesRegistrationAdmin(admin.ModelAdmin):
    list_display = ('course', 'created_at', 'registration_mode', 'referral_code', 'original_price', 'discounted_price')
    list_filter = ('course', 'year', 'created_at', 'registration_mode', 'status')
    search_fields = ('college',)

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
    list_display = ('team',)
    list_filter = ('team',)
    search_fields = ('team__name', 'student__username')

admin.site.register(FlamesCourse, FlamesCourseAdmin)
admin.site.register(FlamesCourseTestimonial, FlamesCourseTestimonialAdmin)
admin.site.register(FlamesRegistration, FlamesRegistrationAdmin)
admin.site.register(Alumni, AlumniAdmin)
admin.site.register(ReferralCode, ReferralCodeAdmin)
admin.site.register(FlamesTeam, FlamesTeamAdmin)
admin.site.register(FlamesTeamMember, FlamesTeamMemberAdmin)

