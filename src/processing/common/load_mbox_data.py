import hashlib
import logging
import mailbox
import re
from email.header import decode_header, make_header
from email.utils import parsedate_to_datetime

import requests
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile

from processing.models import Batch, File, Item

logger = logging.getLogger(__name__)


# Reporter Processing
reporter_scrub = [
    ', Senior White House Correspondent',
    'via All',
    'EOP/WHO',
]

reporter_extract = re.compile(
    r"""
    ^
    ["\' ]*     # ignore punctuation and whitespace
    (.*?)       # reporter name (minimal match)
    ["\' ]*     # ignore punctuation and whitespace
    (?:\(.+\))? # ignore a title or organization in parentheses
    ["\' ]*     # ignore punctuation and whitespace
    <.*>        # ignore the email address
    $
""",
    re.VERBOSE,
)


def process_reporter(reporter: str) -> str:
    """Build the Reporter field from the message From header."""

    logger.debug(f'reporter: From={reporter}')

    for scrub in reporter_scrub:
        if scrub in reporter:
            reporter = reporter.replace(scrub, '')
            logger.debug(f'reporter: scrubbed "{scrub}": {reporter}')

    if m := reporter_extract.match(reporter):
        s = re.split(r' *, *', m[1])
        if len(s) == 1:
            reporter = s[0]
        else:
            # Change "LastName, FirstName" to "FirstName LastName"
            # Ignore anything after a second comma
            reporter = s[1] + ' ' + s[0]

        logger.debug(f'reporter: extracted: {reporter}')

    return reporter


# Processing Title
title_scrub = [
    '[WH Pool] ',
    '\n',
]


def scrub_title(value: str) -> str:
    """
    Build the Title field from the message Subject header.
    """
    logger.debug(f'title: Subject={value}')

    for scrub in title_scrub:
        if scrub in value:
            value = value.replace(scrub, '')
            logger.debug(f'title: scrubbed "{scrub}": {value}')

    # escape any backslashes and pipe characters
    value = re.sub(r'([\\|])', r'\\\1', value)

    return value


# Body Processing
body_scrub = [
    (
        r'-- \nTo unsubscribe from this group and stop receiving emails from it, send an email to all\+unsubscribe@.*\.com\.',  # noqa
        '',
    ),
    (
        r'-- \<br /\>\nTo unsubscribe from this group and stop receiving emails from it, send an email to \<a href\="mailto\:all\+unsubscribe@.*\.com"\>all\+unsubscribe@.*\.com\</a\>\.\<br /\>',  # noqa
        '',
    ),
]

p_charset = re.compile(r'charset=[a-zA-Z0-9-]+')


def scrub_body(html: str) -> str:
    # Scrub specific string values
    for old, new in body_scrub:
        html = re.sub(old, new, html, re.DOTALL)
        logger.debug(f'body: scrubbed "{old}"')
    # Update the charset since we have convert to utf-8
    html = p_charset.sub('charset=utf-8', html)
    return html


# Determine pool_report to be true or false
# https://docs.python.org/3/library/re.html
# r'\b...\b' is for matching "whole words"
NONPOOL_REPORT_MARKERS = [
    re.compile('[Dd]ear [Cc]olleagues'),
    re.compile('[Hh]ello [Cc]olleagues'),
    re.compile('Colleagues'),
    re.compile('OFF RECORD', re.IGNORECASE),
    re.compile('off the record', re.IGNORECASE),
    re.compile(r'\bFPPO\b'),
    re.compile('non-reportable', re.IGNORECASE),
    re.compile(r'\breportable\b', re.IGNORECASE),
]


def is_pool_report(html: str) -> bool:
    """
    Returns True if the given HTML appears to be pool report, False
    otherwise.
    """
    for marker in NONPOOL_REPORT_MARKERS:
        if marker.search(html):
            return False

    return True


def decode_header_string(header: str) -> str:
    return str(make_header(decode_header(header)))


