import re
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand

from quiz.models import Event


def strip_html(text: str) -> str:
    """Remove HTML tags and decode common entities."""
    text = re.sub(r'<[^>]+>', '', text)
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
               .replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    return ' '.join(text.split())


class Command(BaseCommand):
    help = 'Import historical events from the parquet file into SQLite'

    def add_arguments(self, parser):
        default_path = Path(__file__).resolve().parents[4] / 'day_in_history.en.parquet'
        parser.add_argument(
            '--parquet',
            default=str(default_path),
            help='Path to the parquet file (default: repo root)',
        )

    def handle(self, *args, **options):
        parquet_path = Path(options['parquet'])
        if not parquet_path.exists():
            self.stderr.write(self.style.ERROR(f'File not found: {parquet_path}'))
            return

        self.stdout.write(f'Reading {parquet_path} ...')
        df = pd.read_parquet(parquet_path)

        self.stdout.write(f'Columns: {df.columns.tolist()}')
        self.stdout.write(f'Rows: {len(df)}')
        self.stdout.write('Sample:\n' + str(df.head(2)[['year', 'month', 'day', 'event_description']]))

        self.stdout.write('Clearing existing events...')
        Event.objects.all().delete()

        events = []
        for row in df.itertuples(index=False):
            desc = strip_html(str(row.event_description))
            if not desc:
                continue
            pages = strip_html(str(row.reference)) if pd.notna(row.reference) else ''
            events.append(Event(
                year=int(row.year),
                month=int(row.month),
                day=int(row.day),
                description=desc,
                pages=pages,
            ))

        self.stdout.write(f'Importing {len(events)} events...')
        Event.objects.bulk_create(events, batch_size=500)

        self.stdout.write(self.style.SUCCESS(f'Done. {Event.objects.count()} events in database.'))
