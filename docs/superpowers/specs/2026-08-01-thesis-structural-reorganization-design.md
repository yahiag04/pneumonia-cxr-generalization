# Riorganizzazione strutturale della tesi

## Obiettivo

Riorganizzare `professor-report-final.tex` secondo una progressione accademica
chiara: identificazione del problema, materiali disponibili, metodologia,
esperimenti e risultati, discussione, limitazioni e conclusioni. La revisione
deve conservare integralmente il materiale attuale e aggiungere soltanto
l'introduzione tecnica sulle CNN richiesta e le frasi di raccordo necessarie.

## Principio conservativo

La riorganizzazione non deve eliminare, duplicare o alterare risultati,
interpretazioni, valori numerici, figure, tabelle, didascalie, label o fonti
esistenti. Il sorgente contiene quattro figure, venti tabelle e venti voci
bibliografiche: tutti questi elementi devono essere ancora presenti al termine
della revisione. I richiami a figure e tabelle già aggiunti devono continuare a
puntare alle stesse label.

Ogni citazione `\cite{...}` deve spostarsi insieme al contenuto che supporta e
tutti i `\bibitem` esistenti devono rimanere nella bibliografia. L'introduzione
tecnica userà le fonti già presenti quando pertinenti. Potranno essere aggiunte
soltanto le fonti generali strettamente necessarie a documentare i fondamenti
delle CNN e il loro impiego nell'imaging medico; nessuna fonte esistente verrà
sostituita.

## Struttura finale

### 1. Introduzione

La nuova introduzione presenterà prima il ruolo dell'imaging medico e della
radiografia toracica, poi i fondamenti tecnici delle CNN. Dovrà spiegare input e
tensori, kernel e convoluzione, stride e padding, feature map, gerarchia delle
feature, funzioni di attivazione, pooling, batch normalization, dropout, global
average pooling, classificatore fully connected, logit, sigmoid e softmax,
funzione di loss, backpropagation, transfer learning e domain shift. Questa
parte definirà i concetti generali senza ripetere le descrizioni specifiche di
PneumoniaNet, ResNet18, MobileNetV3-Large, EfficientNet-B0 e DenseNet121.

Lo stato dell'arte generale sulla classificazione di radiografie toraciche e
sulla generalizzazione cross-dataset verrà spostato vicino all'introduzione. Le
frasi dell'attuale sezione “Stato dell'arte e posizionamento” che commentano
risultati specifici della tesi saranno invece trasferite nella discussione.

### 2. Obiettivo e impostazione del lavoro

Conterrà l'attuale sezione “Obiettivo”, la domanda sperimentale e la distinzione
generale tra valutazione zero-shot e post-training. Non conterrà risultati
numerici.

### 3. Materiali

Raccoglierà i contenuti descrittivi relativi a RSNA, Kermany e Chittagong, la
mappatura delle classi, gli split, il controllo del leakage, le proiezioni AP e
PA e lo split esplorativo multi-classe. Le tabelle con le numerosità dei dataset
resteranno in questa sezione. Le implicazioni operative della proiezione per
l'inferenza verranno collocate nella metodologia, mentre i risultati AP/PA
resteranno nella sezione sperimentale.

### 4. Metodologia

Conterrà esclusivamente descrizioni di procedure e strumenti:

- preprocessing, input e preparazione degli split;
- PneumoniaNet e architetture di confronto;
- protocollo di training e valutazione;
- metriche, intervalli bootstrap e test statistici;
- procedure per soglia di Youden, calibrazione e temperature scaling;
- disegno degli esperimenti zero-shot, post-training, AP/PA, scaling e
  multi-classe.

I paragrafi che oggi presentano insieme protocollo e risultati verranno divisi
senza perdere frasi: la descrizione procedurale andrà nella metodologia e i
valori osservati nella sezione successiva.

### 5. Esperimenti e risultati

Raccoglierà tutti i risultati empirici nel seguente ordine:

1. esperimenti zero-shot e confronto Kermany-trained/RSNA-trained;
2. benchmark post-training su RSNA, Kermany e Chittagong;
3. andamento del training, dimensione e costo computazionale;
4. controllo della proiezione AP/PA;
5. analisi della soglia e curve ROC;
6. calibrazione e temperature scaling;
7. studio di scaling controllato;
8. estensione esplorativa multi-classe;
9. confronti statistici paired.

Tutte le tabelle, le figure e i rispettivi richiami resteranno associati al
risultato che documentano. I dettagli procedurali già descritti nella
metodologia non verranno ripetuti.

### 6. Discussione

Conterrà l'attuale sezione “Interpretazione”, rinominata “Discussione”, e le
parti di “Stato dell'arte e posizionamento” che confrontano i risultati ottenuti
con la letteratura. I nove punti interpretativi resteranno presenti e nello
stesso ordine logico.

### 7. Limitazioni

Conserverà integralmente l'attuale sezione e il suo elenco di limitazioni,
aggiornando soltanto eventuali frasi di raccordo rese necessarie dal nuovo
ordine.

### 8. Conclusioni

Conterrà integralmente l'attuale “Conclusione operativa”, con il titolo reso
coerente con la struttura finale.

## Bibliografia e riferimenti

La bibliografia resterà alla fine del documento. Prima e dopo la
riorganizzazione verranno confrontati gli insiemi delle chiavi bibliografiche
esistenti. Ogni chiave usata da `\cite` dovrà avere un `\bibitem` corrispondente
e nessuna delle venti voci attuali potrà scomparire. Eventuali nuove voci per
l'introduzione tecnica saranno aggiunte in coda e verificate separatamente.

Analogamente, tutte le ventiquattro label `fig:*` e `tab:*` esistenti dovranno
rimanere univoche e richiamate almeno una volta.

## Vincoli operativi

- Modificare soltanto `professor-report-final.tex` per il contenuto della tesi.
- Non compilare e non aggiornare il PDF.
- Non modificare gli asset grafici o gli output sperimentali.
- Non cambiare alcun valore numerico o conclusione sperimentale.
- Non aggiungere nuovi esperimenti, metriche o interpretazioni dei risultati.
- Limitare il nuovo contenuto all'introduzione tecnica e ai raccordi editoriali.

## Verifica finale

La revisione sarà completa quando l'indice segue esattamente la nuova
macrostruttura, nessun valore di prestazione sperimentale appare nelle sezioni
“Materiali” o “Metodologia”, tutti gli elementi attuali sono ancora presenti,
tutte le citazioni sono risolte dalla bibliografia, tutte le label sono univoche
e richiamate, la sintassi statica LaTeX è bilanciata e il timestamp del PDF è
rimasto invariato.
