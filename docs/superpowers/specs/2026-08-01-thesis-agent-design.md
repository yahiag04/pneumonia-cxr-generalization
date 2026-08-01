# Thesis Agent: agente verificabile per la ricerca universitaria

## Visione e obiettivo

`thesis-agent` sarà una CLI open source, local-first e generalista per condurre
una ricerca universitaria dall'impostazione della domanda fino alla bozza e al
controllo finale. Dovrà anche importare e revisionare tesi esistenti in Markdown
o LaTeX. Il sistema potrà generare testo completo, ma ogni affermazione
sostanziale dovrà essere collegata a evidenze acquisite e approvate; i contenuti
non supportati saranno segnalati e non completati silenziosamente.

Il progetto sarà pubblicato in un repository Python autonomo. Questo repository
sulla classificazione della polmonite conserverà la specifica e fornirà un caso
di studio anonimizzato, ma non sarà una dipendenza del nuovo pacchetto.

## Utenti e casi d'uso

La prima release è rivolta a studenti e ricercatori che lavorano da terminale e
che desiderano un processo riproducibile, non un ghostwriter autonomo. Deve
supportare due percorsi completi:

1. creare una ricerca partendo da domanda, disciplina e criteri di selezione;
2. importare una tesi Markdown/LaTeX, ricostruirne struttura e citazioni,
   proseguire la ricerca e proporre revisioni tracciabili.

L'utente approva fonti, matrice delle evidenze, scaletta, bozza e correzioni
proposte dall'audit. Il relatore e l'autore mantengono la responsabilità finale.

## Principi di progetto

- **Evidence-first:** nessuna citazione viene generata prima dell'acquisizione e
  della verifica della fonte.
- **Provenienza esplicita:** ogni affermazione generata rimanda agli identificativi
  delle evidenze e alle chiavi bibliografiche utilizzate.
- **Pipeline riprendibile:** ogni fase produce artefatti persistenti e può essere
  rieseguita senza ricominciare il progetto.
- **Local-first:** stato, documenti, cache e log restano locali; la modalità
  offline blocca tutte le chiamate esterne.
- **Provider-agnostic:** fonti, modelli e formati dipendono da interfacce stabili,
  non dalla logica centrale.
- **Controllo umano:** le transizioni che influenzano corpus, struttura o testo
  richiedono un'approvazione registrata. In modalità non interattiva il comando
  può consumare un manifesto di approvazione preparato dall'utente, ma non può
  generarlo o approvarlo autonomamente.
- **Originali immutabili:** i documenti importati non vengono sovrascritti.

## Architettura

Il sistema è suddiviso in quattro livelli:

```text
CLI
  -> orchestratore della pipeline
      -> servizi di dominio
          -> adattatori per fonti, LLM, embeddings, documenti ed export
```

### CLI

La CLI espone i comandi `init`, `import`, `research`, `evidence`, `outline`,
`draft`, `audit`, `export`, `status` e `run`. I comandi specifici rendono il
processo automatizzabile e riproducibile; `run` offre un percorso guidato che
invoca gli stessi servizi. Una futura interfaccia conversazionale potrà usare il
medesimo livello applicativo senza diventare parte della prima release.

### Orchestratore

L'orchestratore applica la macchina a stati del progetto, valida i prerequisiti
di ogni comando, crea checkpoint, registra approvazioni e riprende le esecuzioni
interrotte. Le fasi restano deterministiche nel loro ordine; cicli agentici
limitati sono ammessi soltanto dentro una fase, con numero massimo di tentativi,
budget e condizione di arresto configurabili.

### Servizi di dominio

I servizi sono separati per acquisizione, normalizzazione bibliografica,
deduplicazione, classificazione delle fonti, estrazione delle evidenze,
progettazione della scaletta, scrittura, audit e conversione. DOI, metadati,
riferimenti, stato ed esportazioni sono gestiti deterministicamente. I modelli
linguistici sono usati per espansione delle query, classificazione semantica,
sintesi, riorganizzazione, scrittura e revisione.

### Adattatori

Interfacce tipizzate isolano:

- fonti accademiche e web;
- acquisizione di PDF, URL e documenti locali;
- modelli cloud e locali;
- modelli di embeddings;
- parser Markdown/LaTeX e convertitori di output.

Cambiare provider non deve modificare i servizi di dominio.

## Struttura di un progetto

La cartella di lavoro è leggibile, versionabile con Git e autosufficiente:

```text
mia-tesi/
├── project.yaml
├── originals/
├── sources/
│   ├── records.jsonl
│   └── documents/
├── evidence/
│   ├── claims.jsonl
│   └── records.jsonl
├── outline.md
├── draft.md
├── references.bib
├── audit.md
├── provenance.json
├── exports/
└── .thesis-agent/cache.sqlite3
```

`project.yaml` contiene domanda di ricerca, lingua, profilo disciplinare,
criteri di inclusione/esclusione, stile bibliografico, provider e politica di
rete. Markdown è il formato canonico del testo. JSONL conserva record
ispezionabili; BibTeX conserva la bibliografia; SQLite è soltanto indice e cache
rigenerabile, quindi non costituisce la fonte primaria dello stato.

