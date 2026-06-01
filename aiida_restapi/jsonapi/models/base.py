"""This module should reproduce JSON:API v1.1 https://jsonapi.org/format/1.1/"""

from __future__ import annotations

import datetime
import typing as t

import pydantic as pdt


class Meta(pdt.BaseModel):
    """Non-standard meta-information that can not be represented as an attribute or relationship."""

    model_config = pdt.ConfigDict(extra='allow')


class Link(pdt.BaseModel):
    """A link **MUST** be represented as either: a string containing the link's URL or a link object."""

    href: t.Annotated[
        pdt.AnyUrl,
        pdt.Field(
            description="A string whose value is a URI-reference pointing to the link's target.",
            examples=['../{type}/1'],
        ),
    ]
    rel: t.Annotated[
        str | None,
        pdt.Field(
            description="A string indicating the link's relation type. The string **MUST** be  valid link relation "
            'type.',
            examples=['related', 'self'],
        ),
    ] = None
    describedby: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='A link to a description document (e.g. OpenAPI or JSON Schema) for the link target.',
            examples=['../docs/{type}/schema'],
        ),
    ] = None
    title: t.Annotated[
        str | None,
        pdt.Field(
            description='A string which serves as a label for the destination of a link such that it can be used as a '
            'human-readable identifier (e.g., a menu entry).',
            examples=['Resource'],
        ),
    ] = None
    type: t.Annotated[
        str | None,
        pdt.Field(
            description="A string indicating the media type of the link's target.",
            examples=['application/vnd.api+json'],
        ),
    ] = None
    hreflang: t.Annotated[
        str | set[str] | None,
        pdt.Field(
            description="A string or an array of strings indicating the language(s) of the link's target. An array "
            "of strings indicates that the link's target is available in multiple languages. Each string MUST be a "
            'valid language tag.',
            examples=['en', 'en-US', ['en', 'fr']],
        ),
    ] = None
    meta: t.Annotated[
        Meta | None,
        pdt.Field(
            description='A meta object containing non-standard meta-information about the link.',
            examples=[{'timestamp': '2024-01-01T12:00:00Z'}],
        ),
    ] = None


JsonLinkType = t.Union[pdt.AnyUrl, Link, str]


class JsonApi(pdt.BaseModel):
    """An object describing the server's implementation."""

    version: t.Annotated[
        str,
        pdt.Field(
            description='Version of the JSON:API used, whose value is a string indicating the highest JSON:API '
            'version supported.',
            examples=['1.1'],
        ),
    ] = '1.1'
    ext: t.Annotated[
        list[pdt.AnyUrl] | None,
        pdt.Field(
            description='An array of URIs for all applied extensions.',
            examples=['../docs/extensions/ext1'],
        ),
    ] = None
    profile: t.Annotated[
        list[pdt.AnyUrl] | None,
        pdt.Field(
            description='An array of URIs for all applied profiles.',
            examples=['../docs/profiles/profile1'],
        ),
    ] = None
    meta: t.Annotated[
        Meta | None,
        pdt.Field(
            description='A meta object that contains non-standard meta-information.',
            examples=[{'timestamp': '2024-01-01T12:00:00Z'}],
        ),
    ] = None


class BaseToplevelLinks(pdt.BaseModel):
    """A set of Links objects, possibly including pagination."""

    model_config = pdt.ConfigDict(extra='allow')

    self: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='The link that generated the current response document. If a document has extensions '
            'or profiles applied to it, this link **SHOULD** be represented by a link object with the "type" '
            'target attribute specifying the JSON:API media type with all applicable parameters.',
            examples=['../{type}?page=2'],
        ),
    ] = None

    @pdt.model_validator(mode='after')
    def check_additional_keys_are_links(self) -> BaseToplevelLinks:
        for field, value in self:
            if field not in self.model_fields:
                setattr(
                    self,
                    field,
                    pdt.TypeAdapter(t.Optional[JsonLinkType]).validate_python(value),
                )

        return self


