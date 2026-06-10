# pymss WebUI

Svelte and Vite browser interface for the pymss music source separation server.

## Development

Install dependencies:

```sh
npm ci
```

Start the development server:

```sh
npm run dev
```

The development server proxies `/health` and `/v1/*` requests to `http://127.0.0.1:8000`.
Start the pymss server separately before using API-backed views:

```sh
pymss serve --host 127.0.0.1 --port 8000
```

## Build

Build static assets:

```sh
npm run build
```

The built files are written to `dist/`. To vendor the WebUI into the Python package,
copy the contents of `dist/` to `pymss/server/webui_static/` in the pymss repository
before building the Python package.