Gli originali importati sono copiati in `originals/` e non sono modificati. La
copia di lavoro viene normalizzata in Markdown, mantenendo una mappa tra
sezioni, citazioni, figure, tabelle e posizioni del documento originario.

## Modello dei dati e provenienza

Ogni fonte contiene almeno identificativo interno, titolo, autori, anno, tipo,
DOI o URL, connettore di origine, livello della fonte, disponibilità del testo,
stato di selezione e motivazione. Gli stati sono `candidate`, `included`,
`excluded` e `needs_review`.

Ogni evidenza è atomica e contiene fonte, posizione nel documento, estratto o
riassunto attribuito, relazione con l'affermazione (`supports`, `contradicts` o
`contextualizes`), metodo di estrazione e stato di approvazione. Vengono
distinti metadati, abstract, testo completo open access e PDF fornito
dall'utente. Un record contenente soltanto metadati non può supportare
un'affermazione sul contenuto dell'opera.

Ogni affermazione contiene testo, sezione, stato (`supported`, `unsupported`,
`conflicted` o `needs_review`) e collegamenti alle evidenze. `draft.md` utilizza
chiavi bibliografiche soltanto per fonti presenti in `references.bib` e incluse
nel corpus. `provenance.json` registra versioni dei prompt, provider, modelli,
parametri, hash degli input e output, connettori consultati e approvazioni.

## Pipeline e comandi

### `init` e `import`

`init` crea un progetto da domanda, disciplina, lingua e criteri di selezione.
`import` accetta Markdown o LaTeX per la tesi, file BibTeX associati e PDF, DOI
o URL per le fonti. Per LaTeX segue `\input` e `\include` a partire da un file
radice, ma soltanto entro la directory importata. Riconosce sezioni, citazioni,
bibliografia, figure e tabelle; ambiguità di parsing producono avvisi con
posizione e non modificano l'originale.

### `research`

Genera query controllate a partire dalla domanda di ricerca e interroga i
connettori abilitati. La priorità è:

1. banche dati accademiche;
2. pagine istituzionali e documentazione ufficiale;
3. web generico, soltanto come fallback etichettato.

I connettori iniziali sono OpenAlex per la scoperta generale, Crossref per DOI e
metadati, PubMed/NCBI per l'area biomedica, arXiv per preprint, Unpaywall per
individuare copie open access e Brave Search API come ricerca web opzionale.
DOI e metadati discordanti vengono inviati a `needs_review`. Il web controllato
applica allowlist e classificazione del dominio; risultati generici non entrano
automaticamente tra le fonti incluse.

La classificazione registra quattro livelli senza trasformarli in un giudizio
automatico di verità: `academic_reviewed`, `academic_preprint`,
`institutional_official` e `generic_web`. Il profilo può stabilire quali livelli
sono ammessi, ma ogni inclusione resta visibile e approvabile dall'utente.

### `evidence`

Deduplica prima per DOI e identificatori persistenti, poi per titolo, autori e
anno normalizzati. Estrae evidenze dal contenuto disponibile, distingue
supporto, contraddizione e contesto, quindi costruisce la matrice da approvare.
Abstract e testo completo non sono trattati come equivalenti.
I PDF con livello testuale vengono estratti direttamente. Un PDF scansionato
richiede il componente OCR opzionale; se non disponibile resta acquisito ma non
può produrre evidenze e viene marcato `needs_review`.

### `outline`

Costruisce una scaletta basata su domanda, profilo e sole evidenze approvate.
Nel percorso di revisione propone spostamenti e raccordi senza eliminare o
aggiungere contenuto preesistente senza una voce esplicita nel rapporto delle
modifiche.

### `draft`

Genera una sezione per volta a partire dalla scaletta approvata. Ogni paragrafo
conserva i collegamenti alle evidenze; risultati dichiarati dalle fonti e
inferenze del modello sono etichettati separatamente nei dati di provenienza.
Un'informazione mancante produce un marcatore di revisione, non una fonte o un
risultato inventato.

### `audit`

Controlla copertura delle affermazioni, citazioni mancanti, citazioni prive di
fonte, riferimenti inutilizzati, metadati discordanti, evidenze contraddittorie,
ripetizioni e coerenza dei richiami a figure e tabelle. Produce `audit.md` con
gravità, posizione, motivazione, evidenze e correzione proposta. Le correzioni
non vengono applicate senza approvazione.

### `export`

Esporta dal Markdown canonico verso Markdown, LaTeX, BibTeX e DOCX. La prima
release non promette importazione o modifica diretta di Word con conservazione
perfetta dell'impaginazione. Le conversioni usano Pandoc quando disponibile e
falliscono con istruzioni operative se la dipendenza manca. Gli stili
bibliografici sono selezionati tramite nome o file CSL dichiarato in
`project.yaml`.

## Provider LLM, embeddings e privacy

