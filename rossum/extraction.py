from __future__ import division, print_function

from itertools import groupby
import json
import os
import sys

import requests
import polling

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
        self.default_locale = 'en_GB'

        # we do not use requests.auth.HTTPBasicAuth
        self.headers = {'Authorization': 'secret_key ' + self.api_key}

    def extract(self, document_file, output_file=None, filter='best', locale=None):
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
        :param locale: (optional)
            A hint for Elis that may help her to extract certain fields, which may depend on the locale, correctly.
            For example, in US the typical date format is mm.dd.yyyy whilst in Czech it is dd.mm.yyyy.
            So date such as 12. 6. 2018 when locale=cz_CZ is specified is going to be extracted as 12th of June,
            while when locale=en_US is used the date is going to be extracted as 6th of December 2018.
            When passed None, uses self.default_locale.
        :return: dict with extractions, see the documentation for details
        """
        send_result = self.send_document(document_file, locale)
        document_id = send_result['id']
        extraction = self.get_document(document_id, filter=filter, verbose=True)
        if extraction['status'] == 'error':
            raise ValueError(extraction['message'])

        if output_file is not None:
            self._save_extraction(extraction, output_file)

        print('Web preview:', self.document_preview_url(document_id))

        return extraction

    def send_document(self, document_path, locale=None):
        """
        Submits a document to Elis Extraction API for extractions.

        Returns: dict with 'id' representing job id
        """
        if locale is None:
            locale = self.default_locale
        with open(document_path, 'rb') as f:
            content_type = self._content_type(document_path)
            response = requests.post(
                '%s/document?locale=%s' % (self.base_url, locale),
                files={'file': (os.path.basename(document_path), f, content_type)},
                headers=self.headers)
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


def print_summary(invoice, deduplicate=True):
    fields = invoice['fields']
    if deduplicate:
        fields = _deduplicate_fields(fields)

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


def _deduplicate_fields(fields):
    def group_by_key(values, key):
        return groupby(sorted(values, key=lambda f: f[key]), lambda f: f[key])

    def sort_by_score(values):
        return sorted(values, key=lambda f: f['score'])

    def deduplicate_single_value_field(group):
        return [sort_by_score(group)[-1]]

    def deduplicate_multi_value_field(group):
        # multi-value field, only take unique values with best score
        return [sort_by_score(fs)[-1] for (value, fs) in group_by_key(group, 'value')]

    def deduplicate_content(item):
        new_item = item.copy()
        new_item['content'] = deduplicate_fields(item['content'])
        return new_item

    def deduplicate_group(name, group):
        if name == 'tax_details':
            return [deduplicate_content(item) for item in group]
        elif '_addrline' in name:
            return deduplicate_multi_value_field(group)
        else:
            return deduplicate_single_value_field(group)

    def deduplicate_fields(fields):
        return [field
                for (name, group) in group_by_key(fields, 'name')
                for field in deduplicate_group(name, group)]

    return deduplicate_fields(fields)


Api = ElisExtractionApi


class MissingApiKeyException(Exception):
    pass
