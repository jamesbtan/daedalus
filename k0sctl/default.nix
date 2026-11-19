let
  root = builtins.getFlake (toString ../.);
  pkgs = root.inputs.nixpkgs.legacyPackages.${builtins.currentSystem};
in
pkgs.mkShell {
  packages = with pkgs; [
    k0sctl
    kubectl
    k9s
  ];

  shellHook = builtins.readFile ./scripts/shell-hook.sh;
}
