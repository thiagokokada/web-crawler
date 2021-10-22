{ poetry2nix ? (import <nixpkgs> { }).poetry2nix }:

poetry2nix.mkPoetryApplication {
  projectDir = ./.;
}
