import json
import os

from django.conf import settings
from django.db.models import Count
from django.http import HttpResponse, FileResponse
from django.utils import dateformat
from pyreportjasper import JasperPy
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType

from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class FindingAidsLabelDataView(APIView):
    """
    Generates and returns a label-printing PDF for all containers in a series.

    The process is:
        1. Resolve carrier type and archival unit (series)
        2. Build a JSON data file containing one "label" record per container
        3. Run JasperReports (pyreportjasper) using the carrier type's jrxml template
        4. Return the resulting PDF as an inline FileResponse

    Notes:
        - This endpoint is public (AllowAny) to support printing workflows
          where authentication may be handled elsewhere (e.g. intranet or kiosk).
        - PDFs are created on disk under:
            clockwork_api/labels/output/
          and JSON work files under:
            clockwork_api/labels/work/
    """

    permission_classes = [AllowAny,]

    def get(self, request, *args, **kwargs):
        """
        Builds (or re-builds) the label PDF for a given series and carrier type.

        URL kwargs:
            series_id: ArchivalUnit id (series level in your routing)
            carrier_type_id: CarrierType id used to select the Jasper jrxml template

        Returns:
            FileResponse: PDF inline when generation succeeded and the file exists
            Response: 404 with a message if template is missing or PDF was not produced
        """
        carrier_type = get_object_or_404(CarrierType, pk=kwargs['carrier_type_id'])
        archival_unit = get_object_or_404(ArchivalUnit, pk=kwargs['series_id'])

        if carrier_type.jasper_file:
            self.make_json(kwargs['series_id'])
            self.create_report(archival_unit.reference_code_id, carrier_type.jasper_file)

            filename = '%s_%s.pdf' % (archival_unit.reference_code_id, carrier_type.jasper_file.replace(".jrxml", ""))
            file_path = os.path.join(settings.BASE_DIR, 'clockwork_api', 'labels', 'output', filename)

            if os.path.exists(file_path):
                response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
                response['Content-Disposition'] = 'inline; filename="%s"' % filename
                return response
            else:
                return Response('The requested pdf was not found in our server.', status=status.HTTP_404_NOT_FOUND)
        else:
            return Response('There are no jasper templates existing to this carrier type.', status=status.HTTP_404_NOT_FOUND)

    def make_json(self, series_id: int):
        """
        Builds the JSON data file consumed by JasperReports for label generation.

        For each container in the series, a "label" record is generated containing:
            - fonds/subfonds/series identifiers (f/sf/s)
            - container number (boxNo)
            - fonds/subfonds/series titles
            - first and last folder titles + formatted date ranges (when present)
            - restriction text from the series ISAD access rights (when available)

        Output:
            Writes a JSON file to:
                clockwork_api/labels/work/<reference_code_id>.json
            with schema:
                {"labels": [ ... ]}

        Args:
            series_id: ArchivalUnit primary key.
        """
        json_array = []

        archival_unit = get_object_or_404(ArchivalUnit, pk=series_id)
        containers = Container.objects.filter(archival_unit=archival_unit)

        for container in containers:
            label = {}
            label['f'] = archival_unit.fonds
            label['sf'] = archival_unit.subfonds
            label['s'] = archival_unit.series
            label['boxNo'] = container.container_no
            label['fondName'] = archival_unit.get_fonds().title
            label['subFondName'] = archival_unit.get_subfonds().title
            label['series'] = archival_unit.title

            start_folder = FindingAidsEntity.objects.filter(container=container).order_by('folder_no',
                                                                                          'sequence_no').first()
            last_folder = FindingAidsEntity.objects.filter(container=container).order_by('folder_no',
                                                                                         'sequence_no').last()

            if start_folder and last_folder:
                label['startFolderName'] = start_folder.title
                label['startFolderDate'] = self._encode_date(start_folder.date_from)
                if start_folder.date_to:
                    label['startFolderDate'] += " - %s" % self._encode_date(start_folder.date_to)

                label['lastFolderName'] = last_folder.title

                label['lastFolderDate'] = self._encode_date(last_folder.date_from)
                if last_folder.date_to:
                    label['lastFolderDate'] += " - %s" % self._encode_date(last_folder.date_to)

            isad = Isad.objects.filter(archival_unit=archival_unit).first()
            if isad:
                label['restrictionText'] = isad.access_rights.statement if isad.access_rights else ''
            else:
                label['restrictionText'] = 'Unknown'
            json_array.append(label)

        output_file = os.path.join(settings.BASE_DIR, 'clockwork_api', 'labels', 'work', '%s.json' % archival_unit.reference_code_id)
        with open(output_file, 'w') as outfile:
            json.dump({'labels': json_array}, outfile, indent=4)

    def _encode_date(self, date):
        """
        Formats an approximate/partial date for label display.

        Behavior:
            - If year/month/day exist: "d M, Y"
            - If year/month exist: "M, Y"
            - If only year exists: "Y"
            - If date is empty string: returns placeholder "YYYY"

        Args:
            date: A date-like object with year/month/day attributes, or ''.

        Returns:
            str: formatted date string suitable for labels.
        """
        if date != '':
            if date.year and date.month and date.day:
                return dateformat.format(date, 'd M, Y')
            elif date.year and date.month:
                return dateformat.format(date, 'M, Y')
            elif date.year:
                return dateformat.format(date, 'Y')
        else:
            return 'YYYY'

    def create_report(self, reference_code, jasper_file):
        """
        Produces a label PDF via JasperReports using the prepared JSON data file.

        Inputs:
            - JRXML template file from clockwork_api/labels/jasper/
            - JSON data file from clockwork_api/labels/work/<reference_code>.json

        Output:
            Writes PDF to:
                clockwork_api/labels/output/<reference_code>_<template_name>.pdf

        Args:
            reference_code: archival_unit.reference_code_id (used for filenames)
            jasper_file: jrxml filename defined on the carrier type.
        """
        output_file = os.path.join(settings.BASE_DIR, 'clockwork_api', 'labels', 'output', '%s_%s' % (reference_code, jasper_file.replace(".jrxml", "")))

        if jasper_file:
            input_file = os.path.join(settings.BASE_DIR, 'clockwork_api', 'labels', 'jasper', jasper_file)
            data_file = os.path.join(settings.BASE_DIR, 'clockwork_api', 'labels', 'work', '%s.json' % reference_code)

            jasper = JasperPy()
            jasper.process(
                input_file=input_file,
                output_file=output_file,
                format_list=["pdf"],
                parameters={},
                db_connection={
                    'driver': 'json',
                    'data_file': data_file,
                    'json_query': 'labels',
                },
                locale='en_US'
            )
        else:
            with open(output_file, 'w') as pdf:
                pass


class FindingAidsCarrierTypeDataView(APIView):
    """
    Returns carrier type breakdown for containers within a given series.

    This endpoint is used to drive label printing UI by showing:
        - which carrier types exist in the series
        - how many containers of each type exist
        - whether a Jasper template exists for that carrier type
    """

    def get(self, request, *args, **kwargs):
        """
        Aggregates containers by carrier type for a given series.

        URL kwargs:
            series_id: ArchivalUnit id

        Returns:
            Response[list[dict]] with:
                - carrier_type: display label
                - carrier_type_id: PK of the carrier type
                - total: number of containers in that carrier type
                - templateExists: whether carrier_type.jasper_file is set
        """
        response = []
        archival_unit = get_object_or_404(ArchivalUnit, pk=kwargs['series_id'])
        containers = Container.objects.filter(archival_unit=archival_unit)\
            .values('carrier_type__type', 'carrier_type_id', 'carrier_type__jasper_file')\
            .annotate(total=Count('carrier_type')).order_by('total')
        for c in containers:
            response.append({
                'carrier_type': c['carrier_type__type'],
                'carrier_type_id': c['carrier_type_id'],
                'total': c['total'],
                'templateExists': c['carrier_type__jasper_file'] is not None
            })
        return Response(response)
