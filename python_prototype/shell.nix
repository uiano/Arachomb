{ pkgs ? import <nixpkgs> {}}:
pkgs.mkShell {
	buildInputs = [
		(pkgs.python38.withPackages (ps: [ps.beautifulsoup4 ps.trio ps.httpx]))
		];
}
