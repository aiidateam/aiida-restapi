import typing as t

import pydantic as pdt


class SubmittedProcess(pdt.BaseModel):
    """Pydantic model for submitted processes."""

    label: str = pdt.Field(
        '',
        description='The label of the process',
        examples=['My process', 'Test calculation'],
    )
    description: str = pdt.Field(
        '',
        description='The description of the process',
        examples=['This process calculates the sum of two numbers.'],
    )
    entry_point: str = pdt.Field(
        description='The entry point of the process',
        examples=['core.arithmetic.add'],
    )
    inputs: dict[str, t.Any] = pdt.Field(
        description='The inputs of the process',
        examples=[{'x': 1, 'y': 2}],
    )
