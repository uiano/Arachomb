let nixpkgs = import <nixpkgs> {};
in
nixpkgs.stdenv.mkDerivation {
	name = "Arachomb";
	buildInputs=[nixpkgs.nodePackages.create-react-app 
	nixpkgs.nodePackages.npm 
	nixpkgs.nodejs-15_x 
	nixpkgs.nodePackages.prettier];
}
