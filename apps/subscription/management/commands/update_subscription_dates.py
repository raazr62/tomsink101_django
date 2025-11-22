from django.core.management.base import BaseCommand
from apps.subscription.models import Subscription
import stripe
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta

stripe.api_key = settings.STRIPE_SECRET_KEY


class Command(BaseCommand):
    help = 'Update missing end_date for subscriptions from Stripe'

    def add_months(self, start_date, months):
        """Add months to a date."""
        month = start_date.month - 1 + months
        year = start_date.year + month // 12
        month = month % 12 + 1
        day = min(start_date.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
        return start_date.replace(year=year, month=month, day=day)

    def handle(self, *args, **options):
        # Get all active Stripe subscriptions without end_date
        subscriptions = Subscription.objects.filter(
            payment_method='stripe',
            is_active=True,
            end_date__isnull=True
        ).exclude(stripe_subscription_id='')

        self.stdout.write(f'Found {subscriptions.count()} subscriptions to update')

        updated = 0
        failed = 0

        for subscription in subscriptions:
            try:
                # Fetch from Stripe
                stripe_sub = stripe.Subscription.retrieve(subscription.stripe_subscription_id)
                
                end_date = None
                
                # Try to get from Stripe
                if hasattr(stripe_sub, 'current_period_end'):
                    end_date = datetime.fromtimestamp(stripe_sub.current_period_end)
                    if timezone.is_naive(end_date):
                        end_date = timezone.make_aware(end_date)
                # Fallback: Calculate from start_date and package interval
                elif subscription.start_date and subscription.package:
                    start = subscription.start_date
                    interval = subscription.package.interval
                    
                    if interval == 'month':
                        end_date = self.add_months(start, 1)
                    elif interval == 'year':
                        end_date = self.add_months(start, 12)
                    elif interval == 'week':
                        end_date = start + timedelta(weeks=1)
                    elif interval == 'daily':
                        end_date = start + timedelta(days=1)
                
                if end_date:
                    subscription.end_date = end_date
                    subscription.save()
                    updated += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Updated subscription {subscription.id} - End date: {subscription.end_date}'
                        )
                    )
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f'No end date found for subscription {subscription.id}'
                        )
                    )
            except stripe.error.StripeError as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Failed to update subscription {subscription.id}: {str(e)}'
                    )
                )
            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'Error updating subscription {subscription.id}: {str(e)}'
                    )
                )

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Successfully updated: {updated}'))
        self.stdout.write(self.style.WARNING(f'Failed: {failed}'))
