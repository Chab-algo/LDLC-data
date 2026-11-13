# Soutenance : déroulé et répartition (Rubens Le Scao)

Dashboard (démo, avec la synthèse IA) : https://claude.ai/artifact/UFqbRsCqsWfCxSCEa4iCpf
Deck : `slides/LDLC_Espagne_Comex.pptx` (12 slides), généré par `slides/build_deck.js`.

| Temps | Partie de l'oral (PDF) | Slides | Qui | Critère évalué |
|---|---|---|---|---|
| 1 min | Entreprise et pays cible | 1 | Rubens | posture métier |
| 1 min 30 | Base de données et cadrage | 2 et 3 | Benjamin (sources, automatisation), Thomas (étoile) | modélisation, sources, automation |
| 2 min | Pourquoi ces KPIs | 4 | Georges | réflexion analytique et KPIs |
| 3 min | L'analyse tirée des chiffres | 5 à 11 + démo dashboard et IA | Georges | DataViz |
| 1 min 30 | Recommandation Go/No-Go | 12 | Rubens | arbitrage |

## Message central

No-Go magasins en l'état : le marché croît (+17,7 % en 2025) et 97,9 % du catalogue est déjà disponible
en Espagne, mais LDLC ne peut pas s'aligner sur les prix Android sans quasiment perdre sa marge.
Trois conditions et quatre données pour rouvrir le dossier.

## Questions probables

- **Pourquoi LDLC ?** Société cotée, données publiques complètes, expansion déjà tentée en Espagne (2018-2020).
- **Votre marge est une hypothèse ?** Oui, c'est dit sur la slide 8 : marge du groupe appliquée à la téléphonie. À 15 %, Android passe en négatif.
- **Qu'est-ce qui est automatisé ?** Eurostat, OpenStreetMap, distances et prix LDLC, chaque lundi via GitHub Actions ; la base DuckDB et le dashboard sont régénérés.
- **Pourquoi une étoile ?** Peu de dimensions, requêtes simples ; clé produit sans EAN car Apple change de référence selon le pays.
