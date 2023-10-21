import click
from plumbum import local


@click.command()
@click.argument('uifile')
@click.argument('outfile')
def main(uifile, outfile):
	"""Erwartet zwei Argumente\n\n
	UIFILE - Der Name/Pfad der vom QTDesigner erstellten UI-Datei (optional mit Pfadangabe)\n
	OUTFILE - Der Name/Pfad der Ausgabedatei (optional mit Pfadangabe)"""
	pyuic5 = local["pyuic5"]
	pyuic5('-x', uifile, '-o', outfile)

if __name__ == '__main__':
	main()