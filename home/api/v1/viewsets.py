from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from home.models import *
from rest_framework import permissions
from rest_framework_simplejwt.backends import TokenBackend
import requests
import json
from holidays import country_holidays
from validate_email import validate_email
import threading
from datetime import date
from rest_framework.decorators import api_view
from rest_framework.decorators import  permission_classes as permission_classes_for_method


from home.api.v1.serializers import (
    SignupSerializer,
    PostSerializer,
    LikeSerializer
)


class SignupViewSet(ModelViewSet):
    serializer_class = SignupSerializer
    http_method_names = ["post"]

    def perform_data_enrichment(self, request, retry):
        try:
            enriched_data = {}
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            print("User IP address --> ", ip)
            # ip = '39.110.142.79'
            response = requests.get(f"https://geolocation-db.com/json/{ip}?position=true")
            if response.status_code == 200:
                geolocation = json.loads(response.text)
                print("Geolocation -->", geolocation)
                if geolocation['country_code'] == 'Not found':
                    print(f"Can't fetch geolocation for {request.data['email']} having ip address {ip}")
                    enriched_data['latitude'] = None
                    enriched_data['longitude'] = None
                    enriched_data['country'] = None
                    enriched_data['holiday'] = None
                else:
                    given_holidays = country_holidays(geolocation['country_code'])
                    is_holiday = date.today() in given_holidays
                    print(f"{date.today} is {'a' if is_holiday else 'not a'} holiday")
                    # signup_user['ip'] = geolocation['IPv4']
                    enriched_data['latitude'] = geolocation['latitude']
                    enriched_data['longitude'] = geolocation['longitude']
                    enriched_data['country'] = geolocation['country_name']
                    enriched_data['holiday'] = is_holiday
            else:
                raise Exception(f"Can't fetch geolocation for {request.data['email']} having ip address {ip}")

            MyUser.objects.filter(username=request.data['username']).update(latitude=enriched_data['latitude'], longitude=enriched_data['longitude'], country=enriched_data['country'], holiday=enriched_data['holiday'])
            print(f"Enriched {request.data['email']} with data ", enriched_data)
        except Exception as e:
            print(e)
            if retry < 3:
                retry += 1
                self.perform_data_enrichment(request, retry)


    def create(self, request, *args, **kwargs):
        is_valid = validate_email(
            email_address=request.data['email'],
            check_format=True,
            check_blacklist=True,
            check_dns=True,
            dns_timeout=10,
            check_smtp=True,
            smtp_timeout=10,
            smtp_helo_host='my.host.name',
            smtp_from_address='my@from.addr.ess',
            smtp_skip_tls=False,
            smtp_tls_context=None,
            smtp_debug=False
        )
        if not is_valid:
            print(f"{request.data['email']} is not a valid email address")
            return Response(data={"message": f"{request.data['email']} is not a valid email address. Please enter a valid email."}, status=status.HTTP_400_BAD_REQUEST)
        data_enrichment = threading.Thread(target=self.perform_data_enrichment, name="DataEnrichment", args=[request, 1])
        data_enrichment.start()
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return super().create(request, *args, **kwargs)

