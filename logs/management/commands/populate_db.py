import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from users.models import CustomUser
from sites.models import ServerLocation
from logs.models import ActivityCategory, ActivitySubCategory, ServerRoomAccessLog

class Command(BaseCommand):
    help = 'Populates the database with dummy data for the server room access app.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Deleting old data...")
        # Clean up old data to prevent duplicates
        ServerRoomAccessLog.objects.all().delete()
        ActivitySubCategory.objects.all().delete()
        ActivityCategory.objects.all().delete()
        ServerLocation.objects.all().delete()
        CustomUser.objects.filter(is_superuser=False).delete()

        self.stdout.write("Creating new data...")

        # --- 1. Create Users ---
        pics = []
        for i in range(1, 4):
            pic, _ = CustomUser.objects.get_or_create(
                username=f'pic{i}',
                defaults={'first_name': f'PIC', 'last_name': f'User {i}', 'email': f'pic{i}@pln.co.id', 'department': 'IT Operations', 'is_staff': True}
            )
            pic.set_password('password123')
            pic.save()
            pics.append(pic)

        users = []
        user_names = [('Budi', 'Santoso'), ('Citra', 'Wijaya'), ('Dewi', 'Lestari'), ('Eko', 'Prasetyo'), ('Fitri', 'Handayani')]
        for first, last in user_names:
            user, _ = CustomUser.objects.get_or_create(
                username=first.lower(),
                defaults={'first_name': first, 'last_name': last, 'email': f'{first.lower()}@vendor.com', 'department': 'Vendor Services'}
            )
            user.set_password('password123')
            user.save()
            users.append(user)
        
        all_users = pics + users

        # --- 2. Create Sites with Coordinates (around Bandung) ---
        sites_data = [
            {'name': 'Data Center Gedebage', 'lat': -6.9452, 'lon': 107.7013},
            {'name': 'Server Room Pasteur', 'lat': -6.8922, 'lon': 107.5898},
            {'name': 'Network Hub Dago', 'lat': -6.8833, 'lon': 107.6143},
            {'name': 'IT Office Asia Afrika', 'lat': -6.9218, 'lon': 107.6071}
        ]
        sites = []
        for site_info in sites_data:
            site = ServerLocation.objects.create(
                name=site_info['name'],
                address=f'Jl. {site_info["name"].split(" ")[-1]} No. {random.randint(1, 100)}, Bandung',
                pic=random.choice(pics),
                latitude=site_info['lat'],
                longitude=site_info['lon']
            )
            sites.append(site)
        self.stdout.write(f"Created {len(sites)} sites with coordinates.")

        # --- 3. Create Categories ---
        categories_data = {
            'Pemeriksaan Fisik & Lingkungan': ['Suhu & Kelembapan', 'Sistem Pendingin (AC)', 'UPS & Daya Listrik', 'Kebersihan & Kerapian', 'Pencegahan Bencana'],
            'Pemeriksaan Perangkat Keras (Hardware)': ['Server', 'Perangkat Jaringan', 'Sistem Penyimpanan'],
            'Instalasi, Perawatan, & Konfigurasi': ['Instalasi/Pelepasan Fisik', 'Penggantian/Upgrade Komponen', 'Manajemen Kabel', 'Akses Konsol Fisik', 'Manajemen Backup Fisik'],
            'Keamanan & Aktivitas Lainnya': ['Verifikasi Keamanan', 'Inventarisasi', 'Mendampingi Pihak Ketiga'],
        }
        categories = []
        for cat_name, sub_cats in categories_data.items():
            category = ActivityCategory.objects.create(name=cat_name)
            categories.append(category)
            for sub_cat_name in sub_cats:
                ActivitySubCategory.objects.create(category=category, name=sub_cat_name)

        # --- 4. Create Logs ---
        # ... (The log creation part is the same as before) ...
        statuses = ['Pending', 'Approved', 'Denied', 'Checked-In', 'Completed']
        outcomes = ['Success', 'Partial', 'Failed']
        for _ in range(50):
            log_user = random.choice(all_users)
            log_site = random.choice(sites)
            log_category = random.choice(categories)
            log_subcategory = random.choice(log_category.subcategories.all())
            log_status = random.choice(statuses)
            
            request_time = timezone.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
            
            log = ServerRoomAccessLog.objects.create(
                user=log_user,
                location=log_site,
                category=log_category,
                subcategory=log_subcategory,
                notes=f'Dummy request for {log_subcategory.name}.',
                request_timestamp=request_time,
                status=log_status,
            )

            if log_status != 'Pending':
                log.approved_by = log_site.pic
            
            if log_status in ['Checked-In', 'Completed']:
                log.entry_timestamp = request_time + timedelta(hours=random.randint(1, 5))

            if log_status == 'Completed':
                log.exit_timestamp = log.entry_timestamp + timedelta(minutes=random.randint(30, 180))
                log.activity_report = f'Completed the {log_subcategory.name} task successfully.'
                log.outcome = random.choice(outcomes)
            
            log.save()
        
        self.stdout.write("Created 50 dummy log entries.")
        self.stdout.write(self.style.SUCCESS('Successfully populated the database!'))