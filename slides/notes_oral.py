"""Ajoute à chaque slide du deck l'orateur, son temps et son texte (dans les notes).
Usage : node slides/build_deck.js && python slides/notes_oral.py
"""
from pathlib import Path
from pptx import Presentation

DECK = Path(__file__).with_name("LDLC_Espagne_Comex.pptx")

ORAL = [
 ("Rubens", "1 min", "Bonjour. Nous sommes l'équipe Data Analytics du Groupe LDLC : 125 magasins en France, 554 millions d'euros de chiffre d'affaires. Pour sa stratégie 2027-2029, le Comex nous pose une question : ouvrir des magasins en Espagne, sur la téléphonie, est-ce réalisable et rentable ? Le sujet est sensible : LDLC a déjà ouvert des magasins en Espagne en 2018 et les a fermés en 2020. Notre réponse : pas de magasins en l'état. Voici comment on y arrive. Benjamin va vous montrer d'où viennent nos données."),
 ("Benjamin", "45 s", "Toutes nos données viennent de sources publiques et gratuites : Eurostat pour le marché, OpenStreetMap pour les concurrents, OSRM pour les distances, et les sites de LDLC, PcComponentes et MediaMarkt pour les prix. Un script Python par source, relancé chaque lundi par GitHub Actions, qui met à jour la base et le dashboard. Si une source tombe, on garde la collecte précédente et l'incident est noté. Chaque chiffre porte un statut : sourcé, calculé ou hypothèse. Thomas va vous montrer comment on les a structurées."),
 ("Thomas", "45 s", "On a choisi un modèle en étoile dans DuckDB : cinq tables de faits (prix, points de vente, marché, catalogue, magasin simulé) autour de six dimensions. Une règle clé : on compare les prix par modèle, capacité et RAM, pas par code EAN, parce qu'Apple change de référence selon le pays. Et on compare hors taxes, pour neutraliser l'écart de TVA : 20 % en France, 21 % en Espagne."),
 ("Thomas", "1 min 15", "Nos onze KPIs suivent les cinq axes du cahier des charges, et chacun répond à une décision. Marché : le plafond de chiffre d'affaires. Prix et marges : peut-on être au prix ? Réseau : le coût d'ouverture. Logistique : l'approvisionnement. Assortiment : catalogue complet ou ciblé. Résultat : le marché et l'assortiment sont favorables, 97,9 % de notre catalogue est déjà en ligne sur le site espagnol de LDLC. Tout se joue donc sur les prix et les marges. Benjamin commence par le marché."),
 ("Benjamin", "30 s", "Le marché d'abord. Les ventes des magasins high-tech spécialisés ont progressé de 67 % en Espagne depuis 2021, contre 27 % en France. Rien qu'en 2025 : plus 17,7 % contre plus 9 %. Le marché espagnol est porteur."),
 ("Benjamin", "30 s", "La téléphonie y pèse 3,6 milliards d'euros. Mais le marché est déjà occupé : Apple et Samsung dominent le parc, et MediaMarkt détient 21,5 % du marché. LDLC arriverait face à un leader installé. Georges va vous montrer ce que ça donne sur les prix."),
 ("Georges", "30 s", "Pour un même modèle, l'Espagne est en moyenne 10,9 % moins chère hors taxes. Sur Apple, l'écart est faible : indice 96,3. Sur Android, il est fort : 76,6, soit environ 23 % moins cher. Or Android représente environ deux tiers du parc espagnol."),
 ("Georges", "40 s", "Si LDLC s'aligne sur ces prix, sa marge tombe à 1 % sur Android, et à 21,6 % sur Apple, sous notre seuil de 22 %. C'est une hypothèse, on le dit : on applique la marge du groupe, 24,5 %, car LDLC ne publie pas sa marge sur la téléphonie. À 15 %, plus réaliste pour des smartphones, Android passe à moins 11,4 %."),
 ("Benjamin", "30 s", "Pour l'implantation, Barcelone est la ville logique : c'est la plus proche de notre hub de l'Isère, 634 kilomètres, moins de 7 heures de route. Sa densité de concurrents est moyenne : 11,2 points de vente pour 100 000 habitants, 6e sur 10 villes."),
 ("Georges", "30 s", "Un magasin pilote de 150 m² à Barcelone doit faire 0,6 million d'euros de chiffre d'affaires pour couvrir loyer et personnel, soit 0,52 % du marché téléphonie de la ville : c'est atteignable. Mais seulement avec un loyer de centre commercial. En rue commerçante, il faudrait 1,8 million."),
 ("Georges", "50 s", "Enfin, la brique IA. Dans le dashboard, Claude lit tous nos chiffres et rédige une synthèse pour le Comex, avec une règle : n'utiliser que nos chiffres et signaler les hypothèses. Démonstration : je baisse la marge à 15 % dans le simulateur, je génère, et la recommandation se met à jour. Rubens conclut."),
 ("Rubens", "1 min 30", "Notre recommandation : No-Go sur les magasins en l'état. Deux seuils sur trois ne sont pas tenus : les prix et la marge. Le marché est porteur et le catalogue est prêt, mais LDLC ne peut pas s'aligner sur les prix Android sans quasiment perdre sa marge. Pour rouvrir le dossier : élargir le suivi des prix à Amazon, Fnac et El Corte Inglés, obtenir la marge réelle de LDLC sur la téléphonie, tester une offre Apple seule, la plus proche des seuils, et confirmer le loyer à Barcelone. Comme la collecte tourne chaque semaine, la recommandation se met à jour avec les données. Merci, nous sommes prêts pour vos questions."),
]

p = Presentation(DECK)
assert len(p.slides) == len(ORAL), f"{len(p.slides)} slides pour {len(ORAL)} textes"
for slide, (qui, temps, texte) in zip(p.slides, ORAL):
    tf = slide.notes_slide.notes_text_frame
    ancien = tf.text.split("\n\nRepères : ", 1)[-1] if "ORATEUR" in tf.text else tf.text
    tf.text = f"ORATEUR : {qui} ({temps})\n\n{texte}\n\nRepères : {ancien}"
p.save(DECK)
print("notes ajoutées à", len(ORAL), "slides")
