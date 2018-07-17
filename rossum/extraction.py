from __future__ import division, print_function

import json
import os

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
                raise ValueError("Please provide API key via `ROSSUM_API_KEY` environment "
                                 "variable or `rossum.extraction.Api(api_key)` argument.")
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

    def extract(self, document_file, output_file=None):
        """
        Extracts a document using Elis Extraction API.

        In particular it submits the document, wait for extraction result to be
        ready, optionally save it to a JSON file and return it.

        :param document_file: input document path
        :param output_file: output JSON extraction path (optional)
        :return: dict with extractions, see the documentation for details
        """
        send_result = self.send_document(document_file)
        document_id = send_result['id']
        extraction = self.get_document(document_id)
        if extraction['status'] == 'error':
            raise ValueError(extraction['message'])

        print('OK')

        if output_file is not None:
            self._save_extraction(extraction, output_file)

        print('Web preview:', self.document_preview_url(document_id))

        return extraction

    def send_document(self, document_path):
        """
        Submits a document to Elis Extraction API for extractions.

        Returns: dict with 'id' representing job id
        """
        with open(document_path, 'rb') as f:
            content_type = self._content_type(document_path)
            response = requests.post(
                '%s/document' % self.base_url,
                files={'file': (os.path.basename(document_path), f, content_type)},
                headers=self.headers)
        result = json.loads(response.text)
        if 'error' in result:
            raise ValueError(result['error'])
        return result

    def get_document_status(self, document_id):
        """
        Gets a single document status.

        It the status is "ready" the response contains the extraction result.
        """
        response = requests.get('%s/document/%s' % (self.base_url, document_id), headers=self.headers)
        response_json = json.loads(response.text)
        if response_json['status'] != 'ready':
            print(response_json)
        return response_json

    def get_document(self, document_id, max_retries=30, sleep_secs=5):
        """
        Waits for document to be processed via polling.
        """

        def is_done(response_json):
            return response_json['status'] != 'processing'

        return polling.poll(
            lambda: self.get_document_status(document_id),
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


Api = ElisExtractionApi
