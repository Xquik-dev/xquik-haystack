# SPDX-FileCopyrightText: 2026-present AUTHOR <your@email.com>
#
# SPDX-License-Identifier: Apache-2.0

from haystack import component


# TODO: Rename this class and update the output types and run method to match your use case.
@component
class ExampleComponent:
    """
    A custom Haystack component.

    Usage:
    ```python
    from haystack_integrations.components.example import ExampleComponent

    component = ExampleComponent()
    result = component.run(input_text="Hello, world!")
    ```
    """

    def __init__(self, param: str = "default") -> None:
        """
        Initialize the component.

        :param param: An example parameter.
        """
        self.param = param

    @component.output_types(output=str)
    def run(self, input_text: str) -> dict[str, str]:
        """
        Process the input and return results.

        :param input_text: The text to process.
        :returns: A dictionary with the following keys:
            - `output`: The processed text.
        """
        # TODO: Implement your component logic here.
        result = input_text
        return {"output": result}

    # NOTE: Custom `to_dict` and `from_dict` methods are only needed if the default serialization doesn't work
    # for your component (e.g. it has non-serializable attributes). For details, see:
    # https://docs.haystack.deepset.ai/docs/serialization#default-serialization-behavior
