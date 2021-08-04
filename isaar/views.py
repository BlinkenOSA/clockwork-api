from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.filters import OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from isaar.models import Isaar, IsaarRelationship, IsaarPlaceQualifier
from isaar.serializers import IsaarSelectSerializer, IsaarReadSerializer, IsaarWriteSerializer, IsaarListSerializer, \
    IsaarRelationshipSerializer, IsaarPlaceQualifierSerializer


class IsaarList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = Isaar.objects.all()
    method_serializer_classes = {
        ('GET', ): IsaarListSerializer,
        ('POST', ): IsaarWriteSerializer
    }
    filter_backends = (SearchFilter, OrderingFilter, DjangoFilterBackend)
    ordering_fields = ('name', 'type', 'status')
    filterset_fields = ('type', 'status')
    search_fields = ('name',)


class IsaarDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Isaar.objects.all()
    method_serializer_classes = {
        ('GET', ): IsaarReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): IsaarWriteSerializer
    }


class IsaarSelectList(generics.ListAPIView):
    serializer_class = IsaarSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ('type',)
    search_fields = ('name',)
    queryset = Isaar.objects.all().order_by('name')


class IsaarRelationshipSelectList(generics.ListAPIView):
    serializer_class = IsaarRelationshipSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('theme',)
    queryset = IsaarRelationship.objects.all().order_by('relationship')


class IsaarPlaceQualifierSelectList(generics.ListAPIView):
    serializer_class = IsaarPlaceQualifierSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('place',)
    queryset = IsaarPlaceQualifier.objects.all().order_by('qualifier')
