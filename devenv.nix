{ pkgs, ... }:
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

  enterShell = ''
    export UV_PROJECT_ENVIRONMENT=$(pwd)/.venv
    export UV_PYTHON_DOWNLOADS=never
    export UV_PYTHON_PREFERENCE=system
    export UV_VENV_CLEAR=1
  '';
}
