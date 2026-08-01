# Thesis Structural Reorganization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Riorganizzare la tesi secondo la sequenza problema, materiali, metodologia, risultati, discussione, limitazioni e conclusioni, conservando integralmente il contenuto attuale e aggiungendo una sola introduzione tecnica sulle CNN.

**Architecture:** Il lavoro resta confinato a `professor-report-final.tex`. Si crea prima una copia di controllo, poi si ricompone il documento per blocchi semantici usando le intestazioni LaTeX come confini; figure, tabelle, citazioni e bibliografia viaggiano insieme ai paragrafi che supportano. L'audit finale confronta la versione riorganizzata con la copia iniziale per dimostrare che nessun elemento esistente è andato perso.

**Tech Stack:** LaTeX, `apply_patch`, controlli statici con `rg`, `awk`, `perl`, `cmp`, `stat` e `git check-ignore`.

## Global Constraints

- Modificare soltanto `professor-report-final.tex` per il contenuto della tesi.
- Non compilare e non aggiornare `professor-report-final.pdf`.
- Non modificare gli asset grafici o gli output sperimentali.
- Non cambiare alcun valore numerico o conclusione sperimentale.
- Non eliminare o duplicare contenuti esistenti.
- Conservare tutte le 4 figure, le 20 tabelle e le 20 voci bibliografiche attuali.
- Conservare tutte le 24 label `fig:*` e `tab:*` e i relativi richiami.
- Spostare ogni `\cite{...}` insieme al contenuto che supporta.
- Limitare il nuovo contenuto all'introduzione tecnica sulle CNN, a una sola nuova fonte canonica e ai raccordi editoriali.
- Non aggiungere il file `.tex`, ignorato da Git, all'indice del repository.

---

### Task 1: Congelare l'inventario iniziale

**Files:**
- Read: `professor-report-final.tex`
- Create copy: `/tmp/pneumonia-thesis-reorg-20260801/professor-report-final.before.tex`
- Verify unchanged: `professor-report-final.pdf`

**Interfaces:**
- Consumes: il sorgente completo prima della riorganizzazione.
- Produces: una copia di confronto e i conteggi di baseline usati nel Task 8.

- [ ] **Step 1: Creare la directory temporanea e copiare il sorgente**

Run:

```bash
mkdir -p /tmp/pneumonia-thesis-reorg-20260801
cp -p professor-report-final.tex /tmp/pneumonia-thesis-reorg-20260801/professor-report-final.before.tex
```

Expected: la copia esiste e `cmp` non rileva differenze.

- [ ] **Step 2: Verificare la copia**

Run:

```bash
cmp professor-report-final.tex /tmp/pneumonia-thesis-reorg-20260801/professor-report-final.before.tex
```

Expected: exit code 0, nessun output.

- [ ] **Step 3: Registrare a schermo l'inventario iniziale**

Run:

```bash
awk '/\\begin\{figure\}/{f++} /\\begin\{table\}/{t++} /\\begin\{longtable\}/{lt++} /^\\bibitem\{/{b++} /\\label\{fig:/{fl++} /\\label\{tab:/{tl++} END {print "figures=" f, "tables=" t, "longtables=" lt, "bibitems=" b, "figure_labels=" fl, "table_labels=" tl}' professor-report-final.tex
```

Expected: `figures=4 tables=19 longtables=1 bibitems=20 figure_labels=4 table_labels=20`.

- [ ] **Step 4: Registrare il timestamp del PDF**

Run:

```bash
stat -f '%N | %Sm' -t '%Y-%m-%d %H:%M:%S' professor-report-final.pdf
```

Expected: timestamp `2026-08-01 11:03:11`.

### Task 2: Costruire introduzione, stato dell'arte e obiettivo

**Files:**
- Modify: `professor-report-final.tex:74-98`
- Move from: `professor-report-final.tex:1296-1332`
- Preserve for later placement: `professor-report-final.tex:1334-1352`
- Modify bibliography: `professor-report-final.tex:1409-1535`

**Interfaces:**
- Consumes: l'attuale “Obiettivo”, i primi tre blocchi dello stato dell'arte e le fonti `kermany2018`, `wang2017nih`, `cohen2020limits`, `he2016resnet`, `huang2017densenet`, `tan2019efficientnet`, `howard2019mobilenetv3`, `canziani2016analysis`.
- Produces: sezioni `Introduzione` e `Obiettivo e impostazione del lavoro`, più la nuova chiave `lecun1998gradient`.

