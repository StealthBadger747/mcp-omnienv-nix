{
  description = "mcp-omnienv-nix: MCP server for Nix-backed polyglot ephemeral envs";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.11";

  outputs = {self, nixpkgs}: let
    systems = ["x86_64-linux" "aarch64-linux"];
    forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f system);
  in {
    packages = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
      app = pkgs.python3Packages.buildPythonApplication {
        pname = "mcp-omnienv-nix";
        version = "0.0.1";
        src = self;
        format = "pyproject";
        nativeBuildInputs = [pkgs.python3Packages.hatchling];
        propagatedBuildInputs = [
          pkgs.python3Packages.fastmcp
          pkgs.python3Packages.requests
        ];
      };
    in {
      default = app;
      mcp-omnienv-nix = app;
    });

    defaultPackage = forAllSystems (system: self.packages.${system}.default);

    devShells = forAllSystems (system: let
      pkgs = import nixpkgs {inherit system;};
    in {
      default = pkgs.mkShell {
        packages = [
          pkgs.python312
          pkgs.python3Packages.hatchling
          pkgs.python3Packages.fastmcp
          pkgs.python3Packages.requests
          pkgs.python3Packages.pytest
        ];
      };
    });
  };
}
