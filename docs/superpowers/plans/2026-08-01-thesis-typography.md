# UniBS Thesis Typography Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adeguare `professor-report-final.tex` alle impostazioni tipografiche UniBS approvate, senza modificare contenuti o compilare il PDF.

**Architecture:** La modifica è confinata al preambolo e alla dichiarazione del titolo. La classe passa a 12 pt, `fontspec` seleziona Times New Roman, `geometry` applica i quattro margini, `setspace` imposta l'interlinea 1,5 e `titlesec` controlla le dimensioni gerarchiche dei titoli; i ridimensionamenti locali delle tabelle restano invariati.

**Tech Stack:** LaTeX, Tectonic/XeTeX, `fontspec`, `geometry`, `setspace`, `titlesec`, controlli statici con `rg`, `perl`, `awk` e `stat`.

## Global Constraints

- Modificare soltanto `professor-report-final.tex` per il contenuto della tesi.
- Non compilare né aggiornare `professor-report-final.pdf`.
- Mantenere formato A4.
- Usare Times New Roman come carattere principale.
- Usare corpo testo 12 pt, titoli 16 pt e sottotitoli 14 pt.
- Usare interlinea 1,5.
- Usare margini: superiore 3 cm, inferiore 3 cm, sinistro 4 cm, destro 3 cm.
- Conservare la giustificazione completa predefinita di LaTeX.
- Non modificare figure, tabelle, label, citazioni, bibliografia o valori sperimentali.
- Non aggiungere all'indice Git il `.tex`, che è intenzionalmente ignorato.

---

### Task 1: Applicare la tipografia UniBS

**Files:**
- Modify: `professor-report-final.tex:1-40`
- Verify unchanged: `professor-report-final.pdf`

**Interfaces:**
- Consumes: il preambolo LaTeX esistente e le direttive UniBS approvate.
- Produces: un preambolo con font, corpo, margini, interlinea e titoli conformi.

- [ ] **Step 1: Aggiornare classe e pacchetti tipografici**

Sostituire:

```latex
\documentclass[11pt,a4paper]{article}

\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
```

con:

```latex
\documentclass[12pt,a4paper]{article}

\usepackage{fontspec}
\setmainfont{Times New Roman}
```

Aggiungere dopo `\usepackage{geometry}`:

```latex
\usepackage{setspace}
\usepackage{titlesec}
```

- [ ] **Step 2: Impostare margini, interlinea e gerarchia dei titoli**

Sostituire `\geometry{margin=2.1cm}` con:

```latex
\geometry{
  top=3cm,
  bottom=3cm,
  left=4cm,
  right=3cm
}
\onehalfspacing

\titleformat{\section}
  {\normalfont\bfseries\fontsize{16}{19.2}\selectfont}
  {\thesection}{1em}{}
\titleformat{\subsection}
  {\normalfont\bfseries\fontsize{14}{16.8}\selectfont}
  {\thesubsection}{1em}{}
\titleformat{\subsubsection}
  {\normalfont\bfseries\fontsize{12}{14.4}\selectfont}
  {\thesubsubsection}{1em}{}
```

La giustificazione del corpo resta quella predefinita di LaTeX; non inserire
`raggedright`, `flushleft` o ambienti equivalenti.

- [ ] **Step 3: Impostare titolo e sottotitolo di copertina**

Sostituire la dichiarazione corrente con:

```latex
\title{%
  {\fontsize{16}{19.2}\selectfont\textbf{Classificazione binaria di polmonite da radiografie toraciche -- Inquadramento per tesi}}\\[0.4em]
  {\fontsize{14}{16.8}\selectfont Confronto tra reti CNN, generalizzazione cross-dataset e analisi statistica}%
}
```

Non modificare autore, data o contenuto del titolo.

- [ ] **Step 4: Verificare staticamente le impostazioni**

Run:

```bash
rg -n -F \
  -e '\documentclass[12pt,a4paper]{article}' \
  -e '\setmainfont{Times New Roman}' \
  -e '\onehalfspacing' \
  -e 'top=3cm' -e 'bottom=3cm' -e 'left=4cm' -e 'right=3cm' \
  -e '\fontsize{16}{19.2}' -e '\fontsize{14}{16.8}' \
  professor-report-final.tex
```

Expected: tutte le impostazioni compaiono nel preambolo o nel titolo.

- [ ] **Step 5: Verificare conservazione e sintassi**

Run:

```bash
awk '/\\begin\{figure\}/{f++} /\\begin\{table\}/{t++} /\\begin\{longtable\}/{lt++} /^\\bibitem\{/{b++} /\\label\{fig:/{fl++} /\\label\{tab:/{tl++} END {print "figures=" f, "tables=" t, "longtables=" lt, "bibitems=" b, "figure_labels=" fl, "table_labels=" tl; exit !((f==4)&&(t==19)&&(lt==1)&&(b==21)&&(fl==4)&&(tl==20))}' professor-report-final.tex
```

Expected: `figures=4 tables=19 longtables=1 bibitems=21 figure_labels=4 table_labels=20`.

Run anche un controllo degli ambienti `\begin`/`\end`, delle parentesi e dei
delimitatori matematici. Tutti devono risultare bilanciati.

- [ ] **Step 6: Verificare che il PDF non sia cambiato**

Run:

```bash
stat -f '%N | %Sm' -t '%Y-%m-%d %H:%M:%S' professor-report-final.pdf
```

Expected: `professor-report-final.pdf | 2026-08-01 11:03:11`.