class PostViewSet(ModelViewSet):
    serializer_class = PostSerializer
    queryset = Post.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ["get", "post", "put", 'delete']

    def list(self, request, *args, **kwargs):
        posts = Post.objects.all()
        return Response(data=PostSerializer(posts, many=True).data)

    def retrieve(self, request, *args, **kwargs):
        post_id = kwargs['pk']
        post = Post.objects.filter(id=post_id).first()
        if post is None:
            return Response(data={"message": f"No post found against id {post_id}."}, status=status.HTTP_404_NOT_FOUND)
        return Response(data=PostSerializer(post).data)

    def create(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        active_user = TokenBackend(algorithm='HS256').decode(token, verify=False)
        request.data['author'] = active_user['user_id']
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        post_id = kwargs['pk']
        post = Post.objects.filter(id=post_id).first()
        if post is None:
            return Response(data={"message": f"No post found against id {post_id}."}, status=status.HTTP_404_NOT_FOUND)
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        active_user = TokenBackend(algorithm='HS256').decode(token, verify=False)
        if post.author.id != active_user['user_id']:
            return Response(data={"message": f"User is not authorized to update post having id {post_id}."}, status=status.HTTP_403_FORBIDDEN)
        request.data['author'] = active_user['user_id']
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        post_id = kwargs['pk']
        print(f"Deleting post having id {post_id}")
        post = Post.objects.filter(id=post_id).first()
        if post is None:
            return Response(data={"message": f"No post found against id {post_id} to delete."}, status=status.HTTP_404_NOT_FOUND)
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        active_user = TokenBackend(algorithm='HS256').decode(token, verify=False)
        if post.author.id != active_user['user_id']:
            return Response(data={"message": f"User is not authorized to delete post having id {post_id}."}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @api_view(['GET'])
    @permission_classes_for_method((permissions.IsAuthenticated, ))
    def get_user_posts(request, user_id):
        user = MyUser.objects.filter(id=user_id).first()
        if user is None:
            return Response(data={"message": f"No user found against id {user_id} while retrieving posts."}, status=status.HTTP_404_NOT_FOUND)
        posts = Post.objects.filter(author=user_id)
        return Response(data=PostSerializer(posts, many=True).data)


class LikeViewSet(ModelViewSet):
    serializer_class = LikeSerializer
    queryset = Like.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    http_method_names = ["get", "post", "put"]

    # not required
    # def list(self, request, *args, **kwargs):
    #     token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    #     active_user = TokenBackend(algorithm='HS256').decode(token, verify=False)
    #     like = Like.objects.filter(user=active_user['user_id'])
    #     return Response(data=LikeSerializer(like, many=True).data)

    # not required
    # def retrieve(self, request, *args, **kwargs):
    #     like_id = kwargs['pk']
    #     like = Like.objects.filter(id=like_id).first()
    #     if like is None:
    #         return Response(data={"message": f"No like found against id {like_id}."}, status=status.HTTP_404_NOT_FOUND)
    #     token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    #     active_user = TokenBackend(algorithm='HS256').decode(token, verify=False)
    #     if like.user_id != active_user['user_id']:
    #         return Response(data={"message": f"User is not authorized to retrieve like info having id {like_id}."}, status=status.HTTP_403_FORBIDDEN)
    #     return Response(data=LikeSerializer(like).data)

    def create(self, request, *args, **kwargs):
        token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
        active_user = TokenBackend(algorithm='HS256').decode(token, verify=False)
        request.data['user'] = active_user['user_id']
        Like.objects.filter(user=active_user['user_id'],post=request.data['post']).delete()
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        return super().create(request, *args, **kwargs)

    # not required
    # def update(self, request, *args, **kwargs):
    #     like_id = kwargs['pk']
    #     like = Like.objects.filter(id=like_id).first()
    #     if like is None:
    #         return Response(data={"message": f"No like found against id {like_id} to update."}, status=status.HTTP_404_NOT_FOUND)
    #     token = request.META.get('HTTP_AUTHORIZATION', " ").split(' ')[1]
    #     active_user = TokenBackend(algorithm='HS256').decode(token, verify=False)
    #     if like.user_id != active_user['user_id']:
    #         return Response(data={"message": f"User is not authorized to update like having id {like_id}."},status=status.HTTP_403_FORBIDDEN)
    #     request.data['user'] = active_user['user_id']
    #     serializer = self.serializer_class(
    #         data=request.data, context={"request": request}
    #     )
    #     serializer.is_valid(raise_exception=True)
    #     return super().update(request, *args, **kwargs)

    # not required
    @api_view(['GET'])
    @permission_classes_for_method((permissions.IsAuthenticated, ))
    def get_reactions_on_post(request, post_id):
        post = Post.objects.filter(pk=post_id).first()
        if post is None:
            return Response(data={"message": f"No post found against id {post_id} to get reactions."}, status=status.HTTP_404_NOT_FOUND)
        num_of_likes = Like.objects.filter(post=post_id, value='Like').count()
        num_of_dislikes = Like.objects.filter(post=post_id, value='Like').count()
        return Response({"num_of_likes": num_of_likes, "num_of_likes": num_of_dislikes, "post_id": post_id}, status=200)

    # not required
    # @api_view(['GET'])
    # @permission_classes_for_method((permissions.IsAuthenticated, ))
    # def getUnlikeCountOnPost(request, post_id):
    #     post = Post.objects.filter(pk=post_id).first()
    #     if post is None:
    #         return Response(data={"message": f"No post found against id {post_id} to get unlikes count."}, status=status.HTTP_404_NOT_FOUND)
    #     numOfLikes = Like.objects.filter(post=post_id, value='Unlike').count()
    #     return Response({"numOfLikes": numOfLikes, "post_id": post_id}, status=200)
