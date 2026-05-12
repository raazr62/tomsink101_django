from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

import stripe

from apps.subscription.models import Package


class Command(BaseCommand):
    help = (
        "Recreate Stripe Product+Price IDs for packages using the currently configured STRIPE_SECRET_KEY. "
        "Useful after switching Stripe accounts or test/live keys."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--all",
            action="store_true",
            help="Resync all packages.",
        )
        parser.add_argument(
            "--package-id",
            action="append",
            dest="package_ids",
            default=[],
            help="Resync a specific package ID (repeatable).",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Recreate Stripe IDs even if they already exist.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print what would happen without writing to the database.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Actually perform the resync (required unless --dry-run).",
        )

    def handle(self, *args, **options):
        if not getattr(settings, "STRIPE_SECRET_KEY", None):
            raise CommandError("STRIPE_SECRET_KEY is not configured")

        if not options["dry_run"] and not options["yes"]:
            raise CommandError("Refusing to modify data without --yes (or use --dry-run)")

        package_ids: list[str] = options["package_ids"]
        do_all: bool = options["all"]
        force: bool = options["force"]
        dry_run: bool = options["dry_run"]

        if not do_all and not package_ids:
            raise CommandError("Specify --all or at least one --package-id")

        queryset = Package.objects.all().order_by("id") if do_all else Package.objects.filter(id__in=package_ids)

        stripe.api_key = settings.STRIPE_SECRET_KEY

        total = queryset.count()
        updated = 0
        skipped = 0

        for package in queryset:
            needs_sync = force or (not package.stripe_product_id) or (not package.stripe_price_id)
            if not needs_sync:
                skipped += 1
                continue

            if package.discount_price is None or package.discount_price <= 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"Skipping package id={package.id} name={package.name!r}: discount_price={package.discount_price}"
                    )
                )
                skipped += 1
                continue

            self.stdout.write(f"Resyncing package id={package.id} name={package.name!r}")

            if dry_run:
                continue

            try:
                stripe_product = stripe.Product.create(
                    name=package.name,
                    description=package.description or "",
                )
                stripe_price = stripe.Price.create(
                    product=stripe_product.id,
                    currency="USD",
                    unit_amount=int(package.discount_price * 100),
                    recurring={"interval": package.interval},
                )
            except stripe.error.StripeError as e:
                raise CommandError(f"Stripe error while syncing package id={package.id}: {e}")

            Package.objects.filter(pk=package.pk).update(
                stripe_product_id=stripe_product.id,
                stripe_price_id=stripe_price.id,
            )
            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. total={total} updated={updated} skipped={skipped} dry_run={dry_run} force={force}"
            )
        )
