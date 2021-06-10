# GraphQL server (`/graphql`)

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
  Nodes {
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
  Nodes {
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

```
filter: [SPACES] comparison [ AND comparison ]

// Comparisons

comparison: PROPERTY rhs_comparisons [SPACES]

rhs_comparisons: value_op_rhs
    | fuzzy_string_op_rhs
    | length_op_rhs
    | contains_op_rhs
    | is_in_op_rhs
    | has_op_rhs

value_op_rhs: OPERATOR value
fuzzy_string_op_rhs: ILIKE STRING | LIKE STRING
length_op_rhs: [OF] LENGTH DIGITS
contains_op_rhs: CONTAINS valuelist
is_in_op_rhs: [IS] IN valuelist
has_op_rhs: HAS [KEY] ( STRING | PROPERTY )

// Values

value: STRING | FLOAT | INTEGER | PROPERTY | DATE | TIME | DATETIME
valuelist: value (COMMA value)*

// Separators

DOT: "." [SPACES]
COMMA: "," [SPACES]
COLON: ":" [SPACES]
SEMICOLON: ";" [SPACES]
AND: [SPACES] ("AND" | "&") [SPACES]

// Relations

OPERATOR: [SPACES] ( "<" [ "=" ] | ">" [ "=" ] | "!=" | "==" ) [SPACES]

LIKE: [SPACES] "LIKE" [SPACES]
ILIKE: [SPACES] "iLIKE" [SPACES]

OF: [SPACES] "OF" [SPACES]
LENGTH: [SPACES] "LENGTH" [SPACES]
CONTAINS: [SPACES] "CONTAINS" [SPACES]
IS: [SPACES] "IS" [SPACES]
IN: [SPACES] "IN" [SPACES]
HAS: [SPACES] "HAS" [SPACES]
KEY: [SPACES] "KEY" [SPACES]

// Datetime
// minimal implementation of ISO 8601 subset

DATE: DIGIT DIGIT DIGIT DIGIT "-" DIGIT DIGIT "-" DIGIT DIGIT
TIME: DIGIT DIGIT ":" DIGIT DIGIT | DIGIT DIGIT ":" DIGIT DIGIT ":" DIGIT DIGIT
DATETIME: DATE [SPACE] TIME

// Property

%import common.LCASE_LETTER -> LCASE_LETTER
IDENTIFIER: ( LCASE_LETTER | "_" ) ( LCASE_LETTER | "_" | DIGIT )*
PROPERTY: IDENTIFIER ( DOT IDENTIFIER )*

// Strings

%import common._STRING_ESC_INNER -> _STRING_ESC_INNER
STRING: "'" _STRING_ESC_INNER "'" | "\"" _STRING_ESC_INNER "\""

// Numbers

DIGIT: "0".."9"
DIGITS: DIGIT+
%import common.SIGNED_FLOAT
FLOAT: SIGNED_FLOAT
%import common.SIGNED_INT
INTEGER: SIGNED_INT

// White-space

SPACE: /[ \t\f\r\n]/
SPACES: SPACE+
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

  * you select the fields you want to retrieve, and
  * you can combine multiple queries in one request.
 
### Nodes



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
