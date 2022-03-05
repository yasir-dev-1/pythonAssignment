from django.http import HttpRequest
from django.utils.translation import ugettext_lazy as _
from allauth.account import app_settings as allauth_settings
from allauth.account.forms import ResetPasswordForm
from allauth.utils import email_address_exists
from django.contrib.auth.hashers import make_password
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from rest_framework import serializers
from home.models import *





class SignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyUser
        fields = ('id',  'first_name', 'last_name', 'username', 'email', 'password')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'style': {
                    'input_type': 'password'
                }
            },
            'email': {
                'required': True,
                'allow_blank': False,
            },
            'username': {
                'required': True,
                'allow_blank': False,
            }
        }

    def _get_request(self):
        request = self.context.get('request')
        if request and not isinstance(request, HttpRequest) and hasattr(request, '_request'):
            request = request._request
        return request

    def validate_email(self, email):
        email = get_adapter().clean_email(email)
        if allauth_settings.UNIQUE_EMAIL:
            if email and email_address_exists(email):
                raise serializers.ValidationError(
                    _("A user is already registered with this e-mail address."))
        return email

    def create(self, validated_data):
        user = MyUser(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=make_password(validated_data.get('password'))
        )
        user.save()
        request = self._get_request()
        setup_user_email(request, user, [])
        return user

    def save(self, request=None):
        """rest_auth passes request so we must override to accept it"""
        return super().save()

class PostSerializer(serializers.ModelSerializer):
    # Post Model Serializer for CRUD operations
    class Meta:
        model = Post
        fields = ['id', 'author', 'body', 'active', 'created_at', 'updated_at']

class LikeSerializer(serializers.ModelSerializer):
    # Post Model Serializer for CRUD operations
    class Meta:
        model = Like
        fields = ['id', 'user', 'post', 'value']
