import random

from django.db.models.aggregates import Sum, Count
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from container.models import Container
from finding_aids.models import FindingAidsEntity


def get_containers(archival_unit):
    if archival_unit == 0:
        containers = Container.objects.all()
    else:
        archival_unit = get_object_or_404(ArchivalUnit, pk=archival_unit)
        if archival_unit.level == 'F':
            containers = Container.objects.filter(archival_unit__fonds=archival_unit.fonds)
        elif archival_unit.level == 'SF':
            containers = Container.objects.filter(archival_unit__fonds=archival_unit.fonds,
                                                  archival_unit__subfonds=archival_unit.subfonds)
        else:
            containers = Container.objects.filter(archival_unit=archival_unit)
    return {'containers': containers, 'archival_unit': archival_unit}


class LinearMeterView(APIView):
    def get(self, request, archival_unit):
        containers_dict = get_containers(archival_unit)

        containers = containers_dict['containers']
        archival_unit = containers_dict['archival_unit']

        cw_unit = containers.aggregate(Sum('carrier_type__width'))['carrier_type__width__sum']

        if not cw_unit:
            cw_unit = 0

        cw_all = Container.objects.all().aggregate(Sum('carrier_type__width'))['carrier_type__width__sum']

        if archival_unit == 0:
            cw_top_unit = cw_all
        else:
            if archival_unit.level == 'F':
                cw_top_unit = Container.objects.filter(archival_unit__fonds=archival_unit.fonds).aggregate(
                    Sum('carrier_type__width'))['carrier_type__width__sum']
            elif archival_unit.level == 'SF':
                cw_top_unit = Container.objects.filter(archival_unit__fonds=archival_unit.fonds).aggregate(
                    Sum('carrier_type__width'))['carrier_type__width__sum']
            else:
                cw_top_unit = Container.objects.filter(archival_unit__fonds=archival_unit.fonds,
                                                       archival_unit__subfonds=archival_unit.subfonds).aggregate(
                    Sum('carrier_type__width'))['carrier_type__width__sum']

        cw_percentage = cw_unit / cw_top_unit * 100
        cw_all_percentage = cw_unit / cw_all * 100

        dataset = {
            'linear_meter': "%.2f" % (cw_unit / 100),
            'linear_meter_percentage': "%.2f" % cw_percentage,
            'linear_meter_all': "%.2f" % (cw_all / 100),
            'linear_meter_all_pecentage': "%.2f" % cw_all_percentage
        }

        return Response(dataset)


class PublishedItems(APIView):
    def get(self, request, archival_unit):
        containers = get_containers(archival_unit)['containers']
        items = FindingAidsEntity.objects.filter(container__in=containers)

        if items.count() > 0:
            items_all = items.count()
            items_published = items.filter(published=True).count()

            items_percentage = items_published / items_all * 100
        else:
            items_all = 0
            items_published = 0
            items_percentage = 0

        dataset = {
            'total_items': items_all,
            'published_items': items_published,
            'published_items_percentage': "%.2f" % items_percentage,
        }

        return Response(dataset)


class CarrierTypes(APIView):
    def get(self, request, archival_unit):
        data = []

        containers = get_containers(archival_unit)['containers']
        archival_unit = get_containers(archival_unit)['archival_unit']

        cts = containers.values('carrier_type__type').annotate(total=Count('id')).order_by('-total')

        for ct in cts:
            data.append({
                'type': ct['carrier_type__type'],
                'total': ct['total']
            })

        return Response(data)
