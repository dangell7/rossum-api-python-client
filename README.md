# Rossum Elis Extraction API client

[![PyPI - version](https://img.shields.io/pypi/v/rossum.svg)](https://pypi.python.org/pypi/rossum)
![MIT licence](https://img.shields.io/pypi/l/rossum.svg)
![PyPI - supported python versions](https://img.shields.io/pypi/pyversions/rossum.svg)

The [Elis Extraction API](https://rossum.ai/developers) provides a universal
invoice extraction service based on Artificial Intelligence. Unlike traditional
OCR tools, the robot requires no specific rule or template setup — it is ready
to extract data from a wide variety of invoices right away. This is thanks to
our [deep learning technology](https://rossum.ai/about) that infers the
underlying general structure of invoices.

Our API officially supports English (UK, US and world regions), German (DE
region), Czech and Slovak language invoices, with more languages being added
as we train them. Our model covers the full standard taxonomy of invoice data,
as detailed in our [documentation](https://rossum.ai/developers/api).

## Quickstart

Extracting invoices in 3 lines of code:

```bash
pip install rossum
export ROSSUM_API_KEY="xxxxxxxxxxxxxxxxxxxxxx_YOUR_ELIS_API_KEY_xxxxxxxxxxxxxxxxxxxxxxx"
rossum extract invoice.pdf
```

Let's get into details...

## Installing

Rossum provides a Python package via PyPI:

```
pip install rossum
```

It supports both Python 2 and 3 and uses `requests` and `polling` libraries.

### API key

[Sign-up](https://rossum.ai/developers/) for free the Rossum Elis Extraction API
and obtain an API key.

Set the API key to an environment variable, for example:

```bash
export ROSSUM_API_KEY="xxxxxxxxxxxxxxxxxxxxxx_YOUR_ELIS_API_KEY_xxxxxxxxxxxxxxxxxxxxxxx"
```

*Optional step:* The API base URL defaults to `https://all.rir.rossum.ai`. In case we need to
change it we can set another environment variable, for example:

```bash
export ROSSUM_API_URL="https://cz.rir.rossum.ai"
```

## Features

Upload an invoice and extract fields with text and bounding boxes.

Invoice can be a scanned image in PNG/JPEG/PDF format or a PDF with text.
Extraction output is in JSON. 
Check the [documentation](https://rossum.ai/developers/api/) for details of the
output JSON and see below for a simplified example.

Since version 0.5.0 (2018-10-16) it can read tables!

## Usage examples

This library provides CLI for common tasks and Python API to integrate it with
other code and for more complex use cases.

### Command-line interface

```
usage: rossum extract [-h] [-o OUTPUT] [-l LOCALE] [-f {best,all}]
                      DOCUMENT_PATH

positional arguments:
  DOCUMENT_PATH         Document path (PDF/PNG)

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Path of output JSON (defaults to DOCUMENT_PATH +
                        .json)
  -l LOCALE, --locale LOCALE
                        Locale (eg. en_US)
  --no-tables           Disable extraction of tables
  -f {best,all}, --filter {best,all}
                        select only high-quality subset of extractions or all
                        of them
```

Extract invoice and save the extractions to a JSON file. It sends the input
file and waits for it being processed.

```bash
rossum extract invoice.pdf -o invoice.json

# or other formats 
rossum extract invoice.png -o invoice.json
rossum extract invoice.jpg -o invoice.json
```

In we don't provide the output file name it will be derived from the input by
adding '.json' extension.

```bash
# output saved as invoice.jpg.json
rossum extract invoice.jpg
```

### Python API

Save extracted data to a file.

```
import rossum
rossum.extract('invoice.pdf', 'invoice.json')
```

Extract and invoice and return a dictionary with the results:

```
import rossum
extracted = rossum.extract('invoice.png')
```

Example extracted JSON (shortened for the sake of simplicity):

```json
{
  "status": "ready",
  "language": "ces",
  "currency": "czk",
  "original_pages": [ "https://all.rir.rossum.ai/img/o_1234567890abcdef12345678_0.png" ],
  "preview": "https://all.rir.rossum.ai/img/1234567890abcdef12345678_0.png",
  "previews": [ "https://all.rir.rossum.ai/img/1234567890abcdef12345678_0.png" ],
  "fields": [
    {
      "title": "Total Amount",
      "page": 0,
      "value_type": "number",
      "score": 0.8362206409066133,
      "bbox": [ 1116, 1152, 1200, 1188 ],
      "content": "4 044,60",
      "checks": {},
      "name": "amount_total",
      "value": "4044.60"
    },
    {
      "title": "Variable Symbol",
      "page": 0,
      "value_type": "number",
      "score": 0.9943074548973594,
      "bbox": [ 1077, 426, 1199, 462 ],
      "content": "250100413",
      "checks": {},
      "name": "var_sym",
      "value": "250100413"
    }
  ],
  
  "full_text": {
    "name": "full_text",
    "title": "Rough Content",
    "content": [ "...", "...", "..." ]
  },
  "text_lines": {
    "name": "text_lines",
    "title": "Rough Content",
    "content": [ [ "...", "...", "..." ] ]
  }
}
```

You can specify the API key or base URL in the API client instance (if you can't
pass it via environment variable):

```python
from rossum.extraction import ElisExtractionApi
# just explicit API key
api = ElisExtractionApi('xxx_YOUR_ELIS_API_KEY_xxx')
# or possibly also the endpoint (eg. some testing one)
api = ElisExtractionApi(api_key='xxx_YOUR_ELIS_API_KEY_xxx',
                        base_url='https://some-other.rir.rossum.ai')
extraction = api.extract('invoice.pdf')
```

#### More examples

For example we can easily obtain a table with the extracted fields:

```python
import pandas as pd
df = pd.DataFrame.from_dict(extracted['fields'])
df[['name', 'value']].to_csv('extracted_fields.csv')
```

## About

- Bohumír Zámečník, [Rossum, Ltd.](https://rossum.ai/)
- License: MIT
- Home page of this library: https://github.com/rossumai/rossum-api-python-client
- In case of an issue:
  - https://github.com/rossumai/rossum-api-python-client/issues
  - or contact our support at [support@rossum.ai](mailto:support@rossum.ai) 

Happy invoice extraction!
