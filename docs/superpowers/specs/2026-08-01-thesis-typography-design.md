# Impostazione tipografica della tesi secondo le indicazioni UniBS

## Obiettivo

Adeguare la sola impaginazione di `professor-report-final.tex` alle indicazioni
fornite dall'Università degli Studi di Brescia, senza modificare il contenuto,
le tabelle, le figure, le citazioni o la bibliografia e senza compilare il PDF.

## Impostazioni approvate

- formato A4;
- Times New Roman come carattere principale;
- corpo del testo di 12 punti;
- titolo principale di 16 punti;
- sottotitolo di 14 punti;
- interlinea 1,5;
- margine superiore di 3 cm;
- margine inferiore di 3 cm;
- margine sinistro di 4 cm, inclusa la rilegatura;
- margine destro di 3 cm;
- testo giustificato.

## Implementazione LaTeX

Il documento manterrà la classe `article` in formato A4, passando da 11 a 12
punti. Il carattere Times New Roman verrà impostato con `fontspec`, coerentemente
con il motore XeTeX usato da Tectonic; le dichiarazioni `inputenc` e `fontenc`,
non necessarie con questo motore, saranno rimosse. L'interlinea verrà gestita
con `setspace` e `\onehalfspacing`; i margini saranno impostati esplicitamente
con `geometry`. Il testo LaTeX è già giustificato per impostazione predefinita,
quindi non verrà introdotto un ambiente che possa interferire con tabelle,
formule o didascalie.

Il titolo di copertina sarà esplicitamente impostato a 16 punti e il sottotitolo
a 14 punti. Le riduzioni locali già presenti nelle tabelle (`\small` e
`\footnotesize`) resteranno invariate: continuano a servire per contenere dati
numerosi senza cambiare il corpo del testo principale.

## Verifica

La verifica sarà esclusivamente statica: presenza delle impostazioni richieste,
bilanciamento degli ambienti LaTeX, conservazione di figure, tabelle, label,
citazioni e bibliografia, e controllo che il timestamp del PDF non cambi.
