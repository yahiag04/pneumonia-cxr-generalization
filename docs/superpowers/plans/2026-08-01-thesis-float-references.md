# Thesis Figure and Table References Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Aggiungere riferimenti accademici espliciti a tutte le quattro figure e le venti tabelle di `professor-report-final.tex`.

**Architecture:** L'intervento resta confinato al sorgente LaTeX della tesi. Prima si assegna una label sistematica a ogni elemento, poi si inseriscono i richiami nelle frasi introduttive o interpretative delle rispettive sezioni, infine si esegue un controllo statico globale di label, riferimenti e sintassi.

**Tech Stack:** LaTeX (`figure`, `table`, `longtable`, `\label`, `\ref`), controlli statici con `rg`, `awk` e `perl`.

## Global Constraints

- Modificare soltanto `professor-report-final.tex` per il contenuto della tesi.
- Non compilare e non aggiornare `professor-report-final.pdf`.
- Non modificare numeri, dati, ordine degli elementi o significato delle didascalie.
- Conservare le label esistenti e usare prefissi `fig:` e `tab:` per quelle nuove.
- Ogni figura e tabella deve avere almeno un richiamo testuale esplicito.
- Evitare formule dipendenti dall'impaginazione come “tabella seguente”, “qui sopra” e “qui sotto”.
- Non aggiungere il file `.tex`, attualmente ignorato, all'indice Git.

---

### Task 1: Completare le label di tutti gli elementi

**Files:**
- Modify: `professor-report-final.tex:138-151`
- Modify: `professor-report-final.tex:208-271`
- Modify: `professor-report-final.tex:383-489`
- Modify: `professor-report-final.tex:767-885`
- Modify: `professor-report-final.tex:953-1039`

**Interfaces:**
- Consumes: le caption e le sette label di tabella e due label di figura già presenti.
- Produces: venti label `tab:*` e quattro label `fig:*`, tutte univoche.

- [ ] **Step 1: Inserire le tredici label di tabella mancanti**

  Collocare ogni label immediatamente dopo la rispettiva `\caption` usando questa
  mappatura esatta:

```text
Dataset finali                         -> tab:dataset-summary
Split RSNA multi-classe               -> tab:rsna-multiclass-split
Struttura di PneumoniaNet             -> tab:pneumonianet-architecture
Risultati zero-shot                    -> tab:zero-shot-results
Kermany vs RSNA su Chittagong         -> tab:chittagong-training-comparison
Dimensione/costo/training             -> tab:model-cost-training
BA per GMAC                           -> tab:ba-per-gmac
Scaling PneumoniaNet                  -> tab:scaling-pneumonianet
Scaling EfficientNet                  -> tab:scaling-efficientnet
Metriche multi-classe                 -> tab:multiclass-summary
Recall multi-classe                   -> tab:multiclass-recall
Confusion matrix multi-classe         -> tab:multiclass-confusion-mobilenet
Confronti statistici paired           -> tab:paired-tests
```

- [ ] **Step 2: Inserire le due label di figura mancanti**

```latex
\label{fig:scaling-params}
\label{fig:scaling-gmac}
```

  Collocarle subito dopo le caption dei grafici rispetto ai parametri e ai GMAC.
  Conservare `fig:ap-pa-examples` e `fig:threshold-roc`.

- [ ] **Step 3: Verificare quantità e unicità delle label**

Run:

```bash
perl -ne 'while (/\\label\{((?:fig|tab):[^}]+)\}/g) {$n{$1}++} END {for $k (sort keys %n) {print "$n{$k} $k\n"}; exit grep {$n{$_} != 1} keys %n}' professor-report-final.tex
```

Expected: 24 righe, ciascuna con conteggio `1`, exit code 0.

### Task 2: Inserire i richiami in dataset, modelli e risultati principali

**Files:**
- Modify: `professor-report-final.tex:127-271`
- Modify: `professor-report-final.tex:369-533`

**Interfaces:**
- Consumes: label create nel Task 1 e label esistenti `fig:ap-pa-examples`, `tab:benchmark-post-training`, `tab:view-position-rsna`.
- Produces: richiami a una figura e otto tabelle nella prima metà del documento.

- [ ] **Step 1: Richiamare figura AP/PA e tabelle dei dataset**

  Inserire nel paragrafo AP/PA una frase equivalente a:

