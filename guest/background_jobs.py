import logging
from datetime import datetime, date, time

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from guest.models import BackgroundJob
from guest.wristband_lib import close_band_by_regime_and_soft_remove
from web.models import Project


logger = logging.getLogger(__name__)


def _clean_date_value(value):
    if value is None:
        return ""
    return str(value).strip().replace("_", " ")


def parse_job_datetime(value, default_date, default_time):
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, default_time)
    else:
        value = _clean_date_value(value)
        if value == "":
            dt = datetime.combine(default_date, default_time)
        else:
            dt = parse_datetime(value)
            if dt is None:
                parsed_date = parse_date(value)
                if parsed_date is None:
                    raise ValueError("Invalid datetime: {}".format(value))
                dt = datetime.combine(parsed_date, default_time)

    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def get_close_bands_params(start_date, end_date):
    today = timezone.localdate()
    start_dt = parse_job_datetime(start_date, today, time.min)
    end_dt = parse_job_datetime(end_date, today, time.max)
    return {
        "start_date": start_dt.isoformat(),
        "end_date": end_dt.isoformat(),
    }


def create_close_bands_job(project, username, start_date, end_date):
    params = get_close_bands_params(start_date, end_date)
    return BackgroundJob.objects.create(
        job_type=BackgroundJob.TYPE_CLOSE_BANDS,
        project_uuid=project.uuid,
        username=username,
        params=params,
    )


def run_background_job(job):
    with transaction.atomic():
        job = BackgroundJob.objects.select_for_update().get(pk=job.pk)
        if job.status == BackgroundJob.STATUS_RUNNING:
            return job
        if job.status == BackgroundJob.STATUS_SUCCESS:
            return job

        job.status = BackgroundJob.STATUS_RUNNING
        job.attempts += 1
        job.started_at = timezone.now()
        job.finished_at = None
        job.error_message = ""
        job.save(update_fields=[
            "status",
            "attempts",
            "started_at",
            "finished_at",
            "error_message",
            "updated_at",
        ])

    try:
        if job.job_type == BackgroundJob.TYPE_CLOSE_BANDS:
            result = run_close_bands_job(job)
        else:
            raise ValueError("Unsupported job type: {}".format(job.job_type))
    except Exception as e:
        logger.exception("Background job %s failed", job.id)
        job.status = BackgroundJob.STATUS_ERROR
        job.error_message = str(e)
        job.finished_at = timezone.now()
        job.save(update_fields=[
            "status",
            "error_message",
            "finished_at",
            "updated_at",
        ])
        return job

    job.status = BackgroundJob.STATUS_SUCCESS
    job.result = result
    job.finished_at = timezone.now()
    job.save(update_fields=[
        "status",
        "result",
        "finished_at",
        "updated_at",
    ])
    return job


def run_close_bands_job(job):
    project = Project.objects.get(uuid=job.project_uuid)
    start_date = parse_job_datetime(
        job.params.get("start_date"),
        timezone.localdate(),
        time.min,
    )
    end_date = parse_job_datetime(
        job.params.get("end_date"),
        timezone.localdate(),
        time.max,
    )

    guests_closed = close_band_by_regime_and_soft_remove(
        project,
        start_date,
        end_date,
    )

    return {
        "guests_closed_count": len(guests_closed),
        "guests_closed_sample": guests_closed[:100],
        "sample_truncated": len(guests_closed) > 100,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
    }


def process_pending_jobs(limit=10):
    jobs = list(
        BackgroundJob.objects
        .filter(status=BackgroundJob.STATUS_PENDING)
        .order_by("created_at")[:limit]
    )
    for job in jobs:
        run_background_job(job)
    return jobs