- [ ] **Step 1: Inserire la nuova struttura introduttiva dopo l'indice**

Usare esattamente queste intestazioni:

```latex
\section{Introduzione}
\subsection{CNN e imaging medico}
\subsection{Fondamenti delle reti neurali convoluzionali}
\paragraph{Convoluzione e feature map.}
\paragraph{Attivazioni e pooling.}
\paragraph{Normalizzazione, regolarizzazione e classificazione.}
\paragraph{Apprendimento e trasferimento.}
\subsection{Stato dell'arte e generalizzazione cross-dataset}
\section{Obiettivo e impostazione del lavoro}
```

- [ ] **Step 2: Scrivere il paragrafo su CNN e imaging medico**

Il testo deve spiegare che una radiografia è rappresentata come tensore di
intensità, che le CNN sfruttano la struttura spaziale locale e la condivisione
dei pesi, e che negli esami toracici le feature apprese possono evolvere da
bordi e texture a strutture anatomiche e pattern di opacità. Collegare il ruolo
clinico alle fonti già presenti `kermany2018`, `wang2017nih` e
`cohen2020limits`; chiarire che il modello supporta la classificazione del
dataset e non sostituisce il giudizio radiologico.

- [ ] **Step 3: Scrivere i fondamenti tecnici delle CNN**

Includere la notazione della convoluzione discreta:

```latex
\[
z_k(i,j)=b_k+\sum_c\sum_u\sum_v
w_{k,c}(u,v)\,x_c(i+u,j+v),
\]
```

Spiegare kernel, canali, stride, padding e feature map; introdurre la ReLU

```latex
\[
\operatorname{ReLU}(z)=\max(0,z),
\]
```

e distinguere max pooling, average pooling e global average pooling. Descrivere
batch normalization come stabilizzazione delle attivazioni, dropout come
regolarizzazione e i layer fully connected come mappatura finale delle feature.
Spiegare un logit binario con sigmoid e più logit con softmax, senza anticipare
risultati della tesi.

- [ ] **Step 4: Spiegare apprendimento e transfer learning**

Descrivere forward pass, loss, backpropagation e aggiornamento dei pesi; spiegare
che il transfer learning riusa rappresentazioni apprese e può congelare o
riaddestrare diversi blocchi. Collegare questa parte a
`\cite{lecun1998gradient,yosinski2014transferable}` e introdurre il domain shift
come motivazione del confronto RSNA/Kermany/Chittagong, citando
`cohen2020limits`.

- [ ] **Step 5: Spostare lo stato dell'arte generale vicino all'introduzione**

Trasferire senza perdite i paragrafi attuali che iniziano con:

```text
La classificazione automatica di patologie...
Il punto centrale rispetto alla letteratura...
La scelta delle architetture combina...
```

Collocarli nella sottosezione `Stato dell'arte e generalizzazione
cross-dataset`. Le parti che commentano il risultato del temperature scaling e
il posizionamento metodologico restano riservate ai Task 4 e 6.

- [ ] **Step 6: Rinominare e conservare l'obiettivo**

Spostare integralmente l'attuale contenuto di `\section{Obiettivo}` sotto
`\section{Obiettivo e impostazione del lavoro}`. Conservare domanda in quote ed
elenco zero-shot/post-training, senza inserire risultati numerici.

- [ ] **Step 7: Aggiungere la fonte canonica delle CNN**

Inserire in bibliografia:

```latex
\bibitem{lecun1998gradient}
Y. LeCun, L. Bottou, Y. Bengio, P. Haffner.
Gradient-Based Learning Applied to Document Recognition.
\textit{Proceedings of the IEEE}, 86(11):2278--2324, 1998.
\url{https://doi.org/10.1109/5.726791}
```

- [ ] **Step 8: Verificare il nuovo blocco iniziale**

Run:

```bash
rg -n '^\\section\{|^\\subsection\{|^\\paragraph\{' professor-report-final.tex
rg -n -F -e '\cite{lecun1998gradient,yosinski2014transferable}' -e '\bibitem{lecun1998gradient}' professor-report-final.tex
```

Expected: l'introduzione precede l'obiettivo; la nuova citazione e il nuovo
`bibitem` compaiono una volta ciascuno.

### Task 3: Ricomporre la sezione Materiali

**Files:**
- Move and reorganize: `professor-report-final.tex:99-244`

**Interfaces:**
- Consumes: l'attuale sezione Dataset, le figure AP/PA e le tabelle `tab:dataset-summary` e `tab:rsna-multiclass-split`.
- Produces: una sola sezione `Materiali` priva di risultati prestazionali dei modelli.

