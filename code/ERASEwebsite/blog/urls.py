from django.urls import path

from .views import (
    BlogListView,
    BlogDetailView,
    BlogManageView,
    BlogCreateView,
    BlogEditView,
    BlogDeleteView,
    BlogPublishView,
)

app_name = 'blog'

urlpatterns = [
    path('manage/', BlogManageView.as_view(), name='manage_posts'),
    path('create/', BlogCreateView.as_view(), name='post_create'),
    path('', BlogListView.as_view(), name='post_list'),
    path('<slug:slug>/', BlogDetailView.as_view(), name='post_detail'),
    path('<slug:slug>/edit/', BlogEditView.as_view(), name='post_edit'),
    path('<slug:slug>/delete/', BlogDeleteView.as_view(), name='post_delete'),
    path('publish/<int:post_id>/', BlogPublishView.as_view(), name='publish_post'),
]
