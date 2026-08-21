from django.core.management.base import BaseCommand

from guest.background_jobs import process_pending_jobs, run_background_job
from guest.models import BackgroundJob


class Command(BaseCommand):
    help = "Process pending background jobs"

    def add_arguments(self, parser):
        parser.add_argument("--job-id", type=int, default=None)
        parser.add_argument("--limit", type=int, default=10)

    def handle(self, *args, **options):
        job_id = options["job_id"]

        if job_id is not None:
            job = BackgroundJob.objects.get(pk=job_id)
            run_background_job(job)
            job.refresh_from_db()
            self.stdout.write(
                "{} {} {}".format(job.id, job.job_type, job.status)
            )
            return

        jobs = process_pending_jobs(limit=options["limit"])
        self.stdout.write("Processed {} jobs".format(len(jobs)))
        for job in jobs:
            job.refresh_from_db()
            self.stdout.write(
                "{} {} {}".format(job.id, job.job_type, job.status)
            )