- [ ] **Step 1: Creare le intestazioni dei materiali**

Usare:

```latex
\section{Materiali}
\subsection{Dataset RSNA adult-oriented}
\subsection{Proiezioni radiografiche AP e PA}
\subsection{Dataset esterni}
\subsection{Split esplorativo multi-classe}
```

- [ ] **Step 2: Collocare RSNA, classi, split e leakage**

Mantenere insieme descrizione RSNA, mappatura `Normal`/`Lung Opacity`, esclusione
della terza classe dal binario, numerosità dello split e controllo a livello di
`patientId`. Non modificare alcun numero.

- [ ] **Step 3: Collocare descrizione e figura AP/PA**

Mantenere definizioni geometriche, fonte `broder2011`, figura
`fig:ap-pa-examples`, numerosità delle proiezioni e limiti dei metadata esterni.
Spostare invece il paragrafo “Implicazioni per l'inferenza” nel Task 4, insieme
al protocollo AP/PA.

- [ ] **Step 4: Collocare dataset esterni e tabella riassuntiva**

Conservare integralmente Kermany, Chittagong e la
`Tabella~\ref{tab:dataset-summary}`.

- [ ] **Step 5: Collocare lo split multi-classe**

Spostare mappatura a tre classi, conteggi bilanciati e
`Tabella~\ref{tab:rsna-multiclass-split}` nella sottosezione dedicata. La frase
sul congelamento delle reti e sulla singola epoca appartiene alla metodologia
multi-classe del Task 4.

- [ ] **Step 6: Verificare i materiali**

Run:

```bash
rg -n -F -e '\section{Materiali}' -e '\label{fig:ap-pa-examples}' -e '\label{tab:dataset-summary}' -e '\label{tab:rsna-multiclass-split}' professor-report-final.tex
```

Expected: tutti e quattro gli elementi sono compresi tra `\section{Materiali}`
e `\section{Metodologia}`.

### Task 4: Costruire la Metodologia senza risultati prestazionali

**Files:**
- Move and reorganize: `professor-report-final.tex:245-378`
- Extract protocol from: `professor-report-final.tex:379-393`
- Extract protocol from: `professor-report-final.tex:452-459`
- Extract protocol from: `professor-report-final.tex:522-558`
- Extract protocol from: `professor-report-final.tex:559-633`
- Extract protocol from: `professor-report-final.tex:633-833`
- Extract protocol from: `professor-report-final.tex:834-880`
- Extract protocol from: `professor-report-final.tex:948-1006`
- Extract protocol from: `professor-report-final.tex:1069-1074`
- Move from state of art: `professor-report-final.tex:1334-1352`

**Interfaces:**
- Consumes: modelli, metriche e tutti i paragrafi procedurali attualmente inseriti nelle sezioni sperimentali.
- Produces: sezione `Metodologia` con protocolli completi e nessuna tabella di risultati.

- [ ] **Step 1: Creare l'indice interno della metodologia**

Usare:

```latex
\section{Metodologia}
\subsection{Architetture confrontate}
\subsubsection{PneumoniaNet}
\subsubsection{Reti di confronto}
\subsection{Protocollo di training e valutazione}
\subsection{Metriche e analisi statistica}
\subsection{Analisi della soglia e calibrazione}
\subsection{Protocolli sperimentali complementari}
\paragraph{Valutazione zero-shot.}
\paragraph{Controllo AP/PA.}
\paragraph{Studio di scaling.}
\paragraph{Estensione multi-classe.}
```

- [ ] **Step 2: Spostare integralmente le descrizioni delle reti**

Mantenere testo e tabella di PneumoniaNet e i quattro paragrafi su ResNet18,
MobileNetV3-Large, EfficientNet-B0 e DenseNet121. Conservare tutte le citazioni
architetturali.

- [ ] **Step 3: Raccogliere il protocollo di training e valutazione**

Spostare qui le frasi esistenti su subset RSNA bilanciato, early stopping,
soglia 0.5, input, inizializzazione e valutazione sui tre dataset. Non spostare
la `tab:benchmark-post-training` né valori di BA/AUC.

- [ ] **Step 4: Spostare metriche e test statistici**

Conservare formula della balanced accuracy, descrizione delle metriche,
bootstrap, McNemar, DeLong e Holm-Bonferroni. Aggiungere qui il paragrafo
esistente dello stato dell'arte che inizia con “L'analisi statistica segue
infine...”, mantenendo le sue citazioni.

