from rest_framework import serializers
from accounts.models import CustomUser
from student.models import Notification

class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'first_name', 'last_name', 'email', 'mobile_number', 'college', 'dob', 'coins', 'profile_pic', 'github_id', 'linkedin_id', 'role']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'title', 'description', 'type', 'is_fixed', 'is_alert', 'expiration_date', 'timeStamp']
