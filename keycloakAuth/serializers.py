from rest_framework import serializers
from .models import UserProfile


class TokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    refresh_token = serializers.CharField()
    refresh_expires_in = serializers.IntegerField()
    token_type = serializers.CharField()


class RefreshTokenSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    expires_in = serializers.IntegerField()
    refresh_token = serializers.CharField()
    refresh_expires_in = serializers.IntegerField()
    token_type = serializers.CharField()


class RefreshTokenRequestSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class UserInfoSerializer(serializers.Serializer):
    sub = serializers.CharField()  # ID of the user
    given_name = serializers.CharField()
    family_name = serializers.CharField()
    preferred_username = serializers.CharField()
    email = serializers.EmailField()
    profile_picture = serializers.SerializerMethodField()

    def get_profile_picture(self, obj):
        try:
            user_profile = UserProfile.objects.get(uuid=obj['sub'])
            if user_profile.profilePicture and hasattr(user_profile.profilePicture, 'url'):
                return user_profile.profilePicture.url
            else:
                return None
        except UserProfile.DoesNotExist:
            return None


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField(min_length=1)


class SimpleLoginSerializer(serializers.Serializer):
    "Simple login using username and pass"
    username_or_email = serializers.CharField()
    password = serializers.CharField()
    totp = serializers.CharField(
        required=False,
        help_text="time based one-time password"
        )


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ['uuid', 'profilePicture', 'createdDate', 'updatedDate']
        read_only_fields = ['uuid', 'createdDate', 'updatedDate']