- [ ] **Step 5: Spostare soglia, ECE e temperature scaling**

Conservare definizione di soglia Youden oracle, definizione ed equazione ECE,
equal-width/equal-mass, Brier score e procedura di temperature scaling fittata
su RSNA validation. Mantenere nella sezione Risultati tutte le tabelle e ogni
frase che confronta numericamente modelli o dataset.

- [ ] **Step 6: Spostare i protocolli complementari**

Conservare senza risultati:

- elenco dei tre modelli TorchXRayVision;
- pipeline identica per AP e PA e motivazione del controllo;
- definizione delle due famiglie di scaling, parametro `--train-size` e criterio
  del ginocchio;
- adattamento 1-logit/3-logit, caricamento selettivo, congelamento specifico per
  architettura, dataset multi-classe, cross-entropy, softmax, Adam, learning
  rate, risoluzione e singola epoca.

- [ ] **Step 7: Collocare il posizionamento metodologico**

Spostare qui, senza duplicarlo, il contenuto attuale che inizia con “Rispetto
agli studi che si limitano...” e termina con la descrizione dell'estensione
multi-classe alla luce di `yosinski2014transferable`. La frase che dichiara il
risultato della calibrazione va invece nel Task 6.

- [ ] **Step 8: Verificare che non vi siano float di risultati nella metodologia**

Run:

```bash
perl -0777 -e '$s=<>; ($m)=$s=~/\\section\{Metodologia\}(.*?)\\section\{Esperimenti e risultati\}/s; die "metodologia mancante\n" unless defined $m; while ($m =~ /\\label\{((?:fig|tab):[^}]+)\}/g) {print "$1\n"}' professor-report-final.tex
```

Expected: l'unica label ammessa è `tab:pneumonianet-architecture`; non devono
comparire label di tabelle o figure contenenti risultati sperimentali.

### Task 5: Ricomporre Esperimenti e risultati

**Files:**
- Move and reorganize: `professor-report-final.tex:379-1116`

**Interfaces:**
- Consumes: tutte le tabelle, figure, matrici e frasi numeriche delle attuali sezioni sperimentali.
- Produces: una sola sezione `Esperimenti e risultati` con nove sottosezioni ordinate.

- [ ] **Step 1: Creare le nove sottosezioni dei risultati**

Usare nell'ordine:

```latex
\section{Esperimenti e risultati}
\subsection{Valutazione zero-shot e dominio di training}
\subsection{Benchmark post-training}
\subsection{Dimensione, costo computazionale e andamento del training}
\subsection{Controllo della proiezione AP/PA}
\subsection{Analisi della soglia e curve ROC}
\subsection{Calibrazione e temperature scaling}
\subsection{Studio di scaling controllato}
\subsection{Estensione esplorativa multi-classe}
\subsection{Test statistici tra modelli}
```

- [ ] **Step 2: Collocare zero-shot e confronto del training**

Spostare `tab:zero-shot-results`, relativo commento, confronto
Kermany-trained/RSNA-trained, `tab:chittagong-training-comparison` e conclusione
sulla scelta RSNA. Non ripetere l'elenco dei modelli, già in metodologia.

- [ ] **Step 3: Collocare benchmark e costi**

Spostare `tab:benchmark-post-training`, intervalli bootstrap,
`tab:model-cost-training`, relativa interpretazione parametrica/GMAC e
`tab:ba-per-gmac` con il commento costo/prestazione.

- [ ] **Step 4: Collocare controllo AP/PA**

Spostare `tab:view-position-rsna` e tutte le frasi che riportano numerosità per
classe, differenze BA/AUC e limiti della stratificazione. Il protocollo generale
resta in metodologia.

- [ ] **Step 5: Collocare soglia, ROC e calibrazione**

Spostare `tab:threshold-ranking`, `tab:threshold-gap`, `fig:threshold-roc`,
`tab:calibration-ece`, `tab:temperature-scaling` e
`tab:validation-threshold`, insieme a ogni confronto e interpretazione numerica.
Non ripetere formule e definizioni già collocate in metodologia.

- [ ] **Step 6: Collocare lo scaling**

Spostare caveat sui checkpoint, `tab:scaling-pneumonianet`,
`tab:scaling-efficientnet`, `fig:scaling-params`, `fig:scaling-gmac` e relativo
commento. Conservare tutti i valori e i richiami.

- [ ] **Step 7: Collocare il multi-classe**

