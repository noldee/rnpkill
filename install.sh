#!/usr/bin/env bash
# rnpkill installer
# Usage: curl -fsSL https://raw.githubusercontent.com/noldee/rnpkill/main/install.sh | bash

set -euo pipefail

REPO="noldee/rnpkill"
BIN_NAME="rnpkill"

info()  { printf '\033[1;34m==>\033[0m %s\n' "$1"; }
error() { printf '\033[1;31mError:\033[0m %s\n' "$1" >&2; exit 1; }

# ---- 1. Detect OS ----------------------------------------------------------
OS="$(uname -s)"
case "$OS" in
  Linux)  ASSET="rnpkill-linux" ;;
  Darwin) ASSET="rnpkill-macos" ;;
  *) error "Unsupported OS: $OS. On Windows, use install.ps1 instead." ;;
esac

# ---- 2. Resolve version -----------------------------------------------------
# Allow pinning a version: `RNPKILL_VERSION=v0.1.0 bash install.sh`
if [ -n "${RNPKILL_VERSION:-}" ]; then
  VERSION="$RNPKILL_VERSION"
else
  info "Looking up latest release..."
  VERSION="$(curl -fsSL "https://api.github.com/repos/${REPO}/releases/latest" \
    | grep -m1 '"tag_name"' \
    | sed -E 's/.*"tag_name":\s*"([^"]+)".*/\1/')"
  [ -n "$VERSION" ] || error "Could not resolve the latest version. Check your connection or set RNPKILL_VERSION manually."
fi

URL="https://github.com/${REPO}/releases/download/${VERSION}/${ASSET}"
info "Installing rnpkill ${VERSION} for ${OS}..."

# ---- 3. Pick install directory ---------------------------------------------
INSTALL_DIR="${RNPKILL_INSTALL_DIR:-$HOME/.local/bin}"
mkdir -p "$INSTALL_DIR"

# ---- 4. Download -------------------------------------------------------------
TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

if ! curl -fsSL "$URL" -o "$TMP_FILE"; then
  error "Failed to download $URL"
fi

chmod +x "$TMP_FILE"
mv "$TMP_FILE" "$INSTALL_DIR/$BIN_NAME"
trap - EXIT

info "Installed to $INSTALL_DIR/$BIN_NAME"

# ---- 5. Check PATH ------------------------------------------------------------
case ":$PATH:" in
  *":$INSTALL_DIR:"*) ;;
  *)
    SHELL_RC=""
    case "${SHELL:-}" in
      */zsh)  SHELL_RC="$HOME/.zshrc" ;;
      */bash) SHELL_RC="$HOME/.bashrc" ;;
      *)      SHELL_RC="$HOME/.profile" ;;
    esac
    echo "" >> "$SHELL_RC"
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> "$SHELL_RC"
    info "Added $INSTALL_DIR to PATH in $SHELL_RC (restart your shell, or run: export PATH=\"$INSTALL_DIR:\$PATH\")"
    ;;
esac

info "Done! Run 'rnpkill --help' to get started."