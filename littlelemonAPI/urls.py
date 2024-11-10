from django.urls import path
from . import views

urlpatterns = [
    path('menu-items', views.MenuItemListView.as_view()),
    path('menu-items/<int:pk>', views.MenuItemSingleView.as_view()),

    path('groups/manager/users', views.ManagerListView.as_view()),
    path('groups/manager/users/<int:pk>', views.ManagerDeleteView.as_view()),

    path('groups/delivery-crew/users', views.DeliveryListView.as_view()),
    path('groups/delivery-crew/users/<int:pk>', views.DeliveryDeleteView.as_view()),

    path('cart/menu-items', views.CartListCreateDeleteView.as_view()),

    path('orders', views.OrdersListCreateView.as_view()),
    path('orders/<int:order>', views.OrderSingleView.as_view()),


]
