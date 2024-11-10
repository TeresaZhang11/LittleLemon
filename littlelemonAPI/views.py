from django.shortcuts import render, get_object_or_404
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.exceptions import NotFound
from .models import MenuItem, Category, Order, OrderItem, Cart
from django.contrib.auth.models import User, Group
from . import serializers




        
class MenuItemListView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = serializers.MenuItemSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        
        return [IsAdminUser()]

class MenuItemSingleView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = serializers.MenuItemSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return []
        return [IsAdminUser()]

class ManagerListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        managers = Group.objects.get(name="Manager")
        return managers.user_set.all()

    def post(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        managers = Group.objects.get(name="Manager")
        user.groups.add(managers)
        return Response(status=status.HTTP_201_CREATED)
            

class ManagerDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        managers = Group.objects.get(name='Manager')
        if managers in instance.groups.all():
            managers.user_set.remove(instance)
        else:
            raise NotFound(detail="User is not part of the Manager group.")

class DeliveryListView(generics.ListCreateAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = serializers.UserSerializer

    def get_queryset(self):
        delivery_crew = Group.objects.get(name="Delivery crew")
        return delivery_crew.user_set.all()
    
    def post(self, request):
        username = request.data.get('username')
        user = get_object_or_404(User, username=username)
        delivery_crew = Group.objects.get(name="Delivery crew")
        user.groups.add(delivery_crew )
        return Response(status=status.HTTP_201_CREATED)

class DeliveryDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAdminUser]
    serializer_class = serializers.UserSerializer
    queryset = User.objects.all()

    def perform_destroy(self, instance):
        delivery_crew = Group.objects.get(name='Delivery crew')
        if delivery_crew in instance.groups.all():
            delivery_crew.user_set.remove(instance)
        else:
            raise NotFound(detail="User is not part of the delivery crew group.")

class CartListCreateDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    
    
    def get(self, request):
        items = Cart.objects.filter(user=request.user)
        serialize_class = serializers.CartSerializer(items, many=True)
        return Response(serialize_class.data)
    
    def post(self, request):
        menuitem = request.data.get("menuitem")
        quantity = request.data.get("quantity")
        item = Cart.objects.filter(user=request.user, menuitem=menuitem).first()
        if item:
            item.quantity = quantity
            item.price = quantity * item.unit_price
            item.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            item = MenuItem.objects.filter(id=menuitem).first()
            price = item.price * quantity
            request.data["price"] = price
            serializer_class = serializers.CartSerializer(data=request.data)
            if serializer_class.is_valid():
                serializer_class.save(user=request.user)
                return Response(serializer_class.data, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        Cart.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)




class OrdersListCreateView(APIView):
    

    def get(self, request):
        if request.user.is_staff:
            orders = Order.objects.all()
            serializer_class = serializers.OrderSerializer(orders, many=True)
            return Response(serializer_class.data)

        elif request.user.groups.filter(name='Delivery Crew').exists():
            orders = Order.objects.filter(delivery_crew=request.user)
            serializer_class = serializers.OrderSerializer(orders, many=True)
            return Response(serializer_class.data)

        elif request.user.is_authenticated:
            orders = Order.objects.filter(user=request.user)
            serializer_class = serializers.OrderSerializer(orders, many=True)
            return Response(serializer_class.data)
    
    def post(self, request):
        carts = Cart.objects.filter(user=request.user)
        if not carts:
            return Response({"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        total_price = 0
        for item in carts:
            unit_price = item.menuitem.price
            price = unit_price * item.quantity
            total_price += price
            data = {
                "order": request.user,
                "menuitem" : item.menuitem,
                "quantity" : item.quantity,
                "unit_price" : unit_price,
                "price" : price
            }
            OrderItem.objects.create(**data)
          
            Order.objects.create(user=request.user,total=total_price)
        Cart.objects.filter(user=request.user).delete()
        
        return Response(status=status.HTTP_201_CREATED)
      


class OrderSingleView(APIView):

    def get(self,request, *args, **kwargs):
        permission_classes = [IsAuthenticated]
        order = self.kwargs.get('order')
        items = OrderItem.objects.get(order=order)
        serializer_class = serializers.OrderItemSerializer(items)
        return Response(serializer_class.data)

    def put(self, request, *args, **kwargs):
        
        if request.user.is_staff:
            order = self.kwargs.get('order')
            item = OrderItem.objects.get(order=order)
            delivery_crew = request.data.get('delivery_crew')
            if delivery_crew:
                item.delivery_crew = delivery_crew
            
            status = request.data.get('status')
            if status:
                item.status = status
            
            if delivery_crew and status == 0:
                return Response({"message":"out for delivery"})
            
            if delivery_crew and status == 1:
                return Response({"message":"delivered"})

        elif request.user.groups.filter(name='Delivery Crew').exists():
            order = self.kwargs.get('order')
            item = OrderItem.objects.get(order=order)
            status = request.data.get('status')
            if status:
                item.status = status
            if status == 0:
                return Response({"message":"out for delivery"})
            
            if status == 1:
                return Response({"message":"delivered"})
        
    def delete(self, request, **kwargs):
        permission_classes = [IsAdminUser]
        order = self.kwargs.get('order')
        Order.objects.filter(pk=order).delete()
        return Response({"message":"deleted"})








