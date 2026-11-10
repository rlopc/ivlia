# ivlia

ivlia is a 100 % local personal AI assistant that manages knowledge of any type (notes, documents and other sources) and answers citing where each answer comes from. It runs on the user's Mac (Apple M2 Max, 64 GB), keeps data on the machine unless the user decides otherwise, and is built in small vertical slices with production-level practices from day one.

## Status

Phase 0 is in progress: the full development environment, with every piece of the architecture in its minimal working version and no real functionality.

## Documentation

- Design (in Spanish, to be translated): [docs/00-indice.md](docs/00-indice.md).
- Standards (current tools and practices): [docs/standards/](docs/standards/README.md).

## License

AGPL-3.0-or-later. The full text is in [LICENSE](LICENSE).

## Setup

1. Install [mise](https://mise.jdx.dev/), for example with `brew install mise`.
2. Trust the repository configuration: `mise trust`.
3. Install the tools: `mise install`.
4. Install dependencies and hooks: `just setup` (uses the network).
5. Run every local check: `just check`.

See [docs/standards/repository.md](docs/standards/repository.md) for details.

## Install a release

Only tagged releases are installed for use. Download the wheel and its provenance bundle from a [release](https://github.com/rlopc/ivlia/releases), verify it, and install it with [uv](https://docs.astral.sh/uv/):

```sh
gh release download vX.Y.Z --repo rlopc/ivlia --pattern '*.whl*'
gh attestation verify ivlia-X.Y.Z-py3-none-any.whl --repo rlopc/ivlia \
  --signer-workflow rlopc/ivlia/.github/workflows/release.yml
uv tool install ./ivlia-X.Y.Z-py3-none-any.whl
```

Details: [docs/standards/release.md](docs/standards/release.md).

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