Spostare `tab:multiclass-summary`, `tab:multiclass-recall`,
`tab:multiclass-confusion-mobilenet` e commento dei risultati. Il protocollo
1-logit/3-logit resta nella metodologia.

- [ ] **Step 8: Collocare i test statistici**

Spostare `tab:paired-tests` e tutte le conclusioni su RSNA, Kermany e
Chittagong. Le definizioni dei test restano nella metodologia.

- [ ] **Step 9: Verificare la copertura dei risultati**

Run:

```bash
perl -0777 -e '$s=<>; ($r)=$s=~/\\section\{Esperimenti e risultati\}(.*?)\\section\{Discussione\}/s; die "risultati mancanti\n" unless defined $r; while ($r =~ /\\label\{((?:fig|tab):[^}]+)\}/g) {$n{$1}++} print scalar(keys %n)." result labels\n"; exit scalar(keys %n) != 20' professor-report-final.tex
```

Expected: `20 result labels`; tre label sono nei Materiali
(`fig:ap-pa-examples`, `tab:dataset-summary`, `tab:rsna-multiclass-split`) e
`tab:pneumonianet-architecture` è nella Metodologia.

### Task 6: Ricomporre Discussione, Limitazioni e Conclusioni

**Files:**
- Move and rename: `professor-report-final.tex:1117-1228`
- Preserve: `professor-report-final.tex:1229-1295`
- Move selected content from: `professor-report-final.tex:1334-1352`
- Rename and preserve: `professor-report-final.tex:1354-1408`

**Interfaces:**
- Consumes: interpretazione, posizionamento rispetto alla letteratura, limitazioni e conclusione operativa.
- Produces: sezioni finali `Discussione`, `Limitazioni`, `Conclusioni` senza duplicazioni.

- [ ] **Step 1: Rinominare Interpretazione in Discussione**

Usare `\section{Discussione}` e conservare i nove paragrafi numerati nello stesso
ordine logico.

- [ ] **Step 2: Integrare il confronto con la letteratura**

Spostare nella discussione le frasi dell'attuale stato dell'arte che commentano
il risultato di calibrazione e il posizionamento empirico del lavoro. Non
ripetere paragrafi già presenti nei nove punti; usare soltanto raccordi per
collocare il testo esistente.

- [ ] **Step 3: Conservare le Limitazioni**

Mantenere l'intero elenco attuale sotto `\section{Limitazioni}`, senza
modificare contenuto o ordine degli item.

- [ ] **Step 4: Rinominare la conclusione**

Sostituire `\section{Conclusione operativa}` con `\section{Conclusioni}` e
conservare tutti i paragrafi fino alla bibliografia.

- [ ] **Step 5: Verificare l'ordine delle sezioni finali**

Run:

```bash
rg -n '^\\section\{(Discussione|Limitazioni|Conclusioni)\}' professor-report-final.tex
```

Expected: tre righe in ordine crescente: Discussione, Limitazioni, Conclusioni.

### Task 7: Verificare bibliografia, citazioni e riferimenti incrociati

**Files:**
- Verify: `professor-report-final.tex`
- Compare: `/tmp/pneumonia-thesis-reorg-20260801/professor-report-final.before.tex`

**Interfaces:**
- Consumes: documento riorganizzato e copia iniziale.
- Produces: evidenza che tutte le fonti e label esistenti sono preservate e risolte.

- [ ] **Step 1: Verificare che nessuna voce bibliografica iniziale sia scomparsa**

Run:

```bash
perl -0777 -e 'sub keys_for {my ($s)=@_; my %h; $h{$1}=1 while $s=~/\\bibitem\{([^}]+)\}/g; return %h} open my $a,"<",$ARGV[0] or die $!; open my $b,"<",$ARGV[1] or die $!; local $/; my $x=<$a>; my $y=<$b>; my %old=keys_for($x); my %new=keys_for($y); for my $k (sort keys %old) {print "missing bibitem $k\n" unless $new{$k}; $bad=1 unless $new{$k}} print "old=".scalar(keys %old)." new=".scalar(keys %new)."\n"; exit($bad//0)' /tmp/pneumonia-thesis-reorg-20260801/professor-report-final.before.tex professor-report-final.tex
```

Expected: `old=20 new=21`, nessuna riga `missing bibitem`.

- [ ] **Step 2: Verificare che tutte le citazioni siano definite**

Run:

