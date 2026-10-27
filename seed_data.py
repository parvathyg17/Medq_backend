import os
import shutil
from pathlib import Path
from decimal import Decimal
import django

# Setup django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medq_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.products.models import Category, Product
from apps.orders.models import Order, OrderItem
from apps.feedback.models import ContactMessage

User = get_user_model()
BASE_DIR = Path(__file__).resolve().parent

def seed():
    print("[SEED] Seeding MEDQ Database...")

    # 1. Ensure Media Directory Exists
    media_products_dir = BASE_DIR / 'media' / 'products'
    media_products_dir.mkdir(parents=True, exist_ok=True)

    # Copy any available original images
    src_images_dir = BASE_DIR.parent / 'src' / 'src' / 'asset' / 'images'
    if src_images_dir.exists():
        for img_file in src_images_dir.glob('*.*'):
            target = media_products_dir / img_file.name
            if not target.exists():
                shutil.copy(img_file, target)

    # 2. Seed Users
    print("Creating Demo Users...")
    admin_user, _ = User.objects.get_or_create(
        email='admin@medq.com',
        defaults={
            'username': 'admin@medq.com',
            'full_name': 'Dr. Sarah Connor (Admin)',
            'phone': '9876543210',
            'role': User.Role.ADMIN,
            'is_staff': True,
            'is_superuser': True
        }
    )
    admin_user.set_password('Admin@123')
    admin_user.save()

    customer_user, _ = User.objects.get_or_create(
        email='customer@medq.com',
        defaults={
            'username': 'customer@medq.com',
            'full_name': 'Johnathan Davis',
            'phone': '9876543211',
            'role': User.Role.CUSTOMER
        }
    )
    customer_user.set_password('Customer@123')
    customer_user.save()

    delivery_user, _ = User.objects.get_or_create(
        email='delivery@medq.com',
        defaults={
            'username': 'delivery@medq.com',
            'full_name': 'Alex Mercer (Express Delivery)',
            'phone': '9876543212',
            'role': User.Role.DELIVERY_PERSON
        }
    )
    delivery_user.set_password('Delivery@123')
    delivery_user.save()

    # 3. Seed Categories
    print("Creating Medical Equipment Categories...")
    category_data = [
        ("Diagnostic Equipment", "diagnostic", "Medical devices used to identify disease or illness through physical testing and body imaging."),
        ("Therapeutic Equipment", "therapeutic", "Devices designed to assist in healing, rehabilitation, respiratory support, and chronic disease management."),
        ("Laboratory Equipment", "laboratory", "High-precision diagnostic centrifuges, blood analyzers, and clinical microscopes."),
        ("Patient Care Equipment", "patient-care", "Hospital beds, patient monitors, wheelchairs, and assistive devices for clinic and home care.")
    ]

    categories = {}
    for name, slug, desc in category_data:
        cat, _ = Category.objects.get_or_create(
            name=name,
            defaults={'slug': slug, 'description': desc, 'is_active': True}
        )
        categories[name] = cat

    # 4. Seed Products
    print("Creating Medical Equipment Catalog...")
    products_data = [
        {
            "name": "Clinical Digital Infrared Thermometer",
            "slug": "clinical-digital-infrared-thermometer",
            "sku": "DIAG-101",
            "category": categories["Diagnostic Equipment"],
            "brand": "Omron Healthcare",
            "description": "Non-contact medical-grade infrared body thermometer with LCD display and 0.5-second fever alarm.",
            "price": Decimal("1499.00"),
            "discount_price": Decimal("1299.00"),
            "stock_quantity": 45,
            "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "Automatic Digital Blood Pressure Monitor",
            "slug": "automatic-digital-blood-pressure-monitor",
            "sku": "DIAG-102",
            "category": categories["Diagnostic Equipment"],
            "brand": "Dr. Morepen",
            "description": "Clinically validated upper-arm digital sphygmomanometer with irregular heartbeat detection and dual-user memory.",
            "price": Decimal("2499.00"),
            "discount_price": Decimal("1999.00"),
            "stock_quantity": 30,
            "image_url": "https://images.unsplash.com/photo-1629909613654-28e377c37b09?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "Fingertip Pulse Oximeter OLED",
            "slug": "fingertip-pulse-oximeter-oled",
            "sku": "DIAG-103",
            "category": categories["Diagnostic Equipment"],
            "brand": "Beurer Medical",
            "description": "High-accuracy SpO2 oxygen saturation monitor with pulse rate waveform graph and multi-directional display.",
            "price": Decimal("1250.00"),
            "discount_price": Decimal("999.00"),
            "stock_quantity": 60,
            "image_url": "https://images.unsplash.com/photo-1584744982491-665216d95f8b?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "12-Lead Portable ECG Machine",
            "slug": "12-lead-portable-ecg-machine",
            "sku": "DIAG-104",
            "category": categories["Diagnostic Equipment"],
            "brand": "Philips Medical",
            "description": "Synchronous 12-lead electrocardiograph with thermal printing, digital touchscreen, and auto-interpretation software.",
            "price": Decimal("48500.00"),
            "discount_price": Decimal("45000.00"),
            "stock_quantity": 8,
            "image_url": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "Ultrasonic Clinical Nebulizer",
            "slug": "ultrasonic-clinical-nebulizer",
            "sku": "THER-201",
            "category": categories["Therapeutic Equipment"],
            "brand": "Philips Respironics",
            "description": "Ultra-quiet aerosol medication compressor nebulizer for pediatric and adult respiratory therapy.",
            "price": Decimal("2899.00"),
            "discount_price": Decimal("2499.00"),
            "stock_quantity": 25,
            "image_url": "https://images.unsplash.com/photo-1631815588090-d4bfec5b1ccb?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "Homecare Oxygen Concentrator 5L/min",
            "slug": "homecare-oxygen-concentrator-5l",
            "sku": "THER-202",
            "category": categories["Therapeutic Equipment"],
            "brand": "DeVilbiss Healthcare",
            "description": "Medical-grade 93% continuous oxygen flow concentrator with integrated oxygen sensing purity alarm.",
            "price": Decimal("42000.00"),
            "discount_price": Decimal("38500.00"),
            "stock_quantity": 12,
            "image_url": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "Multi-Parameter Vital Signs Patient Monitor 12.1\"",
            "slug": "patient-vital-signs-monitor-12",
            "sku": "PAT-301",
            "category": categories["Patient Care Equipment"],
            "brand": "Mindray Medical",
            "description": "ICU-ready patient monitor supporting ECG, NIBP, SpO2, Respiration, Temperature, and Pulse Rate with visual alarms.",
            "price": Decimal("65000.00"),
            "discount_price": Decimal("59999.00"),
            "stock_quantity": 6,
            "image_url": "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "Motorized Electric Wheelchair with Smart Joystick",
            "slug": "motorized-electric-wheelchair",
            "sku": "PAT-302",
            "category": categories["Patient Care Equipment"],
            "brand": "Invacare",
            "description": "Lightweight foldable powered mobility wheelchair with 360-degree intelligent joystick and electromagnetic brakes.",
            "price": Decimal("58000.00"),
            "discount_price": Decimal("52000.00"),
            "stock_quantity": 4,
            "image_url": "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "3-Function Electric ICU Hospital Bed",
            "slug": "3-function-electric-icu-hospital-bed",
            "sku": "PAT-303",
            "category": categories["Patient Care Equipment"],
            "brand": "Stryker Healthcare",
            "description": "Full-electric hospital bed with handheld remote, motorized backrest, knee elevation, and collapsible side rails.",
            "price": Decimal("75000.00"),
            "discount_price": Decimal("69000.00"),
            "stock_quantity": 3,
            "image_url": "https://images.unsplash.com/photo-1519494026892-80bbd2d6fd0d?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "Digital Clinical Centrifuge 4000 RPM",
            "slug": "digital-clinical-centrifuge-4000",
            "sku": "LAB-401",
            "category": categories["Laboratory Equipment"],
            "brand": "Thermo Fisher Scientific",
            "description": "Microprocessor controlled benchtop laboratory centrifuge with 8-tube rotor capacity and digital speed control.",
            "price": Decimal("18500.00"),
            "discount_price": Decimal("16500.00"),
            "stock_quantity": 15,
            "image_url": "https://images.unsplash.com/photo-1582719508461-905c673771fd?w=600&auto=format&fit=crop&q=80"
        },
        {
            "name": "Binocular Clinical Microscope 1000x LED",
            "slug": "binocular-clinical-microscope-1000x",
            "sku": "LAB-402",
            "category": categories["Laboratory Equipment"],
            "brand": "Olympus Life Science",
            "description": "Achromatic optical laboratory microscope with 40x-1000x magnification, coaxial coarse/fine focus, and LED illumination.",
            "price": Decimal("28000.00"),
            "discount_price": Decimal("25500.00"),
            "stock_quantity": 9,
            "image_url": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=600&auto=format&fit=crop&q=80"
        }
    ]

    for prod_data in products_data:
        Product.objects.get_or_create(
            slug=prod_data["slug"],
            defaults=prod_data
        )

    # 5. Seed Sample Orders
    print("Creating Demo Orders...")
    p1 = Product.objects.get(slug="clinical-digital-infrared-thermometer")
    p2 = Product.objects.get(slug="automatic-digital-blood-pressure-monitor")

    order1, created1 = Order.objects.get_or_create(
        order_number="MEDQ-DEMO-001",
        defaults={
            "user": customer_user,
            "delivery_name": "Johnathan Davis",
            "email": "customer@medq.com",
            "phone_number": "9876543211",
            "address": "742 Evergreen Terrace, Medical District",
            "landmark": "Opposite General Hospital",
            "pin_code": "560001",
            "payment_method": Order.PaymentMethod.CREDIT_CARD,
            "payment_status": Order.PaymentStatus.COMPLETED,
            "masked_card_number": "•••• •••• •••• 4242",
            "subtotal": p1.effective_price + p2.effective_price,
            "shipping_fee": Decimal("0.00"),
            "total_amount": p1.effective_price + p2.effective_price,
            "status": Order.Status.SHIPPED,
            "delivery_boy": delivery_user
        }
    )
    if created1:
        OrderItem.objects.create(
            order=order1, product=p1, product_name=p1.name, product_sku=p1.sku,
            price=p1.effective_price, quantity=1, total_price=p1.effective_price
        )
        OrderItem.objects.create(
            order=order1, product=p2, product_name=p2.name, product_sku=p2.sku,
            price=p2.effective_price, quantity=1, total_price=p2.effective_price
        )

    # 6. Seed Inquiries
    print("Creating Contact Inquiries...")
    ContactMessage.objects.get_or_create(
        subject="Bulk Order Inquiry for Clinical Monitors",
        defaults={
            "name": "Dr. Rajesh Kumar",
            "email": "dr.rajesh@stjudehospital.org",
            "message": "We would like a formal quote for 15 units of the 12.1-inch Vital Signs Patient Monitor for our new cardiology wing."
        }
    )

    print("[DONE] Seed Data Generated Successfully!")
    print(f"Users created: admin@medq.com, customer@medq.com, delivery@medq.com (Password: Admin@123 / Customer@123 / Delivery@123)")
    print(f"Products created: {Product.objects.count()}")

if __name__ == '__main__':
    seed()
