# Soutenance : déroulé et répartition (Rubens Le Scao)

Dashboard (démo, avec la synthèse IA) : https://claude.ai/artifact/UFqbRsCqsWfCxSCEa4iCpf
Deck : `slides/LDLC_Espagne_Comex.pptx` (12 slides), généré par `slides/build_deck.js`.

| Slides | Qui | Temps |
|---|---|---|
| 1. Question | Rubens | 1 min |
| 2. Sources et automatisation | Thomas | 45 s |
| 3. Modèle en étoile | Benjamin | 45 s |
| 4. KPIs par axe | Benjamin | 1 min 15 |
| 5 et 6. Marché | Thomas | 1 min |
| 7 et 8. Prix et marge | Georges | 1 min 10 |
| 9. Barcelone | Thomas | 30 s |
| 10. Magasin pilote | Georges | 30 s |
| 11. Synthèse IA et démo | Georges | 50 s |
| 12. Conclusion | Rubens | 1 min 30 |

Le texte de chaque orateur est dans les notes de chaque slide (`slides/notes_oral.py`).
Georges garde l'ordinateur et avance les slides. Questions : Thomas (sources, automatisation),
Benjamin (modélisation, KPIs), Georges (chiffres, dashboard, IA), Rubens (choix de LDLC et de l'Espagne, décision).

## Message central

No-Go magasins en l'état : le marché croît (+17,7 % en 2025) et 97,9 % du catalogue est déjà disponible
en Espagne, mais LDLC ne peut pas s'aligner sur les prix Android sans quasiment perdre sa marge.
Trois conditions et quatre données pour rouvrir le dossier.

## Questions probables

- **Pourquoi LDLC ?** Société cotée, données publiques complètes, expansion déjà tentée en Espagne (2018-2020).
- **Votre marge est une hypothèse ?** Oui, c'est dit sur la slide 8 : marge du groupe appliquée à la téléphonie. À 15 %, Android passe en négatif.
- **Qu'est-ce qui est automatisé ?** Eurostat, OpenStreetMap, distances et prix LDLC, chaque lundi via GitHub Actions ; la base DuckDB et le dashboard sont régénérés.
- **Pourquoi une étoile ?** Peu de dimensions, requêtes simples ; clé produit sans EAN car Apple change de référence selon le pays.
