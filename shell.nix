{ pkgs ? import <nixpkgs> { } }:

let
  python-with-packages = pkgs.python39.withPackages (ps: with ps; [ poetry ]);
in pkgs.mkShell {
  buildInputs = with pkgs; [ python-with-packages ];
}
