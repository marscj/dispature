from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.http import Http404, HttpResponse
from django.core.files.base import ContentFile
from django.db.models import Q

from rest_framework import viewsets, generics, views
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework_extensions.mixins import DetailSerializerMixin
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import list_route, api_view, detail_route
from django_filters.rest_framework import DjangoFilterBackend

from .permissions import (IsStaffSelf, IsStaffAdmin,IsAuthenticated, AllowAny, IsAdminOrIsSelf)
from .serializers import (OrderStaffSerializer, StaffSerializer,VehicleSerializer, TLISerializer,DLISerializer, PPISerializer, StoreSerializer, VehicleModelSellSerializer)
import main.models as MainModle
from .forms import StaffCreationForm

from rest_framework.renderers import JSONRenderer


class Utf8JSONRenderer(JSONRenderer):
    charset = 'utf-8'


# class BaseModelViewSet(viewsets.ModelViewSet, views.APIView):

#     def get_permissions(self):
#         if self.action == 'list':
#             permission_classes = [IsStaffAdmin]
#         else:
#             permission_classes = [IsAuthenticated]
#         return [permission() for permission in permission_classes]

class BaseModelViewSet(viewsets.ModelViewSet):
    renderer_classes = [Utf8JSONRenderer,]

class StaffViewSet(BaseModelViewSet):
    queryset = MainModle.Staff.objects.all()
    serializer_class = StaffSerializer
    pagination_class = PageNumberPagination
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    filter_fields = ['userId', 'driver', 'tourguide', 'status', 'accept', 'store', 'model']
    search_fields = '__all__'
    ordering_fields = '__all__' 

    def get_queryset(self):
        queryset = MainModle.Staff.objects.all().filter(status=1, accept=True, model=None)
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        
        if start_time is not None and end_time is not None:
            queryset = queryset.exclude(
                Q(order__status=0)
                &(Q(order__start_time__range=(start_time, end_time))
                | Q(order__end_time__range=(start_time, end_time))))

        return queryset

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [IsStaffAdmin]
        else:
            permission_classes = [IsStaffSelf]
        return [permission() for permission in permission_classes]

    @list_route(methods=['get'], permission_classes=[IsAuthenticated])
    def getSelf(self, request, pk=None):
        try:
            user = request.user.staff
        except Exception:
            return Response(status=401)
        
        staff = StaffSerializer(user)
        return Response(staff.data)

class VehicleViewSet(BaseModelViewSet):
    queryset = MainModle.Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    filter_fields = '__all__'
    search_fields = '__all__'
    ordering_fields = '__all__'

    def get_permissions(self):
        if self.action == 'list':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class OrderStaffViewSet(BaseModelViewSet):
    queryset = MainModle.OrderStaff.objects.exclude(status=3)
    serializer_class = OrderStaffSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    filter_fields = '__all__'
    search_fields = '__all__'
    ordering_fields = '__all__'

class StoreViewSet(BaseModelViewSet):
    queryset = MainModle.Store.objects.all()
    serializer_class = StoreSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    filter_fields = ['id']
    search_fields = '__all__'
    ordering_fields = '__all__'

class VehicleModelSellViewSet(BaseModelViewSet):
    queryset = MainModle.VehicleModel.objects.all()
    serializer_class = VehicleModelSellSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = (OrderingFilter, DjangoFilterBackend)

    filter_fields = ['model', 'name', 'seats']
    search_fields = '__all__'
    ordering_fields = '__all__'

    def get_queryset(self):
        queryset = MainModle.VehicleModel.objects.all()
        store = self.request.query_params.get('store', None)
        model = self.request.query_params.get('model', None)

        if store is not None:
            queryset = queryset.filter(store=store)
        
        if model is not None:
            queryset = queryset.filter(model=model)

        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        for item in queryset:
            if start_time is not None and end_time is not None:
                item.count = MainModle.Vehicle.objects.filter(model=item).exclude(Q(order__status=0)
                    & (Q(order__start_time__range=(start_time, end_time))
                    | Q(order__end_time__range=(start_time, end_time)))).count
        
        return queryset

    def list(self, request):
        queryset = self.get_queryset()
        serializer = VehicleModelSellSerializer(queryset, many=True)
        return Response(serializer.data)

class StaffModelViewSet(BaseModelViewSet):
    queryset = MainModle.Staff.objects.all()
    serializer_class = StaffSerializer
    pagination_class = PageNumberPagination
    filter_backends = (OrderingFilter, DjangoFilterBackend)
    filter_fields = ['userId', 'driver', 'tourguide', 'status', 'accept', 'store', 'model__model']
    search_fields = '__all__'
    ordering_fields = '__all__' 

    def get_queryset(self):
        queryset = MainModle.Staff.objects.all().filter(status=1, accept=True).exclude(model=None)
        start_time = self.request.query_params.get('start_time', None)
        end_time = self.request.query_params.get('end_time', None)
        
        if start_time is not None and end_time is not None:
            queryset = queryset.exclude(
                Q(order__status=0)
                &(Q(order__start_time__range=(start_time, end_time))
                | Q(order__end_time__range=(start_time, end_time))))

        return queryset


class StaffSigup(views.APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        staff = StaffCreationForm(request.data)
        if staff.is_valid():
            staff.save()
            return Response('ok')
        return Response(staff.errors, status=400)

class UpLoadFile(views.APIView):

    def post(self, request):
        try:
            staff = request.user.staff
        except Exception:
            return Response(status=401)

        photo=request.FILES.get('photo','')

        if photo:  
            file_content = ContentFile(photo.read()) 
            staff.photo.save(photo.name, file_content)
            staff.save()

            return Response(StaffSerializer(staff).data)