import logging
import sys
import zipfile

from csv import DictWriter
from pathlib import Path

from django.core.management import BaseCommand

from processing.models import Batch, Item


logger = logging.getLogger(__name__)

HEADER = [
    'Identifier',
    'Title',
    'Date',
    'Creator',
    'Format',
    'Rights Statement',
    'FILES',
    'Object Type'
]


class Command(BaseCommand):
    help = "Exports batch"

    def add_arguments(self, parser):
        parser.add_argument('batch_selected', type=int, help='Batch to be exported.')
        parser.add_argument('file_path', type=str, help='File path to export.')

    def handle(self, *args, **options):
        batch_selected = options['batch_selected']
        batch = Batch.objects.get(id=batch_selected)
        batch_selected_name = batch.name
        
        # Check if all items are reviewed
        total_items_count = Item.objects.filter(batch=batch_selected).count()
        not_reviewed = Item.objects.filter(
            batch=batch_selected,
            review_status=False
            )
        not_reviewed_count = not_reviewed.count()
        if not_reviewed_count != 0:
            logger.info(f'Not all items in this batch have been reviewed.')
            logger.info(f'Number of items not reviewed: {not_reviewed_count} out of {total_items_count}')
            result = input('Continue export? Please answer yes or no: ')
            if result == 'yes':
                pass
            else:
                logger.info(f'Exiting Script')
                sys.exit()
        else:
            pass
        

        # Select items only in selected batch and marked publish
        items = Item.objects.filter(
            batch=batch_selected,
            publish=True
            )
        item = Item.objects.all()

        # Create output path if not exists
        path = Path(options['file_path'], batch_selected_name)
        path.mkdir(parents=True, exist_ok=True)
        output_path = path

        # Open the output CSV for writing
        with open(output_path/'whpool.csv', 'w') as csv_file:
            csv_writer = DictWriter(csv_file, fieldnames=HEADER, extrasaction='ignore', escapechar='\\')
            # Add the headers
            csv_writer.writeheader()

            # Iterate over items in database
            for item in items:
                logger.info(f'Exporting: {item.id}, {item.title}')
                
                # Create HTML file
                id = str(item.id)
                file_name = ('body-' + id + '.html')
                file = Path(output_path/id/file_name)
                file.parent.mkdir(parents=True, exist_ok=True)
                with open(file, 'w') as file:
                    file.write(item.body_final)
                
                # Write CSV row
                csv_writer.writerow({'Identifier': item.id,
                                     'Title': item.title,
                                     'Date':  item.date,
                                     'Creator': item.reporter,
                                     'Format': 'http://vocab.lib.umd.edu/form#pool_reports',
                                     'Rights Statement': 'http://vocab.lib.umd.edu/rightsStatement#InC-NC',
                                     'FILES': (id+'/'+file_name),
                                     'Object Type': 'http://purl.org/dc/dcmitype/Text',})
                
        # Zip directory
        directory = Path(output_path)
        logger.info(f'Creating zip file for {directory}')

        zip_file_name = (batch_selected_name+'.zip')
        zip_file = Path(directory.parent / zip_file_name)

        with zipfile.ZipFile(zip_file, mode="w") as archive:
            for file_path in directory.rglob("*"):
                archive.write(file_path, arcname=file_path.relative_to(directory))

        with zipfile.ZipFile(zip_file, mode="r") as archive:
            archive.printdir()

# TO DO
# Check that pipes are escaped
