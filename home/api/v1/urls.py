from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from home.api.v1.viewsets import (
    SignupViewSet,
    PostViewSet,
    LikeViewSet,
)

router = DefaultRouter()
router.register("signup", SignupViewSet, basename="signup")
router.register("posts", PostViewSet, basename="posts")
router.register("posts/<int:post_id>/?", PostViewSet, basename="posts")
router.register("likes", LikeViewSet, basename="likes")
router.register("likes/<int:like_id>/?", LikeViewSet, basename="likes")

urlpatterns = [
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('refresh-token/', TokenRefreshView.as_view(), name='refresh-token'),
    path('user-posts/<int:user_id>', PostViewSet.get_user_posts, name='user-posts'),
    path('post-reactions/<int:post_id>', LikeViewSet.get_reactions_on_post, name='reaction-count'),
    # path('getunlikecount/<int:post_id>', LikeViewSet.getUnlikeCountOnPost, name='getunlikecount'),
    path("", include(router.urls))
]
