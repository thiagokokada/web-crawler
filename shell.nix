{ pkgs ? import (fetchTarball
  "https://github.com/nixos/nixpkgs/archive/66f4dc4fd1b47e9e06d0f1bd78faffa51f0cc59c.tar.gz") { }, ...
}:

let
  python-with-packages = pkgs.python38.withPackages (ps: with ps; [ poetry ]);
in pkgs.mkShell {
  buildInputs = with pkgs; [ python-with-packages ];
}
