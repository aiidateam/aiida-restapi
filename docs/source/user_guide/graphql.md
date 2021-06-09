# GraphQL server (`/graphql`)

The current Graphql schema is:

```{aiida-graphql-schema}
```

## Data Limits and Pagination

...

## Plugins

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

### Nodes

It is important to note, that with GraphQL you specify exactly the fields that you want to retrieve.
It is also important to note, that you are not constrained to one query per request.

```html
http://localhost:5000/api/v4/nodes?id=in=45,56,78
```

```graphql
{
  Nodes(filters: "id IN 45,56,78") {
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
  Nodes {
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
  Nodes {
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
{ Node(uuid: "dee1f869-c45e-40d9-9f9c-f492f4117f13") { uuid } }
```

Partial UUIDs are not yet implemented (but you can also select using `id`).


```html
http://localhost:5000/api/v4/nodes/de83b1/links/incoming?limit=2
```

```graphql
{
  Node(id: 1011) {
    Incoming {
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
  Node(id: 1011) {
    Incoming(filters: "node_type == 'data.dict.Dict.'") {
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
  Node(id: 1011) {
    Outgoing(filters: "node_type == 'data.dict.Dict.'") {
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
{ Node(uuid: "dee1f869-c45e-40d9-9f9c-f492f4117f13") { attributes } }
```


```html
http://localhost:5000/api/v4/nodes/ffe11/contents/attributes?attributes_filter=append_text,is_local
```

```graphql
{ Node(uuid: "dee1f869-c45e-40d9-9f9c-f492f4117f13") { attributes(filter: ["append_text", "is_local"]) } }
```


```html
http://localhost:5000/api/v4/nodes/ffe11/contents/comments
```

```graphql
{
  Node(id: 1011) {
    Comments {
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
  Nodes(filters: "mtime>=2019-04-23") {
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
  Computers {
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
  Computer(uuid: "5d490d77") {
    label
  }
}
```

```html
http://localhost:5000/api/v4/computers/?scheduler_type=in="slurm","pbs"
```

```graphql
{
  Computers(filters: "scheduler_type IN slurm,pbs") {
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
  Computers {
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
  Computers {
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
  Users {
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
  Users(filters: "first_name iLIKE 'aii%'") {
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
  Groups {
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
  Group(id: 1) {
    id
    label
    Nodes {
      count
    }
  }
}
```