```latex
La Figura~\ref{fig:ap-pa-examples} mostra due esempi reali delle proiezioni PA e AP.
```

  Collegare poi le numerosità dei dataset alla
  `Tabella~\ref{tab:dataset-summary}` e lo split a tre classi alla
  `Tabella~\ref{tab:rsna-multiclass-split}`.

- [ ] **Step 2: Richiamare la struttura di PneumoniaNet**

  Concludere la descrizione architetturale con:

```latex
La sequenza dei blocchi e le relative dimensioni sono sintetizzate nella
Tabella~\ref{tab:pneumonianet-architecture}.
```

- [ ] **Step 3: Richiamare le due tabelle zero-shot**

  Introdurre i risultati TorchXRayVision con
  `Tabella~\ref{tab:zero-shot-results}` e il confronto del dominio di training
  con `Tabella~\ref{tab:chittagong-training-comparison}`.

- [ ] **Step 4: Richiamare benchmark, costi e controllo AP/PA**

  Sostituire “La tabella seguente riporta” con
  `La Tabella~\ref{tab:benchmark-post-training} riporta`. Introdurre la tabella
  dei costi con `Tabella~\ref{tab:model-cost-training}` e sostituire il richiamo
  generico nella sottosezione AP/PA con `Tabella~\ref{tab:view-position-rsna}`.

- [ ] **Step 5: Controllare i richiami della prima metà**

Run:

```bash
rg -n -F -e 'fig:ap-pa-examples' -e 'tab:dataset-summary' -e 'tab:rsna-multiclass-split' -e 'tab:pneumonianet-architecture' -e 'tab:zero-shot-results' -e 'tab:chittagong-training-comparison' -e 'tab:benchmark-post-training' -e 'tab:model-cost-training' -e 'tab:view-position-rsna' professor-report-final.tex
```

Expected: ogni label appare nella definizione e in almeno un `\ref`.

### Task 3: Inserire i richiami in soglie, calibrazione ed efficienza

**Files:**
- Modify: `professor-report-final.tex:535-791`

**Interfaces:**
- Consumes: label esistenti dell'analisi di soglia e della calibrazione, più `tab:ba-per-gmac` dal Task 1.
- Produces: richiami a una figura e sei tabelle nella sezione analitica.

- [ ] **Step 1: Introdurre ranking e gap di soglia**

  Chiudere il paragrafo metodologico con un richiamo alla
  `Tabella~\ref{tab:threshold-ranking}`. Prima della tabella del gap inserire una
  frase che distingua il confronto cross-dataset e richiami la
  `Tabella~\ref{tab:threshold-gap}`.

- [ ] **Step 2: Richiamare il grafico ROC**

  Prima dell'ambiente `figure`, collegare cerchi e croci alla
  `Figura~\ref{fig:threshold-roc}` senza ripetere integralmente la didascalia.

- [ ] **Step 3: Richiamare ECE e temperature scaling**

  Collegare le metriche non calibrate alla
  `Tabella~\ref{tab:calibration-ece}` e i risultati post-hoc alla
  `Tabella~\ref{tab:temperature-scaling}`.

- [ ] **Step 4: Rendere espliciti soglia da validation e rapporto BA/GMAC**

  Sostituire “riportato nella tabella seguente” con
  `riportato nella Tabella~\ref{tab:validation-threshold}`. Introdurre il rapporto
  costo/prestazione tramite `Tabella~\ref{tab:ba-per-gmac}`.

- [ ] **Step 5: Controllare i richiami della sezione analitica**

Run:

```bash
rg -n -F -e 'tab:threshold-ranking' -e 'tab:threshold-gap' -e 'fig:threshold-roc' -e 'tab:calibration-ece' -e 'tab:temperature-scaling' -e 'tab:validation-threshold' -e 'tab:ba-per-gmac' professor-report-final.tex
```

Expected: ogni label appare nella definizione e in almeno un `\ref`.

### Task 4: Inserire i richiami in scaling, multi-classe e test statistici

**Files:**
- Modify: `professor-report-final.tex:793-1045`

**Interfaces:**
- Consumes: otto label create nel Task 1.
- Produces: richiami a due figure e sei tabelle nelle sezioni finali dei risultati.

- [ ] **Step 1: Richiamare le tabelle di scaling**

  Prima delle due tabelle, specificare che i valori numerici sono raccolti nelle
  `Tabelle~\ref{tab:scaling-pneumonianet} e~\ref{tab:scaling-efficientnet}`.

