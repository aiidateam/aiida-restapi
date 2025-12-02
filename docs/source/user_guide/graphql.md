# GraphQL server (`/graphql`)

## What is GraphQL?

From [graphql.org](https://graphql.org/):

> GraphQL is a query language for APIs and a runtime for fulfilling those queries. GraphQL provides a complete and understandable description of the data in your API, gives clients the power to ask for exactly what they need and nothing more.

Features:

- Ask for what you need, get exactly that.
- Get many resources in a single request.
- Describe what’s possible with a clear schema.

## Why GraphQL?

GitHub provided a very concise blog of why they switched to GraphQL: <https://github.blog/2016-09-14-the-github-graphql-api/>

> GraphQL represents a massive leap forward for API development.
> Type safety, introspection, generated documentation, and predictable responses benefit both the maintainers and consumers of our platform.

More so than this, GraphQL maps very well with the data structure of an AiiDA profile,
and makes it very intuitive for clients to construct complex queries, for example:

```graphql
{
  aiidaVersion
  aiidaEntryPointGroups
  nodes(filters: "node_type LIKE '%Calc%' & mtime >= 2018-02-01") {
    count
    rows(limit: 10, offset: 10) {
      uuid
      node_type
      mtime
      incoming {
        count
      }
      outgoing {
        count
      }
    }
  }
}
```

````{dropdown} Example response

```json
{
  "data": {
    "aiidaVersion": "1.6.3",
    "aiidaEntryPointGroups": [
      "aiida.calculations",
      "aiida.cmdline.data",
      "aiida.cmdline.data.structure.import",
      "aiida.cmdline.computer.configure",
      "aiida.data",
      "aiida.groups",
      "aiida.node",
      "aiida.parsers",
      "aiida.schedulers",
      "aiida.tools.calculations",
      "aiida.tools.data.orbitals",
      "aiida.tools.dbexporters",
      "aiida.tools.dbimporters",
      "aiida.transports",
      "aiida.workflows"
    ],
    "nodes": {
      "count": 17784,
      "rows": [
        {
          "uuid": "0f487263-999e-42dd-a71a-66ed6c4d39ba",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "mtime": "2018-02-03T07:18:35.129525+01:00",
          "incoming": {
            "count": 8
          },
          "outgoing": {
            "count": 5
          }
        },
        {
          "uuid": "cff1e914-5a34-4930-9429-9dcc6d38feb1",
          "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
          "mtime": "2018-02-03T07:18:35.129813+01:00",
          "incoming": {
            "count": 2
          },
          "outgoing": {
            "count": 3
          }
        },
        {
          "uuid": "2be5f351-6dd7-4a68-9873-4bc1b3b581fb",
          "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
          "mtime": "2018-02-03T07:18:35.129843+01:00",
          "incoming": {
            "count": 2
          },
          "outgoing": {
            "count": 3
          }
        },
        {
          "uuid": "3e4c9793-49f1-4165-85e1-beaba5a1c4f0",
          "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
          "mtime": "2018-02-03T07:18:35.130197+01:00",
          "incoming": {
            "count": 2
          },
          "outgoing": {
            "count": 2
          }
        },
        {
          "uuid": "3c397478-06af-4b76-8de8-a01fa7248d13",
          "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
          "mtime": "2018-02-03T07:18:35.130550+01:00",
          "incoming": {
            "count": 2
          },
          "outgoing": {
            "count": 3
          }
        },
        {
          "uuid": "d872a924-b831-4c91-92a9-59945544cea8",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "mtime": "2018-02-03T07:18:35.130714+01:00",
          "incoming": {
            "count": 8
          },
          "outgoing": {
            "count": 4
          }
        },
        {
          "uuid": "dfe24253-9993-4abd-91c3-8ed0f2a4fd6f",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "mtime": "2018-02-03T07:18:35.131319+01:00",
          "incoming": {
            "count": 7
          },
          "outgoing": {
            "count": 6
          }
        },
        {
          "uuid": "1feace00-7282-481c-bf6c-51659ef5b115",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "mtime": "2018-02-03T07:18:35.131384+01:00",
          "incoming": {
            "count": 8
          },
          "outgoing": {
            "count": 6
          }
        },
        {
          "uuid": "899d7d18-4880-4942-b45b-2885ca341d55",
          "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
          "mtime": "2018-02-03T07:18:35.131482+01:00",
          "incoming": {
            "count": 2
          },
          "outgoing": {
            "count": 1
          }
        },
        {
          "uuid": "483f69f7-1f23-43ce-b9de-1bb5598083f3",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "mtime": "2018-02-03T07:18:35.132315+01:00",
          "incoming": {
            "count": 8
          },
          "outgoing": {
            "count": 6
          }
        }
      ]
    }
  }
}
```

````

## The GraphQL schema

The current Graphql schema is:

```{aiida-graphql-schema}
```

## Data Limits and Pagination

The maximum number of rows of data returned is limited.
To query this limit use:

```graphql
{ rowLimitMax }
```

Use the `offset` option in conjunction with `limit` in order to retrieve all the rows of data over multiple requests. For example, for pages of length 50:

Page 1:

```graphql
{
  nodes {
    count
    rows(limit: 50, offset: 0) {
      attributes
    }
  }
}
```

Page 2:

```graphql
{
  nodes {
    count
    rows(limit: 50, offset: 50) {
      attributes
    }
  }
}
```

## Filtering

The `filters` option for `computers`, `comments`, `groups`, `logs`, `nodes`, and `users`, accepts a `FilterString`, which maps a string to the `filters` input of the `QueryBuilder` (see [the reference table](https://aiida.readthedocs.io/projects/aiida-core/en/v1.6.3/topics/database.html#reference-tables) for more information).

For example:

```graphql
{ nodes(filters: "node_type ILIKE '%Calc%' & mtime >= 2018-02-01") { count } }
```

maps to:

```python
QueryBuilder().append(Node, filters={"node_type": {"ilike": "%Calc%"}, "mtime": {">=": datetime(2018, 2, 1, 0, 0)}}).count()
```

The syntax is defined by the following [EBNF Grammar](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form):

````{dropdown} FilterString Syntax

```{literalinclude} ../../../aiida_restapi/static/filter_grammar.lark
```

````

## Query Plugins

All top-level queries are plugins.

A plugin is defined as a `QueryPlugin` object, which simply includes three items:

- `name`: The name by which to call the query
- `field`: The graphene field to return (see [graphene types reference](https://docs.graphene-python.org/en/latest/types/))
- `resolver`: The function that resolves the field.

For example:

```python
from aiida_restapi.graphql.plugins import QueryPlugin
import graphene as gr

def resolver(parent, info):
  return "halloworld!"

myplugin = QueryPlugin(
  name="myQuery",
  field=gr.String(description="Return some data"),
  resolver=resolver
)
```

Would be called like:

```graphql
{ myQuery }
```

and return:

```json
{
  "myQuery": "halloworld!"
}
```

(TODO: loading plugins as entry points)

## REST Migration Guide

This section helps AiiDA users migrate API calls between the REST API built into `aiida-core` and the GraphQL API of this plugin.

Most of the listed calls are taken from the [aiida-core documentation](https://aiida.readthedocs.io/projects/aiida-core/en/latest/reference/rest_api.html).

### General

```html
http://localhost:5000/api/v4/server/endpoints
```

```html
http://localhost:5000/graphql
```

It is important to note that (in contrast to REST) with GraphQL

- you select the fields you want to retrieve, and
- you can combine multiple queries in one request.

### Nodes

```html
http://localhost:5000/api/v4/nodes?id=in=45,56,78
```

```graphql
{
  nodes(filters: "id IN 45,56,78") {
    count
    rows {
      id
    }
  }
}
```

```
http://localhost:5000/api/v4/nodes?limit=2&offset=8&orderby=-id
```

```graphql
{
  nodes {
    rows(limit: 2, offset: 8, orderBy: "id", orderAsc: false) {
      id
    }
  }
}
```

```
http://localhost:5000/api/v4/nodes?attributes=true&attributes_filter=pbc1
```

```graphql
{
  nodes {
    rows {
      attributes(filter: ["pbc1"])
    }
  }
}
```


```html
http://localhost:5000/api/v4/nodes/full_types
```

Not implemented for GraphQL, please use the REST API for this use case.

```html
http://localhost:5000/api/v4/nodes/download_formats
```

Not implemented for GraphQL, please use the REST API for this use case.


```html
http://localhost:5000/api/v4/nodes/12f95e1c
```

```graphql
{ node(uuid: "dee1f869-c45e-40d9-9f9c-f492f4117f13") { uuid } }
```

Partial UUIDs are not yet implemented (but you can also select using `id`).


```html
http://localhost:5000/api/v4/nodes/de83b1/links/incoming?limit=2
```

```graphql
{
  node(id: 1011) {
    incoming {
      rows(limit: 2) {
        link {
          label
          type
        }
        node {
          id
          label
        }
      }
    }
  }
}
```


```html
http://localhost:5000/api/v4/nodes/de83b1/links/incoming?full_type="data.dict.Dict.|"
```

```graphql
{
  node(id: 1011) {
    incoming(filters: "node_type == 'data.dict.Dict.'") {
      count
      rows {
        link {
          label
          type
        }
        node {
          id
          label
        }
      }
    }
  }
}
```


```html
http://localhost:5000/api/v4/nodes/a67fba41/links/outgoing?full_type="data.dict.Dict.|"
```

```graphql
{
  node(id: 1011) {
    outgoing(filters: "node_type == 'data.dict.Dict.'") {
      count
      rows {
        link {
          label
          type
        }
        node {
          id
          label
        }
      }
    }
  }
}
```


```html
http://localhost:5000/api/v4/nodes/ffe11/contents/attributes
```

```graphql
{ node(uuid: "dee1f869-c45e-40d9-9f9c-f492f4117f13") { attributes } }
```


```html
http://localhost:5000/api/v4/nodes/ffe11/contents/attributes?attributes_filter=append_text,is_local
```

```graphql
{ node(uuid: "dee1f869-c45e-40d9-9f9c-f492f4117f13") { attributes(filter: ["append_text", "is_local"]) } }
```


```html
http://localhost:5000/api/v4/nodes/ffe11/contents/comments
```

```graphql
{
  node(id: 1011) {
    comments {
      count
      rows {
        content
      }
    }
  }
}
```

Repository based queries are not yet implemented:

```html
http://localhost:5000/api/v4/nodes/ffe11/repo/list
```
```html
http://localhost:5000/api/v4/nodes/ffe11/repo/contents?filename="aiida.in"
```


Not implemented for GraphQL, please use the REST API for this use case.

```html
http://localhost:5000/api/v4/nodes/fafdsf/download?download_format=xsf
```



```html
http://localhost:5000/api/v4/nodes?mtime>=2019-04-23
```

```graphql
{
  nodes(filters: "mtime>=2019-04-23") {
    count
    rows {
        uuid
    }
  }
}
```

### Processes

NOT YET IMPLEMENTED

```html
http://localhost:5000/api/v4/processes/8b95cd85/report
http://localhost:5000/api/v4/calcjobs/sffs241j/input_files
```

### Computers

```
http://localhost:5000/api/v4/computers?limit=3&offset=2&orderby=id
```

```graphql
{
  computers {
    count
    rows(limit: 3, offset: 3, orderBy: "id") {
      id
    }
}
```

```html
http://localhost:5000/api/v4/computers/5d490d77
```

```graphql
{
  computer(uuid: "3d09ebd4-4bda-44c1-86c3-530a778911d5") {
    label
  }
}
```
Partial UUIDs are not yet implemented (but you can also select using `id`).

```html
http://localhost:5000/api/v4/computers/?scheduler_type=in="slurm","pbs"
```

```graphql
{
  computers(filters: "scheduler_type IN slurm,pbs") {
    count
    rows {
      scheduler_type
    }
  }
}
```

```html
http://localhost:5000/api/v4/computers?orderby=+name
```

```graphql
{
  computers {
    rows(orderBy: "name") {
      id
    }
  }
}
```

```html
http://localhost:5000/api/v4/computers/page/1?perpage=5
```

```graphql
{
  computers {
    rows(limit: 5) {
      id
    }
  }
}
```

### Users

```html
http://localhost:5000/api/v4/users/
```

```graphql
{
  users {
    count
    rows {
      id
    }
  }
}
```

```html
http://localhost:5000/api/v4/users/?first_name=ilike="aii%"
```

```graphql
{
  users(filters: "first_name ILIKE 'aii%'") {
    count
    rows {
      email
      first_name
      last_name
      institution
    }
  }
}
```

### Groups

```
http://localhost:5000/api/v4/groups/?limit=10&orderby=-user_id
```

```graphql
{
  groups {
    count
    rows(limit: 10, orderBy: "user_id", orderAsc: false) {
      id
    }
  }
}
```

```html
http://localhost:5000/api/v4/groups/a6e5b
```

```graphql
{
  group(uuid: "3d09ebd4-4bda-44c1-86c3-530a778911d5") {
    id
    label
    nodes {
      count
    }
  }
}
```

Partial UUIDs are not yet implemented (but you can also select using `id`).