Le interfacce dei provider coprono generazione strutturata, generazione testuale
ed embeddings. La prima release fornisce adattatori per OpenAI, Anthropic,
Gemini e Ollama; un endpoint compatibile con OpenAI può essere configurato come
provider aggiuntivo. Ruoli diversi (`researcher`, `writer`, `reviewer`,
`embedder`) possono usare modelli diversi oppure lo stesso modello.

La modalità offline accetta soltanto documenti già presenti e provider locali.
Qualunque tentativo di usare rete o provider cloud viene bloccato prima della
richiesta. Le chiavi sono lette da variabili d'ambiente o dal portachiavi del
sistema e non vengono scritte nei file di progetto. I log evitano segreti e,
per impostazione predefinita, conservano hash e metadati invece del contenuto
integrale dei prompt. L'utente può richiedere un log locale completo.

I documenti importati sono dati non attendibili: il sistema non esegue comandi,
macro LaTeX, JavaScript o contenuti incorporati. Download e parsing applicano
limiti di dimensione, timeout, tipi di contenuto ammessi e protezione dai
percorsi che escono dalla cartella di progetto. Gli export producono file ma non
compilano automaticamente LaTeX né aprono documenti esterni.

## Profili disciplinari

Il nucleo è generalista. I profili modificano connettori prioritari, vocabolario,
tipi di pubblicazione, checklist metodologiche e struttura suggerita, senza
duplicare la pipeline. La distribuzione iniziale include:

- `stem`, profilo generale;
- `computer-science`, con arXiv e pubblicazioni congressuali;
- `biomedical`, con PubMed e distinzione tra studi clinici, revisioni e
  preprint.

Lingua, stile bibliografico e struttura restano configurazioni del progetto.
Un profilo non può abbassare le regole comuni di provenienza e approvazione.

## Errori, ripresa e costi

Ogni fase crea un checkpoint atomico. Timeout, rate limit e indisponibilità
temporanee usano retry limitati con backoff; dopo il limite il progetto resta
riprendibile. Risposte LLM sono validate contro schemi; output non validi
subiscono un solo tentativo di riparazione strutturata e poi passano a
`needs_review`.

Ogni esecuzione può avere limiti di richieste, token e costo. Il superamento
arresta la fase senza invalidare gli artefatti precedenti. Cache e richieste
registrate evitano chiamate duplicate. Un export fallito non modifica la bozza
canonica.

## Test e criteri di accettazione

La suite contiene:

- test unitari per configurazione, normalizzazione, deduplicazione, stati,
  citazioni e riferimenti a figure/tabelle;
- test contrattuali degli adattatori con fixture registrate e segreti assenti;
- test di import/export Markdown e LaTeX con casi golden;
- test della catena completa affermazione-evidenza-fonte-citazione;
- test avversi con DOI inventati, metadati discordanti, fonti contraddittorie,
  abstract senza full text e output LLM malformati;
- test end-to-end con provider simulato e smoke test opzionali con Ollama e
  connettori live;
- caso end-to-end anonimizzato derivato dalla tesi sulla polmonite.

La release è accettabile quando:

1. da una domanda produce corpus approvabile, matrice delle evidenze, scaletta,
   bozza citata, audit e quattro formati di export;
2. da una tesi Markdown/LaTeX preserva l'originale, ricostruisce riferimenti e
   segnala affermazioni non supportate;
3. nessuna citazione nel testo esportato è priva di una fonte verificata nel
   corpus;
4. un'esecuzione interrotta riprende dall'ultimo checkpoint valido;
5. la modalità offline non effettua traffico di rete.

## Distribuzione e confini

Il progetto è un pacchetto Python installabile, multipiattaforma, pubblicato con
licenza Apache 2.0 e nome di lavoro `thesis-agent`. La documentazione comprende
quickstart, configurazione dei provider, esempio offline, politica di
provenienza, limiti e linee guida per l'integrità accademica.

La prima release non include modifica diretta di DOCX con fedeltà tipografica,
superamento di paywall, invio automatico della tesi, certificazione antiplagio o
sostituzione della revisione accademica. Il progetto non redistribuisce testi
protetti acquisiti dall'utente.

L'implementazione è organizzata in milestone sequenziali: fondamenta e CLI;
acquisizione e normalizzazione; evidenze; scaletta e scrittura; audit ed export;
profili, documentazione e rilascio GitHub.

## Riferimenti tecnici verificati

- OpenAlex API: <https://developers.openalex.org/api-reference/introduction>
- Crossref REST API: <https://www.crossref.org/documentation/retrieve-metadata/rest-api/>
- NCBI E-utilities: <https://www.ncbi.nlm.nih.gov/books/NBK25501/>
- Unpaywall REST API: <https://unpaywall.org/api>
- Brave Search API: <https://api-dashboard.search.brave.com/app/documentation/web-search/get-started>
- Ollama API: <https://docs.ollama.com/api/introduction>
- Pandoc: <https://pandoc.org/getting-started.html>