class PaginationLinks(pdt.BaseModel):
    """A set of Links objects for pagination."""

    first: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='The first page of data.',
            examples=['../{type}?page=1'],
        ),
    ] = None
    prev: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='The previous page of data.',
            examples=['../{type}?page=1'],
        ),
    ] = None
    next: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='The next page of data.',
            examples=['../{type}?page=3'],
        ),
    ] = None
    last: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='The last page of data.',
            examples=['../{type}?page=10'],
        ),
    ] = None


class ToplevelLinks(BaseToplevelLinks, PaginationLinks):
    """A set of Links objects, possibly including pagination."""

    related: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='A related resource link when the primary data represents a resource relationship.',
            examples=['../{type}/1/related'],
        ),
    ] = None
    describedby: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='A link to a description document (e.g., OpenAPI or JSON Schema) for the current document.',
            examples=['../docs/{type}/schema'],
        ),
    ] = None


class ErrorLinks(pdt.BaseModel):
    """A Links object specific to Error objects."""

    about: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='A link that leads to further details about this particular occurrence of the problem.',
            examples=['../docs/errors/{id}'],
        ),
    ] = None
    type: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='A link that identifies the type of error that this particular error is an instance of.',
            examples=['../docs/errors/types/{type}'],
        ),
    ] = None


class ErrorSource(pdt.BaseModel):
    """An object containing references to the primary source of the error."""

    pointer: t.Annotated[
        str | None,
        pdt.Field(
            description='A JSON Pointer to the value in the request document that caused the error '
            '[e.g. "/data" for a primary data object, or "/data/attributes/title" for a specific attribute]. '
            "This **MUST** point to a value in the request document that exists; if it doesn't, the client "
            '**SHOULD** simply ignore the pointer.',
            examples=['/data/attributes/thing'],
        ),
    ] = None
    parameter: t.Annotated[
        str | None,
        pdt.Field(
            description='A string indicating which URI query parameter caused the error.',
            examples=['node_type', 'direction', 'page'],
        ),
    ] = None
    header: t.Annotated[
        str | None,
        pdt.Field(
            description='A string indicating the name of a single request header which caused the error.',
            examples=['Authorization'],
        ),
    ] = None


class Error(pdt.BaseModel):
    """An error response."""

    id: t.Annotated[
        str | None,
        pdt.Field(
            description='A unique identifier for this particular occurrence of the problem.',
            examples=['{id}'],
        ),
    ] = None
    links: t.Annotated[
        ErrorLinks | None,
        pdt.Field(
            description='An error link object that **MAY** contain the "about" and/or "type" fields.',
            examples=[
                {'about': '../docs/errors/{id}'},
                {'type': '../docs/errors/{type}'},
            ],
        ),
    ] = None
    status: t.Annotated[
        str | None,
        pdt.Field(
            description='The HTTP status code applicable to this problem, expressed as a string value. '
            'This **SHOULD** be provided.',
        ),
    ] = None
    code: t.Annotated[
        str | None,
        pdt.Field(
            description='An application-specific error code, expressed as a string value.',
        ),
    ] = None
    title: t.Annotated[
        str | None,
        pdt.Field(
            description='A short, human-readable summary of the problem that **SHOULD NOT** change from occurrence to '
            'occurrence of the problem, except for purposes of localization.',
        ),
    ] = None
    detail: t.Annotated[
        str | None,
        pdt.Field(
            description='A human-readable explanation specific to this occurrence of the problem. '
            "Like title, this field's value can be localized.",
        ),
    ] = None
    source: t.Annotated[
        ErrorSource | None,
        pdt.Field(
            description='An object containing references to the primary source of the error. '
            'It **SHOULD** include one of "pointer", "parameter", and/or "header".',
            examples=[{'pointer': '/data/attributes/thing'}],
        ),
    ] = None
    meta: t.Annotated[
        Meta | None,
        pdt.Field(
            description='A meta object containing non-standard meta-information about the error.',
            examples=[{'timestamp': '2024-01-01T12:00:00Z'}],
        ),
    ] = None

    @pdt.model_validator(mode='after')
    def at_least_one_error_field(self) -> Error:
        if not any(getattr(self, field) is not None for field in self.model_fields):
            raise ValueError('At least one of the error fields must be provided')
        return self

    def __hash__(self) -> int:
        return hash(self.model_dump_json())