```bash
perl -0777 -e '$s=<>; $b{$1}=1 while $s=~/\\bibitem\{([^}]+)\}/g; while ($s=~/\\cite\{([^}]+)\}/g) {for $k (split /,/, $1) {$k=~s/^\s+|\s+$//g; $c{$k}=1}} for $k (sort keys %c) {print "undefined cite $k\n" unless $b{$k}; $bad=1 unless $b{$k}} print "cited=".scalar(keys %c)." defined=".scalar(keys %b)."\n"; exit($bad//0)' professor-report-final.tex
```

Expected: nessuna citazione indefinita, 21 voci definite.

- [ ] **Step 3: Verificare label e riferimenti**

Run:

```bash
perl -0777 -e '$s=<>; while ($s=~/\\label\{((?:fig|tab):[^}]+)\}/g) {$l{$1}++} while ($s=~/\\ref\{((?:fig|tab):[^}]+)\}/g) {$r{$1}++} for $k (sort keys %l) {print "$k labels=$l{$k} refs=".($r{$k}//0)."\n"; $bad=1 if $l{$k}!=1 || !$r{$k}} for $k (keys %r) {$bad=1 unless $l{$k}} exit($bad//0)' professor-report-final.tex
```

Expected: 24 righe, tutte con `labels=1` e `refs>=1`.

### Task 8: Eseguire l'audit finale di struttura e conservazione

**Files:**
- Verify: `professor-report-final.tex`
- Verify unchanged: `professor-report-final.pdf`
- Compare: `/tmp/pneumonia-thesis-reorg-20260801/professor-report-final.before.tex`

**Interfaces:**
- Consumes: tutti i blocchi ricomposti nei Task 2-7.
- Produces: prova finale della struttura, della conservazione degli elementi e dell'assenza di compilazione PDF.

- [ ] **Step 1: Verificare la macrostruttura esatta**

Run:

```bash
rg -n '^\\section\{' professor-report-final.tex
```

Expected, prima della bibliografia:

```text
Introduzione
Obiettivo e impostazione del lavoro
Materiali
Metodologia
Esperimenti e risultati
Discussione
Limitazioni
Conclusioni
```

- [ ] **Step 2: Verificare inventario di float e bibliografia**

Run:

```bash
awk '/\\begin\{figure\}/{f++} /\\begin\{table\}/{t++} /\\begin\{longtable\}/{lt++} /^\\bibitem\{/{b++} /\\label\{fig:/{fl++} /\\label\{tab:/{tl++} END {print "figures=" f, "tables=" t, "longtables=" lt, "bibitems=" b, "figure_labels=" fl, "table_labels=" tl; exit !((f==4)&&(t==19)&&(lt==1)&&(b==21)&&(fl==4)&&(tl==20))}' professor-report-final.tex
```

Expected: `figures=4 tables=19 longtables=1 bibitems=21 figure_labels=4 table_labels=20`.

- [ ] **Step 3: Verificare che caption e blocchi visuali siano invariati**

Run:

```bash
perl -0777 -e 'sub floats {my ($s)=@_; my %h; while ($s=~/(\\begin\{(?:figure|table|longtable)\}.*?\\end\{(?:figure|table|longtable)\})/sg) {$x=$1; $x=~s/\s+/ /g; $h{$x}++} return %h} open my $a,"<",$ARGV[0] or die $!; open my $b,"<",$ARGV[1] or die $!; local $/; my %old=floats(<$a>); my %new=floats(<$b>); for $k (keys %old) {$bad=1 if ($new{$k}//0)!=$old{$k}} print "old_float_variants=".scalar(keys %old)." new_float_variants=".scalar(keys %new)."\n"; exit($bad//0)' /tmp/pneumonia-thesis-reorg-20260801/professor-report-final.before.tex professor-report-final.tex
```

Expected: 24 blocchi visuali equivalenti nella baseline e nel documento finale.

- [ ] **Step 4: Verificare la sintassi statica**

Run:

```bash
awk '{o+=gsub(/\{/,"{"); c+=gsub(/\}/,"}"); d+=gsub(/\$/,"$")} END {print "open_braces=" o, "close_braces=" c, "dollar_signs=" d; exit !((o==c)&&(d%2==0))}' professor-report-final.tex
```

Expected: parentesi bilanciate e numero pari di delimitatori `$`.

- [ ] **Step 5: Verificare che il PDF non sia stato aggiornato**

Run:

```bash
stat -f '%N | %Sm' -t '%Y-%m-%d %H:%M:%S' professor-report-final.tex professor-report-final.pdf
```

Expected: il `.tex` ha un timestamp nuovo; il PDF resta a `2026-08-01 11:03:11`.
