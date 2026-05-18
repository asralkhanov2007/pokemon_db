from django.core.management.base import BaseCommand
from cards.services import sync_cards, sync_all_sets
from cards.models import Card

class Command(BaseCommand):
    help = 'Import Pokemon cards from the PokemonTCG API'

    def add_arguments(self, parser):
        parser.add_argument('--set', type=str, help='Import one set by ID e.g. base1')
        parser.add_argument('--query', type=str, help='Lucene query e.g. "name:Charizard"')
        parser.add_argument('--max-pages', type=int, default=999)
        parser.add_argument('--page-size', type=int, default=250)
        parser.add_argument('--sets-only', action='store_true', help='Only import sets, not cards')
        parser.add_argument('--force', action='store_true', help='Force import even if cards exist')

    def handle(self, *args, **options):

        # Skip if already imported (unless --force)
        if not options['force'] and not options.get('set') and not options.get('query'):
            if Card.objects.exists():
                self.stdout.write(self.style.WARNING(
                    f'Database already has {Card.objects.count()} cards. Skipping import. Use --force to override.'
                ))
                return

        if options['sets_only']:
            self.stdout.write('Importing all sets...')
            created, updated = sync_all_sets()
            self.stdout.write(self.style.SUCCESS(
                f'Sets done - Created: {created} | Updated: {updated}'
            ))
            return

        def log(msg):
            self.stdout.write(f' {msg}')

        # Import all cards if no specific set or query
        if not options.get('set') and not options.get('query'):
            self.stdout.write('No set specified — importing ALL cards from all sets...')

            # First import all sets
            self.stdout.write('Step 1: Importing all sets metadata...')
            sync_all_sets()

            # Then import all cards
            self.stdout.write('Step 2: Importing all cards (this may take a while)...')

        created, updated, errors = sync_cards(
            set_id=options.get('set'),
            query=options.get('query'),
            max_pages=options.get('max_pages'),
            page_size=options.get('page_size'),
            logger=log,
        )
        self.stdout.write(self.style.SUCCESS(
            f'\nDone - Created: {created} | Updated: {updated} | Errors: {errors}'
        ))