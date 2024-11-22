from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from homifi_app.models import SavedSearch
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send notifications for saved property searches'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force send notifications regardless of last notification time',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without sending actual emails',
        )

    def handle(self, *args, **options):
        try:
            # Get all saved searches with notifications enabled
            searches = SavedSearch.objects.filter(notification_enabled=True)
            
            if not options['force']:
                # Only get searches that haven't been notified in the last 24 hours
                one_day_ago = timezone.now() - timezone.timedelta(days=1)
                searches = searches.filter(
                    Q(last_notification_sent__isnull=True) |
                    Q(last_notification_sent__lt=one_day_ago)
                )
            
            total_searches = searches.count()
            notifications_sent = 0
            
            self.stdout.write(f"Processing {total_searches} saved searches...")
            
            for search in searches:
                try:
                    if options['dry_run']:
                        # Just show what would be done
                        matching_properties = search.get_matching_properties()
                        self.stdout.write(
                            f"Would send notification to {search.user.email} about "
                            f"{matching_properties.count()} properties"
                        )
                        notifications_sent += 1
                        continue

                    # Validate email before sending
                    if not search.user.email:
                        raise ValidationError(f"User {search.user.username} has no email address")

                    # Send notification for each search
                    search.send_notification()
                    notifications_sent += 1
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Successfully sent notification for search ID {search.id} "
                            f"(User: {search.user.username})"
                        )
                    )
                except ValidationError as e:
                    logger.warning(
                        f"Validation error for search ID {search.id}: {str(e)}"
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skipped search ID {search.id}: {str(e)}"
                        )
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to send notification for search ID {search.id}: {str(e)}"
                    )
                    self.stdout.write(
                        self.style.ERROR(
                            f"Failed to send notification for search ID {search.id}: {str(e)}"
                        )
                    )
            
            status = "Would have processed" if options['dry_run'] else "Successfully processed"
            self.stdout.write(
                self.style.SUCCESS(
                    f"{status} {notifications_sent} out of {total_searches} searches"
                )
            )
            
        except Exception as e:
            logger.error(f"Error in send_search_notifications command: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f"Command failed: {str(e)}")
            )