def load_data(file_path, batch_id):
    batch = Batch(id=batch_id)
    logger.debug(f'Batch ID: {batch_id}')

    for message in mailbox.mbox(file_path):
        item = Item()
        logger.debug(f'{item=}')

        # Date
        date = parsedate_to_datetime(message['Date']).isoformat()
        item.date = date
        logger.debug(date)

        # Reporter
        item.reporter = process_reporter(decode_header_string(message['From']))
        logger.debug(item.reporter)

        # Title
        item.title = scrub_title(decode_header_string(message['Subject']))
        logger.debug(item.title)

        # Body
        for part in message.walk():
            content_type = part.get_content_type()
            if content_type in ('text/html'):
                logger.debug('Found HTML body for message')
                content = part.get_payload(decode=True)
                charset = part.get_content_charset()
                logger.debug(charset)
                if charset is None:
                    charset = 'UTF-8'
                html = content.decode(charset)
            elif content_type in ('text/plain'):
                logger.debug('Found plain text body for message')
                content = part.get_payload(decode=True)
                charset = part.get_content_charset()
                logger.debug(charset)
                if charset is None:
                    charset = 'UTF-8'
                text = content.decode(charset)
                html = f'<html><body><pre>{text}</pre></body></html>'
            elif content_type in (''):
                logger.warning('Unable to find body for message')
                html = ''
        item.body_original = scrub_body(html)

        # Checkboxes
        item.pool_report = is_pool_report(html)
        item.publish = False
        item.off_the_record = False
        item.review_status = False

        # fk
        item.batch = batch

        item.save()

        # Files
        file = File()

        # External images
        external_image_list = []
        html = item.body_original
        soup = BeautifulSoup(html, 'lxml')
        for link in soup.find_all('img'):
            src = link.get('src')
            if src is not None:
                if src.startswith('http'):
                    external_image_list.append(src)

        for external_image in external_image_list:
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept-Language': 'en-US,en;q=0.5',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0',
                'Referer': 'https://www.google.com/',
                'DNT': '1',
            }

            try:
                response = requests.get(external_image, headers=headers, stream=True, timeout=(3.05, 18))
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Failed To Retrieve '{src}'. Connection error: {e}")
            except requests.exceptions.HTTPError as e:
                logger.warning(f"HTTP Error '{src}'. Error: {e}")
            except requests.exceptions.Timeout as e:
                logger.warning(f"Timeout '{src}'. Error: {e}")
            except requests.exceptions.TooManyRedirects as e:
                logger.warning(f"Too Many Redirects '{src}'. Error: {e}")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request Exception '{src}'. Error: {e}")
            else:
                if response.ok:
                    logger.debug(f"Successfully Retrieved '{src}' {response.headers['content-type']}")
                    # filename = os.path.split(src)[1][:100]
                    src_hash = hashlib.md5(src.encode('utf-8')).hexdigest()
                    filename = str(item.id) + '-' + str(src_hash)
                    logger.debug(f'filename: {filename}')
                    content = response.raw.data
                    content_file = ContentFile(content, name=filename)
                    file = File(file=content_file)
                    file.content_type = response.headers['Content-Type']
                    file.disposition = 'external'
                    file.content_id = src
                    file.name = filename
                    file.item = item  # fk
                    file.save()

                    # Replace url and save body with internal link
                    tag = soup.find('img', src)
                    if tag is not None:
                        if filename in tag:
                            new_external_image_src = file.file.url
                            tag['src'] = new_external_image_src
                            item.body_original = str(soup)
                            item.save(update_fields=['body_original'])
                else:
                    logger.warning(f"FAILED to retrieve '{src}'. response={response}")

        # Attachments and Inlines
        for part in message.walk():
            email_filename = part.get_filename()
            if email_filename:
                content_type = part['Content-Type']
                content_disposition = part['Content-Disposition']
                content_id = part['Content-ID']
                content = part.get_payload(decode=True)

                if content_disposition is not None:
                    disposition = re.split(';', content_disposition)[0]
                else:
                    disposition = content_disposition

                content_file = ContentFile(content, name=email_filename)
                file = File(file=content_file)

                file.name = email_filename
                file.content_type = content_type
                file.content_disposition = content_disposition
                file.content_id = content_id
                file.disposition = disposition

                # fk
                file.item = item

                file.save()

                # Inlines

                if content_disposition is not None:
                    file_disposition_type = re.split(';', content_disposition)[0]
                    if file_disposition_type == 'inline':
                        for inline in file_disposition_type:
                            if file.content_id is not None:
                                content_id = str(file.content_id)
                                url = file.file.url

                                image_src_prefix = 'cid:'
                                image_src_id = content_id.strip('<>')
                                image_src = image_src_prefix + image_src_id

                                html = item.body_original
                                soup = BeautifulSoup(html, 'lxml')

                                tag_exists = soup.find('img')
                                if tag_exists is not None:
                                    images = soup.findAll('img')
                                    for image in images:
                                        if image.has_attr('src'):
                                            if image['src'] == image_src:
                                                image['src'] = url
                                                item.body_original = str(soup)
                                                item.save(update_fields=['body_original'])
                                else:
                                    files = File.objects.filter(item=item)
                                    for file in files:
                                        url = file.file.url
                                        inline_image = soup.new_tag('img', src=url)
                                        soup.append(inline_image)
                                        item.body_original = str(soup)
                                        item.save(update_fields=['body_original'])
                            elif file.content_id is None:
                                html = item.body_original
                                url = file.file.url

                                soup = BeautifulSoup(html, 'lxml')
                                inline_image = soup.new_tag('img', src=url)
                                soup.append(inline_image)
                                item.body_original = str(soup)
                                item.save(update_fields=['body_original'])
                elif content_disposition is None:
                    if file.content_id is not None:
                        content_id = str(file.content_id)
                        url = file.file.url

                        image_src_prefix = 'cid:'
                        image_src_id = content_id.strip('<>')
                        image_src = image_src_prefix + image_src_id

                        html = item.body_original
                        soup = BeautifulSoup(html, 'lxml')
                        images = soup.findAll('img')
                        for image in images:
                            if image.has_attr('src'):
                                if image['src'] == image_src:
                                    image['src'] = url
                                    item.body_original = str(soup)
                                    item.save(update_fields=['body_original'])