ErrorType = t.TypeVar('ErrorType', bound=Error)


def resource_json_schema_extra(schema: dict[str, t.Any], model: type[BaseResource]) -> None:
    """Ensure "id" and "type" are the first two entries in the list required properties.

    Note:
        This _requires_ that "id" and "type" are the _first_ model fields defined
        for all sub-models of "BaseResource".

    """
    if 'id' not in schema.get('required', []):
        schema['required'] = ['id'] + schema.get('required', [])
    if 'type' not in schema.get('required', []):
        required = []
        for field in schema.get('required', []):
            required.append(field)
            if field == 'id':
                # To make sure the property order match the listed properties,
                # this ensures "type" is added immediately after "id".
                required.append('type')
        schema['required'] = required


class BaseResource(pdt.BaseModel):
    """Minimum requirements to represent a Resource."""

    model_config = pdt.ConfigDict(json_schema_extra=resource_json_schema_extra)

    id: t.Annotated[
        str,
        pdt.Field(
            description='Resource ID.',
            examples=['1'],
        ),
    ]
    type: t.Annotated[
        str,
        pdt.Field(
            description='Resource type.',
            examples=['{type}'],
        ),
    ]


class RelationshipLinks(pdt.BaseModel):
    """A resource object **MAY** contain references to other resource objects ("relationships").
    Relationships may be to-one or to-many.
    Relationships can be specified by including a member in a resource's links object.
    """

    self: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='A link for the relationship itself (a "relationship link"). This link allows the client to '
            'directly manipulate the relationship. When fetched successfully, this link returns the linkage for the '
            'related resources as its primary data.',
            examples=['../{type}/1/relationships/related'],
        ),
    ] = None
    related: t.Annotated[
        JsonLinkType | None,
        pdt.Field(
            description='A related resource link.',
            examples=['../{type}/1/related'],
        ),
    ] = None

    @pdt.model_validator(mode='after')
    def either_self_or_related_must_be_specified(self) -> RelationshipLinks:
        if self.self is None and self.related is None:
            raise ValueError("Either 'self' or 'related' MUST be specified for RelationshipLinks")
        return self


class Relationship(pdt.BaseModel):
    """Representation references from the resource object in which it's defined to other resource objects."""

    links: t.Annotated[
        RelationshipLinks | None,
        pdt.Field(
            description='A links object containing at least one of the following: `self`, `related`.',
            examples=[
                {'self': '../{type}/1/relationships/related'},
                {'related': '../{type}/1/related'},
            ],
        ),
    ] = None
    meta: t.Annotated[
        Meta | None,
        pdt.Field(
            description='A meta object that contains non-standard meta-information about the relationship.',
            examples=[{'timestamp': '2024-01-01T12:00:00Z'}],
        ),
    ] = None
    data: t.Annotated[
        BaseResource | list[BaseResource] | None,
        pdt.Field(
            description='Resource linkage',
        ),
    ] = None

    @pdt.model_validator(mode='after')
    def at_least_one_relationship_key_must_be_set(self) -> Relationship:
        if self.links is None and self.data is None and self.meta is None:
            raise ValueError("Either 'links', 'data', or 'meta' MUST be specified for Relationship")
        return self


class Relationships(pdt.RootModel[dict[str, Relationship]]):
    """
    Members of the relationships object ("relationships") represent references
    from the resource object in which it's defined to other resource objects.
    Keys **MUST NOT** be:
    - id
    - type
    """

    root: dict[str, Relationship]

    @pdt.model_validator(mode='after')
    def check_illegal_relationships_fields(self) -> Relationships:
        illegal_fields = {'id', 'type'}
        overlap = illegal_fields.intersection(self.root.keys())
        if overlap:
            raise ValueError(f'{sorted(overlap)} MUST NOT be members under Relationships')
        return self


class ResourceLinks(pdt.BaseModel):
    """A Resource Links object"""

    self: t.Annotated[
        JsonLinkType,
        pdt.Field(
            description='A link that identifies the resource represented by the resource object.',
            examples=['../{type}/1'],
        ),
    ]