- [ ] **Step 2: Richiamare congiuntamente i grafici di scaling**

  Inserire prima delle figure:

```latex
Le Figure~\ref{fig:scaling-params} e~\ref{fig:scaling-gmac} mostrano lo stesso
studio rispettivamente rispetto al numero di parametri e al costo computazionale.
```

  Nel commento successivo richiamare la figura pertinente quando si parla della
  curva quasi piatta rispetto alla capacità.

- [ ] **Step 3: Richiamare le tre tabelle multi-classe**

  Alla fine del protocollo sperimentale indicare che le metriche aggregate sono
  nella `Tabella~\ref{tab:multiclass-summary}`, i recall nella
  `Tabella~\ref{tab:multiclass-recall}` e la matrice di confusione nella
  `Tabella~\ref{tab:multiclass-confusion-mobilenet}`. Nel commento finale usare
  nuovamente i riferimenti solo per collegare i valori discussi alla loro fonte.

- [ ] **Step 4: Richiamare la tabella dei test paired**

  Chiudere il paragrafo introduttivo della sezione statistica con:

```latex
I confronti paired principali sono riportati nella Tabella~\ref{tab:paired-tests}.
```

- [ ] **Step 5: Controllare i richiami delle sezioni finali**

Run:

```bash
rg -n -F -e 'tab:scaling-pneumonianet' -e 'tab:scaling-efficientnet' -e 'fig:scaling-params' -e 'fig:scaling-gmac' -e 'tab:multiclass-summary' -e 'tab:multiclass-recall' -e 'tab:multiclass-confusion-mobilenet' -e 'tab:paired-tests' professor-report-final.tex
```

Expected: ogni label appare nella definizione e in almeno un `\ref`.

### Task 5: Eseguire l'audit statico globale

**Files:**
- Verify: `professor-report-final.tex`
- Verify unchanged: `professor-report-final.pdf`

**Interfaces:**
- Consumes: tutte le label e tutti i richiami inseriti nei Task 1-4.
- Produces: evidenza che nessun elemento è privo di label o riferimento e che il PDF non è stato compilato.

- [ ] **Step 1: Verificare che tutte le label siano richiamate**

Run:

```bash
perl -0777 -e '$s=<>; while ($s =~ /\\label\{((?:fig|tab):[^}]+)\}/g) {$l{$1}++} while ($s =~ /\\ref\{((?:fig|tab):[^}]+)\}/g) {$r{$1}++} for $k (sort keys %l) {print "$k labels=$l{$k} refs=".($r{$k}//0)."\n"; $bad=1 if $l{$k} != 1 || !$r{$k}} for $k (keys %r) {$bad=1 unless $l{$k}} exit($bad // 0)' professor-report-final.tex
```

Expected: 24 righe con `labels=1` e `refs` maggiore o uguale a 1, exit code 0.

- [ ] **Step 2: Verificare il numero di elementi e delle label**

Run:

```bash
awk '/\\begin\{figure\}/{f++} /\\begin\{table\}/{t++} /\\begin\{longtable\}/{lt++} /\\label\{fig:/{fl++} /\\label\{tab:/{tl++} END {print "figures=" f, "tables=" t, "longtables=" lt, "figure_labels=" fl, "table_labels=" tl; exit !((f==4)&&(t==19)&&(lt==1)&&(fl==4)&&(tl==20))}' professor-report-final.tex
```

Expected: `figures=4 tables=19 longtables=1 figure_labels=4 table_labels=20`.

- [ ] **Step 3: Verificare sintassi statica e formule generiche residue**

Run:

```bash
awk '{o+=gsub(/\{/,"{"); c+=gsub(/\}/,"}"); d+=gsub(/\$/,"$")} END {print "open_braces=" o, "close_braces=" c, "dollar_signs=" d; exit !((o==c)&&(d%2==0))}' professor-report-final.tex
rg -n -i 'tabella seguente|figura seguente|qui sopra|qui sotto' professor-report-final.tex
```

Expected: parentesi e dollari bilanciati; il secondo comando non produce righe.

- [ ] **Step 4: Confermare che il PDF non sia stato aggiornato**

Run:

```bash
stat -f '%N | %Sm' -t '%Y-%m-%d %H:%M:%S' professor-report-final.tex professor-report-final.pdf
```

Expected: il timestamp del `.tex` cambia durante l'intervento; quello del PDF resta precedente e invariato.
