# GraphQL server (`/graphql`)

## What is GraphQL?

From [graphql.org](https://graphql.org/):

> GraphQL is a query language for APIs and a runtime for fulfilling those queries. GraphQL provides a complete and understandable description of the data in your API, gives clients the power to ask for exactly what they need and nothing more

Features:

- Ask for what you need, get exactly that.
- Get many resources in a single request
- Describe what’s possible with a clear schema

## Why GraphQL?

GitHub provided a very concise blog of why they switched to GraphQL: <https://github.blog/2016-09-14-the-github-graphql-api/>

> GraphQL represents a massive leap forward for API development.
> Type safety, introspection, generated documentation, and predictable responses benefit both the maintainers and consumers of our platform.

More so than this, GraphQL maps very well with the data structure of an AiiDA profile,
and makes it very intuitive for clients to construct complex queries, e.g.

```graphql
{
  aiidaVersion
  aiidaEntryPointGroups
  nodes(filters: "node_type LIKE '%Calc%'") {
    count
    rows(limit: 10) {
      uuid
      node_type
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
          "uuid": "9505e71d-60a9-4d0a-ac44-b27ad42c5d66",
          "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
          "incoming": {
            "count": 0
          },
          "outgoing": {
            "count": 0
          }
        },
        {
          "uuid": "6783928c-24a0-43c2-9b70-f48051222c60",
          "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
          "incoming": {
            "count": 0
          },
          "outgoing": {
            "count": 0
          }
        },
        {
          "uuid": "70971dba-dce7-4272-ac52-3c1c5d1749b0",
          "node_type": "process.calculation.calcfunction.CalcFunctionNode.",
          "incoming": {
            "count": 1
          },
          "outgoing": {
            "count": 1
          }
        },
        {
          "uuid": "6af3f8a0-cf0d-4427-8472-f8907acfc87a",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "incoming": {
            "count": 7
          },
          "outgoing": {
            "count": 4
          }
        },
        {
          "uuid": "de98792b-ad78-4817-bf67-84630671e277",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "incoming": {
            "count": 9
          },
          "outgoing": {
            "count": 6
          }
        },
        {
          "uuid": "c00f403f-84f8-433e-90ee-3801e2fa4fd1",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "incoming": {
            "count": 8
          },
          "outgoing": {
            "count": 6
          }
        },
        {
          "uuid": "66738498-ff6b-40c8-a167-b0c6556695a0",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "incoming": {
            "count": 7
          },
          "outgoing": {
            "count": 4
          }
        },
        {
          "uuid": "b0e93972-4782-4908-b593-5fff627b7c93",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "incoming": {
            "count": 9
          },
          "outgoing": {
            "count": 4
          }
        },
        {
          "uuid": "115904df-b621-4b86-afb6-17fab3359d05",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "incoming": {
            "count": 9
          },
          "outgoing": {
            "count": 6
          }
        },
        {
          "uuid": "a4b9d700-33dc-4114-9d0e-2b0afeb89c0b",
          "node_type": "process.calculation.calcjob.CalcJobNode.",
          "incoming": {
            "count": 9
          },
          "outgoing": {
            "count": 4
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

The maximum number of rows of data returned is limited. To find this limit use:

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

The `filters` option for `Computers`, `Groups` `Nodes`, and `Users`, accepts a `FilterString`.
Its syntax is defined by the following [EBNF Grammar](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form):

````{dropdown} FilterString Syntax

```{literalinclude} ../../../aiida_restapi/static/filter_grammar.lark
```

````

## Plugins

All top-level queries are plugins.

...


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

NOT YET SPECIFICALLY IMPLEMENTED
(although this needs further investigation, because full types is basically not documented anywhere)


```html
http://localhost:5000/api/v4/nodes/download_formats
```

NOT YET IMPLEMENTED


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
  computer(uuid: "5d490d77") {
    label
  }
}
```

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
  users(filters: "first_name iLIKE 'aii%'") {
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
  group(uuid: "a6eb") {
    id
    label
    nodes {
      count
    }
  }
}
```