class Attributes(pdt.BaseModel):
    """
    Members of the attributes object ("attributes") represent information about
    the resource object in which it's defined.
    The keys for Attributes **MUST NOT** be:
    - relationships
    - links
    - id
    - type
    """

    model_config = pdt.ConfigDict(extra='allow')

    @pdt.model_validator(mode='after')
    def check_illegal_attributes_fields(self) -> Attributes:
        illegal_fields = ('relationships', 'links', 'id', 'type')
        for field in illegal_fields:
            if hasattr(self, field):
                raise ValueError(f'{illegal_fields} MUST NOT be fields under Attributes')
        return self


AttributesType = t.TypeVar('AttributesType', bound=Attributes)


class Resource(BaseResource, t.Generic[AttributesType]):
    """A resource objects of a JSON API document representing resources."""

    links: t.Annotated[
        ResourceLinks | None,
        pdt.Field(
            description='A links object containing links related to the resource.',
            examples=[{'self': '../{type}/1'}],
        ),
    ] = None
    meta: t.Annotated[
        Meta | None,
        pdt.Field(
            description='A meta object containing non-standard meta-information about a resource that can not be '
            'represented as an attribute or relationship.',
            examples=[{'timestamp': '2024-01-01T12:00:00Z'}],
        ),
    ] = None
    attributes: t.Annotated[
        AttributesType | None,
        pdt.Field(
            description="An attributes object representing some of the resource's data.",
        ),
    ] = None
    relationships: t.Annotated[
        Relationships | None,
        pdt.Field(
            description='Relationships object describing relationships between the resource and other JSON:API '
            'resources.',
        ),
    ] = None


ResourceType = t.TypeVar('ResourceType', bound=Resource)


def datetime_encoder(value: datetime.datetime) -> str:
    """Encode datetime in UTC ISO 8601 format for JSON:API compliance."""
    return value.astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


class JsonApiBaseDocument(pdt.BaseModel):
    """Common JSON:API top-level members shared by success and error documents."""

    model_config = pdt.ConfigDict(json_encoders={datetime.datetime: datetime_encoder})

    jsonapi: t.Annotated[
        JsonApi,
        pdt.Field(
            description="An object describing the server's implementation.",
        ),
    ] = JsonApi()
    meta: t.Annotated[
        Meta | None,
        pdt.Field(
            description='A meta object that contains non-standard meta-information.',
            examples=[{'timestamp': '2024-01-01T12:00:00Z'}],
        ),
    ] = None


class JsonApiResourceDocument(JsonApiBaseDocument, t.Generic[ResourceType]):
    """A top-level JSON:API document for successful single resource responses."""

    links: t.Annotated[
        ToplevelLinks | None,
        pdt.Field(
            description='A links object related to the document as a whole.',
        ),
    ] = None
    data: t.Annotated[
        ResourceType,
        pdt.Field(
            description='The document\'s "primary data".',
        ),
    ]
    included: t.Annotated[
        list[Resource] | None,
        pdt.Field(
            description='An array of resource objects that are related to the primary data and/or each other '
            '("included data").',
        ),
    ] = None

    @pdt.model_validator(mode='after')
    def _no_included_without_data(self) -> JsonApiResourceDocument[ResourceType]:
        if self.included is not None and self.data is None:
            raise ValueError("'included' must not be present without 'data' being present")
        return self


class JsonApiCollectionDocument(JsonApiResourceDocument, t.Generic[ResourceType]):
    """A top-level JSON:API document for successful resource collection responses."""

    data: t.Annotated[
        list[ResourceType],
        pdt.Field(
            description="The document's 'primary data'.",
        ),
    ]


class JsonApiErrorDocument(JsonApiBaseDocument, t.Generic[ErrorType]):
    """A top-level JSON:API document for error responses."""

    links: t.Annotated[
        BaseToplevelLinks | None,
        pdt.Field(
            description='A links object related to the document as a whole.',
            examples=[{'self': '../{type}/1'}],
        ),
    ] = None
    errors: t.Annotated[
        list[ErrorType],
        pdt.Field(
            description='An array of error objects.',
        ),
    ]

    @pdt.model_validator(mode='after')
    def _non_empty_errors(self) -> JsonApiErrorDocument:
        if not self.errors:
            raise ValueError("'errors' must not be empty")
        return self
