from celery import shared_task
from django.utils import timezone

from research.models import RequestedMaterialsSharePointJob
from research.services import RequestedMaterialsSharePointError, RequestedMaterialsSharePointService


@shared_task
def deliver_requested_materials_sharepoint_job(job_id):
    try:
        job = RequestedMaterialsSharePointJob.objects.select_related(
            'request',
            'request__researcher',
        ).get(pk=job_id)
    except RequestedMaterialsSharePointJob.DoesNotExist:
        return

    job.status = 'running'
    job.current_step = 'checking_files'
    job.message = 'Checking files...'
    job.progress_current = 0
    job.started_date = timezone.now()
    job.error_message = ''
    job.save(update_fields=[
        'status', 'current_step', 'message', 'progress_current',
        'started_date', 'error_message'
    ])

    def update_progress(current_step, message, progress_current):
        job.current_step = current_step
        job.message = message
        job.progress_current = progress_current
        job.save(update_fields=['current_step', 'message', 'progress_current'])

    try:
        result = RequestedMaterialsSharePointService().deliver_requested_materials_for_request(
            job.request,
            progress_callback=update_progress,
        )
        job.status = 'completed'
        job.current_step = 'completed'
        job.message = 'Requested materials delivery completed.'
        job.progress_current = job.progress_total
        job.result = result
        job.finished_date = timezone.now()
        job.save(update_fields=[
            'status', 'current_step', 'message', 'progress_current',
            'result', 'finished_date'
        ])
    except RequestedMaterialsSharePointError as exc:
        job.status = 'failed'
        job.current_step = 'failed'
        job.message = 'Requested materials delivery failed.'
        job.error_message = str(exc)
        job.finished_date = timezone.now()
        job.save(update_fields=[
            'status', 'current_step', 'message', 'error_message', 'finished_date'
        ])
        raise
    except Exception as exc:
        job.status = 'failed'
        job.current_step = 'failed'
        job.message = 'Requested materials delivery failed.'
        job.error_message = str(exc)
        job.finished_date = timezone.now()
        job.save(update_fields=[
            'status', 'current_step', 'message', 'error_message', 'finished_date'
        ])
        raise
