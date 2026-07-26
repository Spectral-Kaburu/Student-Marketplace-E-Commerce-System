from django.urls import path
from . import views

urlpatterns = [
    path('', views.GoodListView.as_view(), name='good_list'),
    path('<int:pk>/', views.GoodDetailView.as_view(), name='good_detail'),
    path('new/', views.GoodCreateView.as_view(), name='good_create'),
    path('<int:pk>/edit/', views.GoodUpdateView.as_view(), name='good_update'),
    path('<int:pk>/delete/', views.GoodDeleteView.as_view(), name='good_delete'),
    path('image/<int:pk>/delete/', views.GoodImageDeleteView.as_view(), name='good_image_delete'),
]