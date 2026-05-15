# Custom Component Template

A template repository for creating custom [Haystack](https://haystack.deepset.ai/) components and publishing them as standalone Python packages.

For more details, see the Haystack documentation on [creating custom components](https://docs.haystack.deepset.ai/docs/custom-components) and [creating custom document stores](https://docs.haystack.deepset.ai/docs/creating-custom-document-stores).

## How to use this template

1. Click **[Use this template](https://github.com/deepset-ai/custom-component/generate)** to create a new repository.

2. **Rename the package directory** from `src/haystack_integrations/components/example/` to match your integration. See [Namespace convention](#namespace-convention) below for the correct path.

3. **Update `pyproject.toml`** — search for `TODO` comments and replace:
   - `name`: your package name, following the `<technology>-haystack` convention (e.g. `opensearch-haystack`)
   - `description`, `authors`, `keywords`, `project.urls`
   - `dependencies`: add your integration-specific dependencies
   - `tool.hatch.version.raw-options`: if you renamed directories, the version path is still derived from git tags so no change is needed here

4. **Add your component code** in the renamed directory and export your classes from `__init__.py`.

5. **Add tests** in `tests/` — see the skeleton in `tests/test_example.py`.

6. **Search for all `TODO` comments** across the project and address them.

Check out the [video walkthrough](https://www.youtube.com/watch?v=SWC0QecAMcI) for a step-by-step guide on how to use this template.

## Namespace convention

Haystack integrations use the `haystack_integrations` namespace package. The directory structure under `src/` determines the import path for your component.

**Components** (converters, embedders, generators, rankers, etc.) use:
```
src/haystack_integrations/components/<type>/<name>/
```
Import path: `from haystack_integrations.components.<type>.<name> import MyComponent`

Common component types: `converters`, `embedders`, `generators`, `rankers`, `retrievers`, `connectors`, `tools`, `websearch`

**Document stores** use a separate namespace:
```
src/haystack_integrations/document_stores/<name>/
```
Import path: `from haystack_integrations.document_stores.<name> import MyDocumentStore`

## Development

This project uses [Hatch](https://hatch.pypa.io/) for build and environment management.

```bash
# Install Hatch
pip install hatch

# Format and lint
hatch run fmt        # auto-fix
hatch run fmt-check  # check only

# Run tests
hatch run test:unit         # unit tests only
hatch run test:integration  # integration tests only
hatch run test:all          # all tests
hatch run test:cov          # with coverage
```

## Publishing to PyPI

This template includes a GitHub Actions workflow that publishes your package to PyPI when you push a version tag.

1. **Add a `PYPI_API_TOKEN` secret** to your repository settings (Settings > Secrets and variables > Actions).

2. **Create a version tag** and push it:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```

The release workflow will build and publish the package automatically.

## License

`Apache-2.0` - See [LICENSE](LICENSE) for details.
