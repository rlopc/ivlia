from openapi_spec_validator import validate
from openapi_spec_validator.validation import OpenAPIV32SpecValidator

from ivlia.api.schemas import openapi_document


def test_openapi_document_is_valid_3_2() -> None:
    document = openapi_document()

    assert document["openapi"] == "3.2.0"
    validate(document, cls=OpenAPIV32SpecValidator)


def test_chat_stream_lists_the_event_union() -> None:
    document = openapi_document()

    content = document["paths"]["/api/chat"]["post"]["responses"]["200"]["content"]
    data = content["text/event-stream"]["itemSchema"]["properties"]["data"]
    union = data["contentSchema"]
    assert data["contentMediaType"] == "application/json"
    assert union["discriminator"]["propertyName"] == "type"
    assert set(union["discriminator"]["mapping"]) == {"token", "end", "error"}
    assert len(union["oneOf"]) == 3


def test_event_union_refs_resolve() -> None:
    # openapi-spec-validator does not follow $ref inside contentSchema.
    document = openapi_document()

    content = document["paths"]["/api/chat"]["post"]["responses"]["200"]["content"]
    union = content["text/event-stream"]["itemSchema"]["properties"]["data"][
        "contentSchema"
    ]
    schemas = document["components"]["schemas"]
    for ref in union["discriminator"]["mapping"].values():
        assert ref.removeprefix("#/components/schemas/") in schemas
