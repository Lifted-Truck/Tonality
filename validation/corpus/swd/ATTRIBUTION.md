# Vendored smoke set — Schubert Winterreise Dataset (SWD)

These 5 songs are a committed, deterministic fixture for the validation harness
(`validation/validate_corpus.py --swd validation/corpus/swd`). The full corpus is
fetched on demand for larger sweeps.

**Source:** Schubert Winterreise Dataset (SWD), v2.0.
Christof Weiß, Frank Zalkow, Vlora Arifi-Müller, Meinard Müller, et al.,
International Audio Laboratories Erlangen.
DOI: [10.5281/zenodo.5139893](https://zenodo.org/records/5139893).

**License: Creative Commons Attribution 3.0 (CC BY 3.0).** Attribution-only — no
ShareAlike, no NonCommercial. This lifts the **license** leg of the prior-derivation
boundary (unlike When-in-Rome / DCML, which are BY-SA / BY-NC-SA): tuning a prior
against SWD is *legally* permitted — with attribution, no ShareAlike contamination.
**The methodological leg still stands (response-6 / response-7):** SWD is one
composer / one song-cycle, so it is a sanctioned *measurement oracle* and a
*candidate* calibration source — **not an auto-fit one**. A shipped corpus-fit prior
wants corroborating breadth from a second license-clean repertoire, or an explicit
theory-bounding with the SWD fit as supporting evidence rather than sole authority.
Cite the SWD paper + DOI in any derived asset.

**Vendored slice (score side only; audio discarded):**
- `01_RawData/score_midi/Schubert_D911-{01,07,09,11,21}.mid`
- `02_Annotations/ann_score_localkey-ann{1,2,3}/` — local key, 3 annotators
  (inter-annotator agreement = an interpretive-variance floor for Finding 2)
- `02_Annotations/ann_score_chord/` — chord labels (for Phase-2 chord scoring)
- `02_Annotations/ann_score_globalkey.csv` — global key

Songs chosen to span the result space: D911-01 (D min, opening), 09 (B min, the
engine's best region agreement), 07 (E min — a global-key miss → dominant), 11
(A maj), 21 (F maj).
