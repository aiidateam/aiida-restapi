# Tutorial

We will demonstrate the usage of the [aiida-restapi](https://github.com/aiidateam/aiida-restapi) package with a few examples.

To follow this tutorial, you need to have [aiida-core](https://github.com/aiidateam/aiida-core) and [aiida-restapi](https://github.com/aiidateam/aiida-restapi) installed. The REST API server should be running. Check the [README.md](https://github.com/aiidateam/aiida-restapi/blob/master/README.md) file from the [aiida-restapi](https://github.com/aiidateam/aiida-restapi) package to know how.

## Authentication

For some of the REST API endpoints, you need an authentication token. Do the following steps:


   1. Go to http://127.0.0.1:8000/docs
   2. Click on "Authorize"
   3. Use username "johndoe@example.com" and password "secret"
   4. Click on "Authorize", then "Close"

To follow the steps in the tutorial below, you can use the Swagger Javascript client, which you can access at http://127.0.0.1:8000/docs

<!--
You will also need a tool to make HTTP requests. Here are two options:

**Option 1: HTTPie command line tool**

Install [HTTPie](https://httpie.io/) by typing in the terminal:

```console
$ pip install httpie
````

Then you can execute the REST API call with

```console
$ http localhost:8000/api/v4/endpoint < request_body
```

where `request_body` is the file containing the request body.

**Option 2: [`requests` python library](https://docs.python-requests.org/en/latest/) (all python approach)**

Here is an example on how to do it in python:

```python
import requests

url = 'http://localhost:8000/api/v4/endpoint'

body = {
   "node_type": "core.int",
   "attributes": {"value": 6},
}

response = requests.post(url, data=body)

print( response.json )
``` -->

## Launching a WorkChain

Here, we show how the REST API can be used to submit a WorkChain process to add two integers.

### Step 1: Post Code Object

Request URL: http://127.0.0.1:8000/nodes
Request Body:
```json
{
   "node_type": "core.code.installed",
   "dbcomputer_id": 2,
   "attributes": {
      "filepath_executable": "/bin/true"
   },
   "label": "test_code"
}
```

Response Body:
```json
{
   "id": 62,
   "uuid": "e590fff6-46e3-4983-bb2b-1f4a335c5836",
   "node_type": "data.core.code.installed.InstalledCode.",
   "process_type": null,
   "label": "test_code",
   "description": "",
   "ctime": "2021-08-14T13:28:07.848515+00:00",
   "mtime": "2021-08-14T13:28:08.134545+00:00",
   "user_id": 1,
   "dbcomputer_id": null,
   "attributes": {
      "filepath_executable": "/bin/true"
   },
   "extras": {
      "_aiida_hash": "72864a25c6ebf290a12d522b8819fb858788bf81730e934dc95ca7a1ff8cce5c"
   }
}
```

### Step 2: Post Integers

We are creating two integers with values 6 and 3. Below is the example for posting an `orm.Int` object with value 6.

Request URL: http://127.0.0.1:8000/nodes

Request Body:
```json
{
   "node_type": "core.int",
   "attributes": {"value": 6},
}
```

Response Body:
```json
{
   "id": 63,
   "uuid": "4a1a5e4c-e6ea-4a85-b407-4989a292b442",
   "node_type": "data.core.int.Int.",
   "process_type": null,
   "description": "",
   "ctime": "2021-08-14T13:31:40.565835+00:00",
   "mtime": "2021-08-14T13:31:40.802201+00:00",
   "user_id": 1,
   "dbcomputer_id": null,
   "attributes": {
      "value": 6
   },
   "extras": {
      "_aiida_hash": "d74556d1d8c2610f7ec28de9c18c57efaca06a0b478875e304f9fe05ac4213d6"
   }
}
```

Similarly, we created another `orm.Int` object of value 3. The retrieved UUID was “29ff3e11-5165-46db-84b0-d85620d0b972”.

### Step 3: Posting Process

After retrieving the UUIDs, the process is submitted at `/processes` endpoint as follows:

   Request URL: http://127.0.0.1:8000/processes

   Request Body:
   ```json
   {
      "label": "report_process",
      "process_entry_point": "aiida.calculations:core.arithmetic.add",
      "inputs": {
         "code.uuid": "e590fff6-46e3-4983-bb2b-1f4a335c5836",
         "x.uuid": "4a1a5e4c-e6ea-4a85-b407-4989a292b442",
         "y.uuid": "29ff3e11-5165-46db-84b0-d85620d0b972",
         "metadata": {
               "description": "job submission with the adding processes."
         }
      }
   }
   ```

   Response Body:
   ```
   {
      "id": 64,
      "uuid": "6bc238e2-0dec-4449-bbe0-3cf181df00eb",
      "node_type": "process.calculation.calcjob.CalcJobNode.",
      "process_type": "aiida.calculations:core.arithmetic.add",
      "label": "",
      "description": "job submission with the adding processes",
      "ctime": "2021-08-14T13:41:39.823818+00:00",
      "mtime": "2021-08-14T13:41:40.975750+00:00",
      "user_id": null,
      "dbcomputer_id": null,
      "attributes": {
         ...
      },
      "extras": {
         "_aiida_hash": "f773c294c242640d3495fb96aeab604ba90935b76cbebe2dad04ef7ead6e37a1"
      }
   }
   ```

### Step 4: Check status

Once the process is submitted, its status can be checked:

Request URL: http://127.0.0.1:8000/processes/64

Response Body:
```
{
   "id": 64,
   "uuid": "6bc238e2-0dec-4449-bbe0-3cf181df00eb",
   "node_type": "process.calculation.calcjob.CalcJobNode.",
   "process_type": "aiida.calculations:core.arithmetic.add",
   "label": "",
   "description": "job submission with the adding processes",
   "ctime": "2021-08-14T23:41:39.823818+10:00",
   "mtime": "2021-08-14T23:41:40.975750+10:00",
   "user_id": 1,
   "dbcomputer_id": 2,
   "attributes": {
      "version": {
         "core": "1.6.4",
         "plugin": "1.6.4"
      },
   ...
      "parser_name": "core.arithmetic.add",
      "prepend_text": "",
      "process_label": "ArithmeticAddCalculation",
      "process_state": "created",
      "input_filename": "aiida.in",
      "output_filename": "aiida.out"
   },
}
```

The process status is reported in `response.json()["attributes"]["process_state"]`.
