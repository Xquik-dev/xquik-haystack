# SPDX-FileCopyrightText: 2026-present AUTHOR <your@email.com>
#
# SPDX-License-Identifier: Apache-2.0

# TODO: Replace these example tests with tests for your own component(s).

from haystack.core.serialization import component_from_dict, component_to_dict

from haystack_integrations.components.example import ExampleComponent


class TestExampleComponent:
    def test_init_default(self):
        component = ExampleComponent()
        assert component.param == "default"

    def test_init_custom_param(self):
        component = ExampleComponent(param="custom")
        assert component.param == "custom"

    def test_run(self):
        component = ExampleComponent()
        result = component.run(input_text="Hello, world!")
        assert result == {"output": "Hello, world!"}

    def test_to_dict(self):
        component = ExampleComponent(param="custom")
        data = component_to_dict(component, "ExampleComponent")
        assert data == {
            "type": "haystack_integrations.components.example.example_component.ExampleComponent",
            "init_parameters": {"param": "custom"},
        }

    def test_from_dict(self):
        data = {
            "type": "haystack_integrations.components.example.example_component.ExampleComponent",
            "init_parameters": {"param": "custom"},
        }
        deserialized = component_from_dict(ExampleComponent, data, "ExampleComponent")
        assert deserialized.param == "custom"
