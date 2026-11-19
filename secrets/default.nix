let
  root = builtins.getFlake (toString ../.);
  pkgs = root.inputs.nixpkgs.legacyPackages.${builtins.currentSystem};
in
pkgs.mkShell {
  packages = with pkgs; [
    sops
    age
  ];
}
