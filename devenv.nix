{ pkgs, lib, ... }:
let
  # zest.releaser is not packaged in nixpkgs and is only needed for releasing,
  # so run it isolated with uvx instead of installing it into the project venv.
  zestCommands = [
    "fullrelease"
    "prerelease"
    "release"
    "postrelease"
    "lasttagdiff"
    "longtest"
    "addchangelogentry"
  ];
in
{
  tasks = {
    "bash:backend:install" = {
      exec = ''
        UV_PROJECT_ENVIRONMENT=$(pwd)/.venv
        UV_PYTHON_DOWNLOADS=never
        UV_PYTHON_PREFERENCE=system
        if [[ ! -e instance ]]; then
          make install
          make create-site
        fi
      '';
      before = [
        "devenv:enterShell"
      ];
    };
  };

  languages.python = {
    enable = true;
    package = pkgs.python311;
    uv = {
      enable = true;
      package = pkgs.uv;
    };
  };

  packages = [ pkgs.ruff ];

  scripts = lib.genAttrs zestCommands (name: {
    exec = ''
      exec uvx --from "zest.releaser[recommended]>=9.5.0" ${name} "$@"
    '';
  });

  enterShell = ''
    export UV_PROJECT_ENVIRONMENT=$(pwd)/.venv
    export UV_PYTHON_DOWNLOADS=never
    export UV_PYTHON_PREFERENCE=system
    export UV_VENV_CLEAR=1
    export UV_TOOL_DIR=$(pwd)/.devenv/state/uv-tools
  '';
}
