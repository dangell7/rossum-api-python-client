from __future__ import division, print_function

import json
import os
import sys

import polling
import requests
from tabulate import tabulate

ENV_API_KEY = 'ROSSUM_API_KEY'
ENV_API_URL = 'ROSSUM_API_URL'
DEFAULT_API_URL = 'https://all.rir.rossum.ai'


class ElisExtractionApi(object):
    """
    Simple client for Rossum Elis API that allows to submit a document for
    extraction and then wait for the processed result.

    Usage:

    ```
    import rossum
    extracted = rossum.extract('invoice.pdf')

    # direct usage
    from rossum.extraction import ElisExtractionApi
    client = ElisExtractionApi(api_key, base_url)
    extracted = client.extract('invoice.pdf')
    ```
    """

    def __init__(self, api_key=None, base_url=None):
        if api_key is None:
            if ENV_API_KEY in os.environ:
                api_key = os.environ[ENV_API_KEY]
            else:
                raise MissingApiKeyException(
                    "Please provide API key via `ROSSUM_API_KEY` environment "
                    "variable or `rossum.extraction.Api(api_key)` argument.\n"
                    "You can sign-up for free at https://rossum.ai/developers/#sign-in")
        self.api_key = api_key

        if base_url is None:
            if ENV_API_URL in os.environ:
                base_url = os.environ[ENV_API_URL]
            else:
                base_url = DEFAULT_API_URL
        # base URL should be without the trailing slash
        if base_url.endswith("/"):
            base_url = base_url[:-1]
        self.base_url = base_url

        # we do not use requests.auth.HTTPBasicAuth
        self.headers = {'Authorization': 'secret_key ' + self.api_key}

    def extract(self, document_file, document_path, output_file=None, filter='best', locale=None,
            tables_enabled=True):
        print(document_file)
        print(document_path)
        print(output_file)
        """
        Extracts a document using Elis Extraction API.

        In particular it submits the document, wait for extraction result to be
        ready, optionally save it to a JSON file and return it.

        :param document_file: input document path
        :param output_file: output JSON extraction path (optional)
        :param filter: (optional)
            best - (RECOMMENDED) Retrieves a subset of extracted fields filtered
            for only the high quality data; e.g., lower score fields are
            filtered in favor of higher score ones. The exact set of filters
            applied may change over time.
            all - Returns the complete set of extracted fields, even lower
            quality ones. The client has to post-process the fields appropriately.
        :param locale: (str or None), eg. en_US
            A hint for Elis that may help her to extract certain fields, which may depend on the locale, correctly.
            For example, in US the typical date format is mm.dd.yyyy whilst in Czech it is dd.mm.yyyy.
            So date such as 12. 6. 2018 when locale=cz_CZ is specified is going to be extracted as 12th of June,
            while when locale=en_US is used the date is going to be extracted as 6th of December 2018.
        :param tables_enabled: (bool) indicates that tables should be extracted
        :return: dict with extractions, see the documentation for details
        """
        send_result = self.send_document(document_file, document_path, locale, tables_enabled)
        document_id = send_result['id']
        extraction = self.get_document(document_id, filter=filter, verbose=True)
        if extraction['status'] == 'error':
            raise ValueError(extraction['message'])

        if output_file is not None:
            self._save_extraction(extraction, output_file)

        print('Web preview:', self.document_preview_url(document_id))

        return extraction

    def send_document(self, document_file, document_path, locale=None, tables_enabled=True):
        """
        Submits a document to Elis Extraction API for extractions.

        Returns: dict with 'id' representing job id
        """
        content_type = self._content_type(document_path)
        url = '%s/document' % self.base_url
        params = {}
        if locale:
            params['locale'] = locale
        params['tables'] = 'true' if tables_enabled else 'false'
        files = {'file': (document_path, document_file, content_type)}
        if not document_file:
            with open(document_path, 'rb') as f:
                files = {'file': (os.path.basename(document_path), f, content_type)}
        response = requests.post(url, params=params, files=files, headers=self.headers)
        result = json.loads(response.text)
        if 'error' in result:
            raise ValueError(result['error'])
        return result

    def get_document_status(self, document_id, filter='best', verbose=False):
        """
        Gets a single document status.

        It the status is "ready" the response contains the extraction result.
        """
        if filter not in ['best', 'all']:
            raise ValueError("Filter can be one of {'best', 'all'}, not %s" % filter)

        response = requests.get('%s/document/%s' % (self.base_url, document_id),
                                params={'filter': filter},
                                headers=self.headers)
        response_json = json.loads(response.text)
        status = response_json['status']
        if verbose:
            if status == 'processing':
                print('.', end='')
                sys.stdout.flush()
            elif status == 'ready':
                print(' Done.')
            elif status == 'error':
                print(' Error.')
        return response_json

    def get_document(self, document_id, filter='best', max_retries=120, sleep_secs=5, verbose=False):
        """
        Waits for document to be processed via polling.
        """

        def is_done(response_json):
            return response_json['status'] != 'processing'

        if verbose:
            print('Processing document: ', end='')
            sys.stdout.flush()

        return polling.poll(
            lambda: self.get_document_status(document_id, filter=filter, verbose=verbose),
            check_success=is_done,
            step=sleep_secs,
            timeout=int(round(max_retries * sleep_secs)))

    def document_preview_url(self, document_id):
        return 'https://rossum.ai/document/%s?apikey=%s' % (document_id, self.api_key)

    @staticmethod
    def _save_extraction(extraction, path):
        output_dir = os.path.dirname(path)
        if output_dir != '' and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(path, 'w') as f:
            json.dump(extraction, f, indent=4)

    @staticmethod
    def _content_type(document_path):
        ext = os.path.splitext(document_path)[1].lower()
        if ext == '.png':
            return 'image/png'
        elif ext in ['.jpg', '.jpeg']:
            return 'image/jpeg'
        else:
            return 'application/pdf'


def print_summary(invoice):
    fields = invoice['fields']

    print('Language:', invoice['language'])
    print('Currency:', invoice['currency'])

    def format_field(field):
        return '%s: "%s" (%0.2f %%)' % (field['title'], field['value'], 100 * field['score'])

    for field in sorted(fields, key=lambda f: f['title']):
        if 'value' in field:
            print(format_field(field))
        else:
            print('%s:' % field['title'])
            for inner_field in field['content']:
                print('- ' + format_field(inner_field))

    if 'tables' in invoice:
        print_tables(invoice['tables'])


def print_tables(tables):
    for i, table in enumerate(tables):
        print()
        print('Table %d at page %d' % (i, table['page']))
        rows = table['rows']
        cells = [[cell.get('content', '') for cell in row['cells']] for row in rows]
        has_header = rows[0]['type'] == 'header'
        print(tabulate(cells, headers='firstrow' if has_header else ()))


Api = ElisExtractionApi


class MissingApiKeyException(Exception):
    pass
