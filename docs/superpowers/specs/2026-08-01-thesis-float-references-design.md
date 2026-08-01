# Riferimenti a figure e tabelle della tesi

## Obiettivo

Rendere esplicito nel testo il collegamento con tutte le figure e le tabelle di
`professor-report-final.tex`, seguendo la convenzione normalmente usata nelle
tesi universitarie. Il documento contiene quattro figure, diciannove ambienti
`table` e un ambiente `longtable`, per un totale di venti tabelle.

## Criterio editoriale

Ogni figura e tabella deve avere una `\label` univoca con prefisso `fig:` o
`tab:` e deve essere richiamata almeno una volta mediante `\ref`. Il primo
richiamo viene collocato preferibilmente nel testo che introduce l'elemento,
prima della sua comparsa. Un secondo richiamo nel paragrafo successivo viene
aggiunto soltanto quando serve a discutere valori o conclusioni specifiche.

I richiami useranno la forma `Figura~\ref{...}`, `Tabella~\ref{...}` oppure, per
elementi coordinati, `Figure~\ref{...} e~\ref{...}` e
`Tabelle~\ref{...} e~\ref{...}`. Le espressioni dipendenti dall'impaginazione,
come “la tabella seguente”, “qui sopra” e “qui sotto”, saranno sostituite con il
riferimento numerato.

## Strategia di inserimento

- La figura con gli esempi AP e PA sarà introdotta nel paragrafo che spiega le
  due proiezioni.
- Le tabelle descrittive dei dataset e dei modelli saranno richiamate nelle
  frasi che ne sintetizzano contenuto e funzione.
- Le tabelle sperimentali saranno introdotte prima dei risultati e potranno
  essere richiamate nuovamente nell'interpretazione successiva.
- Le due figure dello studio di scaling saranno richiamate congiuntamente,
  distinguendo chiaramente il grafico rispetto ai parametri da quello rispetto
  ai GMAC.
- Le tre tabelle multi-classe saranno richiamate separatamente per metriche
  aggregate, recall per classe e matrice di confusione.

## Vincoli

- Modificare soltanto `professor-report-final.tex` durante l'intervento sulla
  tesi.
- Non compilare e non aggiornare il PDF.
- Non modificare dati, valori numerici, ordine degli elementi o significato
  delle didascalie.
- Conservare le `\label` e i richiami già corretti, intervenendo solo quando
  servono uniformità o chiarezza.

## Verifica

La revisione è completa quando tutte le quattro figure e le venti tabelle
hanno una `\label` univoca e almeno un richiamo nel testo, nessun riferimento
punta a un'etichetta inesistente, nessuna etichetta è duplicata e il conteggio
di parentesi graffe e delimitatori matematici del sorgente resta bilanciato. La
data di modifica del PDF deve rimanere invariata.
