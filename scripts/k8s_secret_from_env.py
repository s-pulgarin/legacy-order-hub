"""Genera k8s/secret.yaml (no versionado) a partir del .env local.

Uso:  python scripts/k8s_secret_from_env.py [--env .env] [--out k8s/secret.yaml]

Así los secretos viven solo en el .env y en el clúster, nunca en Git
(RNF-02.1). El archivo generado está en .gitignore.
"""

import argparse
import json
from pathlib import Path

from dotenv import dotenv_values

SECRET_KEYS = (
    "SECRET_KEY",
    "POSTGRES_PASSWORD",
    "SEED_ADMIN_PASSWORD",
    "SEED_CLIENT_PASSWORD",
)
REQUIRED = ("SECRET_KEY", "POSTGRES_PASSWORD")


def build_secret_manifest(values: dict) -> str:
    """Devuelve el YAML del Secret `orderhub-secrets` con los valores dados."""
    missing = [key for key in REQUIRED if not values.get(key)]
    if missing:
        raise SystemExit(f"Faltan en el .env: {', '.join(missing)}")
    lines = [
        "# Generado por scripts/k8s_secret_from_env.py. NO versionar.",
        "apiVersion: v1",
        "kind: Secret",
        "metadata:",
        "  name: orderhub-secrets",
        "  namespace: orderhub",
        "type: Opaque",
        "stringData:",
    ]
    for key in SECRET_KEYS:
        # json.dumps produce una cadena entre comillas válida también en YAML.
        lines.append(f"  {key}: {json.dumps(values.get(key) or '')}")
    return "\n".join(lines) + "\n"


def main() -> None:
    """Lee el .env y escribe el manifiesto del Secret."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--env", default=".env")
    parser.add_argument("--out", default="k8s/secret.yaml")
    args = parser.parse_args()

    manifest = build_secret_manifest(dotenv_values(args.env))
    Path(args.out).write_text(manifest, encoding="utf-8")
    print(f"Secret escrito en {args.out} (no lo subas a Git)")


if __name__ == "__main__":
    main()
