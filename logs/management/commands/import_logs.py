import csv
from datetime import datetime
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from users.models import CustomUser
from sites.models import ServerLocation
from logs.models import ServerRoomAccessLog, ActivityCategory

class Command(BaseCommand):
    help = 'Imports access logs from a specified CSV file.'

    def add_arguments(self, parser):
        parser.add_argument('--csv-path', type=str, help='The full path to the CSV file.')
        parser.add_argument('--site-name', type=str, help='The name of the ServerLocation to assign these logs to.')

    def handle(self, *args, **kwargs):
        csv_path = kwargs['csv_path']
        site_name = kwargs['site_name']

        if not csv_path or not site_name:
            raise CommandError("Both --csv-path and --site-name are required.")

        try:
            location = ServerLocation.objects.get(name__iexact=site_name)
            self.stdout.write(self.style.SUCCESS(f'Found site: "{location.name}"'))
        except ServerLocation.DoesNotExist:
            raise CommandError(f'ServerLocation with name "{site_name}" does not exist. Please create it first.')

        category, _ = ActivityCategory.objects.get_or_create(name='Imported Historical Data')

        imported_count = 0
        skipped_count = 0

        with open(csv_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    user_name = row.get('nama', '').strip().lower()
                    if not user_name:
                        self.stdout.write(self.style.WARNING(f"Skipping row {row.get('id')} due to missing user name."))
                        skipped_count += 1
                        continue
                    
                    user, created = CustomUser.objects.get_or_create(
                        username=user_name.replace(" ", "."),
                        defaults={
                            'first_name': user_name.split()[0].title() if ' ' in user_name else user_name.title(),
                            'last_name': user_name.split()[-1].title() if ' ' in user_name else '',
                        }
                    )
                    if created:
                        user.set_password('password123')
                        user.save()
                        self.stdout.write(f'Created new user: {user.username}')

                    pic_name = row.get('pic', '').strip().lower()
                    approved_by = None
                    if pic_name:
                        pic, created = CustomUser.objects.get_or_create(
                            username=pic_name.replace(" ", "."),
                            defaults={'first_name': pic_name.title(), 'is_staff': True}
                        )
                        if created:
                            pic.set_password('password123')
                            pic.save()
                            self.stdout.write(f'Created new PIC user: {pic.username}')
                        approved_by = pic

                    tgl_kunjungan = row.get('tgl_kunjungan')
                    check_in_time = row.get('check_in')
                    check_out_time = row.get('check_out')

                    entry_timestamp = timezone.make_aware(datetime.strptime(f"{tgl_kunjungan} {check_in_time}", "%Y-%m-%d %H:%M:%S"))
                    exit_timestamp = None
                    if check_out_time:
                        exit_timestamp = timezone.make_aware(datetime.strptime(f"{tgl_kunjungan} {check_out_time}", "%Y-%m-%d %H:%M:%S"))

                    log, created = ServerRoomAccessLog.objects.get_or_create(
                        user=user,
                        location=location,
                        entry_timestamp=entry_timestamp,
                        defaults={
                            'scheduled_for_date': entry_timestamp.date(),
                            'request_timestamp': entry_timestamp,
                            'exit_timestamp': exit_timestamp,
                            'notes': row.get('perihal', ''),
                            'activity_report': row.get('keterangan', ''),
                            'status': 'Completed',
                            'outcome': 'Success' if row.get('keterangan') else '',
                            'category': category,
                            'approved_by': approved_by
                        }
                    )

                    if created:
                        imported_count += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error processing row {row.get('id')}: {e}"))
                    skipped_count += 1
                    continue
        
        self.stdout.write(self.style.SUCCESS(f"\nImport complete. Successfully imported {imported_count} new logs. Skipped {skipped_count} rows."))