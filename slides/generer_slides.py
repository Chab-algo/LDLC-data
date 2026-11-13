# Génère les slides du Comex (artifact Slides) à partir de data/processed/. Usage : python slides/generer_slides.py
import json, csv, datetime, html
from pathlib import Path
P=str(Path(__file__).resolve().parents[1]/"data"/"processed")+"/"
import os; os.makedirs("project/slides",exist_ok=True)
rd=lambda f: list(csv.DictReader(open(P+f)))
ip=rd("indice_prix.csv"); mg=rd("marge_si_alignement.csv"); de=rd("densite_concurrentielle.csv"); ma=rd("marche.csv")
INK="#16181d"; LIGHT="#f4f2ec"; BLUE="#2a78d6"; ORANGE="#e0622c"; MUTED="#5b5d63"; GRID="#dcd9cf"
fr=lambda x,d=1: f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
def esc(s): return html.escape(str(s))

def hbars(rows, label, val, fam, dom, ref, fmt, W=1664, rh=44, lw=560, aria=""):
    H=len(rows)*rh+50
    x=lambda v: lw+(v-dom[0])/(dom[1]-dom[0])*(W-lw-90)
    o=[f'<svg aria-label="{esc(aria)}" viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">']
    rows_txt=[]
    z = 0 if dom[0]<0 else dom[0]
    for i,r in enumerate(rows):
        y=i*rh; v=val(r); c=BLUE if fam(r)=="Apple" else ORANGE
        xa=min(x(z),x(v)); w=max(3,abs(x(v)-x(z)))
        o.append(f'<text x="{lw-16}" y="{y+rh/2+9}" text-anchor="end" font-family="Inter" font-size="25" fill="{INK}">{esc(label(r))}</text>')
        o.append(f'<rect x="{xa:.1f}" y="{y+9}" width="{w:.1f}" height="{rh-18}" rx="6" fill="{c}"/>')
        inside = w > 120
        if inside:
            tx = x(v)-14 if v>=z else x(v)+14; an="end" if v>=z else "start"; col="#ffffff"
        else:
            tx = x(v)+12 if v>=z else x(v)-12; an="start" if v>=z else "end"; col=INK
        rows_txt.append(f'<text x="{tx:.1f}" y="{y+rh/2+9}" text-anchor="{an}" font-family="Inter" font-weight="600" font-size="25" fill="{col}">{fmt(v)}</text>')
    yb=len(rows)*rh
    if ref is not None and False:
        pass
    if ref is not None:
        o.append(f'<line x1="{x(ref):.1f}" x2="{x(ref):.1f}" y1="-6" y2="{yb}" stroke="{MUTED}" stroke-width="3" stroke-dasharray="10 8"/>')
    if dom[0]<0:
        o.append(f'<line x1="{x(0):.1f}" x2="{x(0):.1f}" y1="-6" y2="{yb}" stroke="{INK}" stroke-width="2"/>')
    o.extend(rows_txt)
    o.append("</svg>")
    return "".join(o)

ip_s=sorted(ip,key=lambda r: float(r["indice_es_vs_fr"]))
svg_ind=hbars(ip_s, lambda r:r["modele"], lambda r: float(r["indice_es_vs_fr"]), lambda r:r["famille"], (0,110), 100, lambda v: fr(v,0), aria="Indice de prix Espagne sur France par modèle")
mg_s=sorted(mg,key=lambda r: float(r["marge_si_alignement"]))
svg_mg=hbars(mg_s, lambda r:r["modele"], lambda r: float(r["marge_si_alignement"]), lambda r:r["famille"], (-0.3,0.3), 0.22, lambda v: ("−" if v<0 else "")+fr(abs(v)*100,1)+" %", rh=50, aria="Marge si alignement par modèle")

# market line chart
g=[r for r in ma if r["indicateur"]=="eurostat_VOL_SLS_G474_I21_CA" and int(r["annee"])>=2021]
ser={p:sorted([(int(r["annee"]),float(r["valeur"])) for r in g if r["pays"]==p]) for p in ("ES","FR")}
W,H,L,R,T,B=1000,620,70,190,20,50
x=lambda a: L+(a-2021)/4*(W-L-R); y=lambda v: T+(1-(v-80)/(180-80))*(H-T-B)
o=[f'<svg aria-label="Volume des ventes des magasins high-tech spécialisés, base 100 en 2021, Espagne et France" viewBox="0 0 {W} {H}" width="{W}" height="{H}" xmlns="http://www.w3.org/2000/svg">']
for v in (100,120,140,160,180):
    o.append(f'<line x1="{L}" x2="{W-R}" y1="{y(v)}" y2="{y(v)}" stroke="{GRID}" stroke-width="2"/><text x="{L-12}" y="{y(v)+8}" text-anchor="end" font-family="Inter" font-size="24" fill="{MUTED}">{v}</text>')
for a in range(2021,2026): o.append(f'<text x="{x(a)}" y="{H-10}" text-anchor="middle" font-family="Inter" font-size="24" fill="{MUTED}">{a}</text>')
for p,c,n in (("ES",BLUE,"Espagne"),("FR",ORANGE,"France")):
    pts=ser[p]; o.append(f'<path d="{"".join(("L" if i else "M")+f"{x(a):.1f},{y(v):.1f}" for i,(a,v) in enumerate(pts))}" fill="none" stroke="{c}" stroke-width="6" stroke-linejoin="round"/>')
    for a,v in pts: o.append(f'<circle cx="{x(a):.1f}" cy="{y(v):.1f}" r="9" fill="{c}" stroke="{LIGHT}" stroke-width="4"/>')
    a,v=pts[-1]; o.append(f'<text x="{x(a)+20}" y="{y(v)+9}" font-family="Inter" font-weight="600" font-size="28" fill="{INK}">{n} {fr(v,0)}</text>')
o.append("</svg>"); svg_mk="".join(o)
es25=ser["ES"][-1][1]; fr25=ser["FR"][-1][1]; ges=ser["ES"][-1][1]/ser["ES"][-2][1]-1; gfr=ser["FR"][-1][1]/ser["FR"][-2][1]-1
print("growth",es25,fr25,ges,gfr)

S={}
S["cover"]=f'''<section id="cover" class="dark cover">
<p class="kicker">Recommandation au Comex · Stratégie 2027-2029</p>
<h1>LDLC en Espagne : faut-il ouvrir des magasins de téléphonie ?</h1>
<p class="lead">Groupe LDLC · étude de faisabilité et de rentabilité</p>
<p class="team">Georges Do Xuan · Thomas Lefevbre · Benjamin Chabani · Rubens Le Scao<br>MSc Eugenia School · données au 12/11/2026</p>
<aside>Ouverture (30 s). On se présente comme l'équipe Data Analytics de LDLC. La question du Comex : l'implantation en Espagne, sur la téléphonie, est-elle réalisable et rentable ? On donne la réponse tout de suite, puis on montre comment on y arrive.</aside>
</section>'''
S["reponse"]=f'''<section id="reponse" class="statement">
<p class="kicker">Notre réponse</p>
<h2 class="huge">Pas de magasins en l'état. Le marché est porteur, mais LDLC ne peut pas s'aligner sur les prix Android sans vendre à perte.</h2>
<div class="stats">
<div class="stat"><p class="num blue">+67 %</p><p class="cap">ventes des magasins high-tech espagnols depuis 2021 (France : +27 %)</p></div>
<div class="stat"><p class="num orange">−29 %</p><p class="cap">prix Android en Espagne par rapport à LDLC, hors taxes</p></div>
<div class="stat"><p class="num">1,7 M€</p><p class="cap">de CA par an pour qu'un magasin à Barcelone ne perde pas d'argent</p></div>
</div>
<aside>1 min. Trois chiffres à retenir. Le marché croît vite (Eurostat, volume des ventes des magasins spécialisés informatique et télécoms). Mais sur Android, deux tiers du parc espagnol, les prix sont environ 29 % plus bas que chez LDLC (indice 70,8). Et un magasin pilote doit faire 1,7 M€ de CA pour couvrir loyer et personnel. Tout ce qui suit est collecté automatiquement ou marqué comme hypothèse.</aside>
</section>'''
S["entreprise"]=f'''<section id="entreprise">
<h2>LDLC : un spécialiste français du high-tech, très dépendant de la France</h2>
<div class="cards c3">
<div class="card"><p class="num">125</p><h3>magasins</h3><p>dont 102 sous enseigne LDLC (33 en propre, 54 franchisés)</p></div>
<div class="card"><p class="num">554 M€</p><h3>de CA 2025-2026</h3><p>marge brute 24,5 %, résultat net 10,2 M€</p></div>
<div class="card"><p class="num">88 %</p><h3>du CA en France</h3><p>deux magasins espagnols ouverts en 2018, fermés en 2020 (environ 2 M€)</p></div>
</div>
<p class="body">Pourquoi l'Espagne et la téléphonie : le marché espagnol des biens techniques pèse 12 Md€ et croît, la téléphonie en fait 30 %. LDLC y vend déjà en ligne depuis la France. Mais la trésorerie est courte : 7,1 M€, pour 42,2 M€ de dette nette.</p>
<p class="source">Sources : rapports financiers Groupe LDLC 2025-2026, AECOC/GfK</p>
<aside>1 min. Le contexte qui pèse sur la décision : un premier essai en Espagne déjà raté, un CA en baisse de 9,6 % au premier semestre 2026-2027, peu de trésorerie. Le Comex n'a pas droit à un deuxième échec.</aside>
</section>'''
S["methode"]=f'''<section id="methode">
<h2>Une chaîne de données automatisée, relancée chaque semaine</h2>
<div class="flow">
<div class="step"><h3>Sources gratuites</h3><p>Eurostat, OpenStreetMap, OSRM, sites LDLC et PcComponentes, BOE</p></div>
<x-shape kind="arrow-right" style="background:{BLUE};width:64px;height:40px"></x-shape>
<div class="step"><h3>Collecte Python</h3><p>4 scripts, GitHub Actions chaque lundi</p></div>
<x-shape kind="arrow-right" style="background:{BLUE};width:64px;height:40px"></x-shape>
<div class="step"><h3>Base en étoile</h3><p>DuckDB : 6 dimensions, 5 tables de faits</p></div>
<x-shape kind="arrow-right" style="background:{BLUE};width:64px;height:40px"></x-shape>
<div class="step"><h3>KPIs et simulation</h3><p>indice de prix, marge, densité, point mort</p></div>
<x-shape kind="arrow-right" style="background:{BLUE};width:64px;height:40px"></x-shape>
<div class="step dark"><h3>Dashboard et IA</h3><p>simulateur et synthèse rédigée par Claude</p></div>
</div>
<p class="body">Chaque chiffre porte un statut : donnée sourcée, calcul de l'équipe ou hypothèse. Rien n'est saisi à la main sans être signalé.</p>
<p class="source">Code et données : github.com/Chab-algo/LDLC-data</p>
<aside>1 min. Benjamin (collecte) : les sources et l'automatisation. Montrer le journal de collecte du dashboard : une collecte peut échouer (OpenStreetMap a été lent une fois), la chaîne garde alors les données précédentes.</aside>
</section>'''
S["etoile"]=f'''<section id="etoile">
<h2>Le modèle en étoile : comparer des prix, des zones et des coûts</h2>
<div class="star">
<div class="dim d1"><h3>dim_produit</h3><p>marque, modèle, capacité, RAM, famille</p></div>
<div class="dim d2"><h3>dim_enseigne</h3><p>type, pays d'origine</p></div>
<div class="dim d3"><h3>dim_pays</h3><p>TVA, canon digital</p></div>
<div class="fact"><h3>fact_prix</h3><p>prix TTC et HT par jour</p><h3>fact_point_de_vente</h3><p>magasins concurrents</p><h3>fact_marche</h3><p>indicateurs par pays et année</p><h3>fact_magasin_sim</h3><p>compte de résultat simulé</p></div>
<div class="dim d4"><h3>dim_zone</h3><p>ville, population, distance au hub</p></div>
<div class="dim d5"><h3>dim_hub</h3><p>entrepôts LDLC</p></div>
<div class="dim d6"><h3>dim_date</h3><p>jour, exercice LDLC</p></div>
</div>
<p class="source">Règle clé : les prix sont appariés par modèle, capacité et RAM, pas par EAN (Apple change de référence selon le pays), et comparés hors taxes</p>
<aside>1 min 30. Thomas (modélisation). Insister sur l'appariement : MG6K4F/A en France contre MG6M4QL/A en Espagne pour le même iPhone. Comparaison hors taxes pour neutraliser 20 % contre 21 % de TVA.</aside>
</section>'''
S["kpis"]=f'''<section id="kpis">
<h2>Onze KPIs, quatre questions</h2>
<table class="kt">
<tr><th>Question</th><th>KPIs</th><th>Ce qu'on a</th></tr>
<tr><td><b>Le marché vaut-il le coup ?</b></td><td>croissance du secteur, pénétration de la téléphonie, part de marché du leader</td><td>Eurostat collecté, AECOC/GfK, Ceconomy</td></tr>
<tr><td><b>Peut-on être au prix ?</b></td><td>indice de prix, marge post-taxe, taxes locales</td><td>11 modèles relevés, marge simulée</td></tr>
<tr><td><b>Où s'implanter ?</b></td><td>densité concurrentielle, coût au m², distance aux hubs</td><td>OpenStreetMap, OSRM, proxy loyer</td></tr>
<tr><td><b>Que vendre ?</b></td><td>% du catalogue éligible, part de marché de LDLC</td><td>à compléter</td></tr>
</table>
<aside>2 min. Georges (analyse). Chaque KPI répond à une question de décision. Le KPI 11 (catalogue éligible) n'est pas encore fiable : nos 11 modèles ont été choisis parce qu'ils sont vendus dans les deux pays.</aside>
</section>'''
S["marche"]=f'''<section id="marche">
<h2>Le commerce high-tech espagnol croît deux fois plus vite</h2>
<div class="split">
<div>{svg_mk}</div>
<div class="side">
<p class="num blue">+{fr(ges*100)} %</p><p class="cap">en Espagne en 2025</p>
<p class="num orange">+{fr(gfr*100)} %</p><p class="cap">en France en 2025</p>
<p class="body small">Volume des ventes des magasins spécialisés en informatique et télécoms, base 100 en 2021</p>
</div>
</div>
<p class="source">Source : Eurostat sts_trtu_a, NACE G474, corrigé des jours ouvrables. Tout le high-tech spécialisé, pas seulement la téléphonie</p>
<aside>45 s. Le marché n'est pas le problème. La téléphonie pèse 29,9 % du marché espagnol des biens techniques (environ 3,6 Md€, calcul de l'équipe).</aside>
</section>'''
S["prix"]=f'''<section id="prix">
<h2>Apple au même prix, Android 29 % moins cher en Espagne</h2>
<div class="legend"><span><i style="background:{BLUE}"></i>Apple · indice 95,9</span><span><i style="background:{ORANGE}"></i>Android · indice 70,8</span><span class="muted">pointillé : même prix qu'en France (100)</span></div>
<div>{svg_ind}</div>
<p class="source">Prix HT PcComponentes Espagne / prix HT LDLC France × 100. 11 modèles, relevés le 12/11/2026. Une seule enseigne espagnole pour l'instant</p>
<aside>45 s. L'écart vient des remises de PcComponentes : les prix conseillés sont proches d'un pays à l'autre. Android, c'est environ deux tiers du parc espagnol (Samsung 24,9 %, Xiaomi 22,2 %, StatCounter août 2026).</aside>
</section>'''
S["marge"]=f'''<section id="marge">
<h2>S'aligner sur Android, c'est vendre à perte</h2>
<div class="legend"><span><i style="background:{BLUE}"></i>Apple · 21 % en moyenne</span><span><i style="background:{ORANGE}"></i>Android · −7 % en moyenne</span><span class="muted">pointillé : marge normative 22 %</span></div>
<div>{svg_mg}</div>
<p class="source">Hypothèse : coût d'achat = prix HT LDLC France × (1 − 24,5 %), marge brute du groupe. La marge réelle en téléphonie n'est pas publiée</p>
<aside>45 s. C'est le point central. Même sur Apple, la marge reste sous la cible de 22 %. Si LDLC achète moins cher que ce qu'on suppose, le constat s'améliore : c'est la première donnée à obtenir en interne.</aside>
</section>'''
bcn=next(r for r in de if r["ville"]=="Barcelona"); mad=next(r for r in de if r["ville"]=="Madrid")
S["terrain"]=f'''<section id="terrain">
<h2>Barcelone : la ville la plus proche des hubs, et déjà très équipée</h2>
<div class="cards c3">
<div class="card"><p class="num">{fr(float(bcn["distance_route_km"]),0)} km</p><h3>depuis Saint-Quentin-Fallavier</h3><p>{fr(float(bcn["duree_route_h"]))} h de route. Madrid : {fr(float(mad["distance_route_km"]),0)} km depuis Nantes</p></div>
<div class="card"><p class="num">{fr(float(bcn["nb_points_de_vente"]),0)}</p><h3>points de vente concurrents</h3><p>{fr(float(bcn["points_de_vente_pour_100k_hab"]))} pour 100 000 habitants, dont MediaMarkt et Fnac</p></div>
<div class="card"><p class="num">21,5 %</p><h3>de part de marché pour MediaMarkt</h3><p>24,6 % en magasins, leader en Espagne</p></div>
</div>
<p class="source">Sources : OpenStreetMap (Overpass, collecte du 12/11/2026), OSRM, Ceconomy. OSM est contributif : un magasin absent n'est pas compté</p>
<aside>45 s. La Catalogne est la zone logique : la plus proche du hub de l'Isère. Les villes moyennes catalanes (Girona, Lleida, Tarragona) ont même plus de points de vente par habitant que Barcelone.</aside>
</section>'''
S["pilote"]=f'''<section id="pilote">
<h2>Un magasin pilote à Barcelone doit faire 1,7 M€ pour être à l'équilibre</h2>
<div class="split2">
<table class="kt">
<tr><th>Poste annuel</th><th class="r">Montant</th><th>Base</th></tr>
<tr><td>Loyer</td><td class="r">243 000 €</td><td>150 m² × 135 €/m²/mois (proxy)</td></tr>
<tr><td>Personnel</td><td class="r">89 333 €</td><td>4 ETP au SMI 2026 + 30,65 % de charges</td></tr>
<tr><td>Taux de contribution</td><td class="r">19,5 %</td><td>marge 24,5 % − 5 % de charges variables</td></tr>
<tr><td><b>CA HT au point mort</b></td><td class="r"><b>1,70 M€</b></td><td>charges fixes / contribution</td></tr>
</table>
<div class="side"><p class="num">1,4 %</p><p class="cap">du marché téléphonie de Barcelone à capter, au prorata de la population</p></div>
</div>
<p class="source">SMI : Real Decreto 126/2026. Charges : Orden PJC/297/2026. Loyer : rue commerçante secondaire (Bilbao), aucun chiffre trouvé pour un centre commercial. Surface et effectif : hypothèses de l'équipe</p>
<aside>1 min. Le point mort semble atteignable sur le papier, mais il suppose la marge de 24,5 %. Avec les prix espagnols sur Android, la marge baisse et le point mort monte. Montrer le simulateur dans le dashboard : faire varier la marge à 15 % en direct.</aside>
</section>'''
S["reco"]=f'''<section id="reco" class="dark">
<h2>Notre recommandation</h2>
<div class="cards c3">
<div class="card choice"><p class="tagline">Ce qu'on recommande</p><h3>No-Go magasins en 2027</h3><p>Renforcer la vente en ligne en Espagne depuis les hubs français</p></div>
<div class="card"><p class="tagline">Ce qui ferait passer en Go</p><h3>Trois conditions</h3><p>prix Android à moins de 5 % des concurrents, marge post-taxe d'au moins 22 %, loyer en centre commercial confirmé</p></div>
<div class="card"><p class="tagline">Prochaines données</p><h3>Pour décider en 2028</h3><p>coûts d'achat réels de LDLC, prix MediaMarkt Espagne, catalogue complet, loyers en périphérie</p></div>
</div>
<p class="source light">La collecte continue chaque semaine : la recommandation se met à jour avec les données</p>
<aside>1 min 30. Rubens. Conclure sur la décision et les conditions. Terminer par la synthèse IA du dashboard, générée en direct avec les réglages du simulateur. Limites à assumer si on nous les demande : une seule enseigne espagnole relevée, marge téléphonie non publiée, loyer proxy, OSM incomplet, canon digital de 2017 à vérifier.</aside>
</section>'''

# ---- révisions après relecture du PDF ----
avg_cat=sum(float(r["distance_route_km"]) for r in de if r["region"]=="Catalogne")/sum(1 for r in de if r["region"]=="Catalogne")
avg_all=sum(float(r["distance_route_km"]) for r in de)/len(de)
S["kpis"]=f"""<section id="kpis">
<h2>Les KPIs du cahier des charges, et la décision que chacun éclaire</h2>
<table class="kt dense">
<tr><th>Axe</th><th>KPIs</th><th>Ce que ça décide</th><th>Notre résultat</th></tr>
<tr><td><b>Marché et potentiel</b></td><td>croissance du secteur, part de marché de LDLC en France, part de marché du leader espagnol</td><td>le plafond de CA accessible</td><td>+17,7 % en 2025 en Espagne ; MediaMarkt 21,5 % ; LDLC ≈ 1,4 % en France</td></tr>
<tr><td><b>Prix et marges</b></td><td>indice de prix relatif, marge brute post-taxe</td><td>peut-on être au bon prix ?</td><td>indice 86,7 ; Android 70,8 ; marge Android si alignement −7 %</td></tr>
<tr><td><b>Réseau et implantation</b></td><td>densité concurrentielle par zone, coût au m²</td><td>rythme et coût d'ouverture</td><td>11,1 points de vente pour 100 000 hab. à Barcelone ; loyer proxy 135 €/m²/mois</td></tr>
<tr><td><b>Opérations et logistique</b></td><td>distance aux hubs, douane et taxes locales</td><td>impact sur l'approvisionnement</td><td>{fr(avg_cat,0)} km en moyenne vers la Catalogne ; pas de douane, TVA 21 %, canon digital</td></tr>
<tr><td><b>Assortiment</b></td><td>pénétration de la téléphonie, % du catalogue éligible</td><td>catalogue complet ou ciblé</td><td>téléphonie 29,9 % du marché ; 97,9 % des smartphones LDLC déjà en ligne sur ldlc.com/es-es</td></tr>
</table>
<aside>2 min. Georges (analyse). On reprend les cinq axes du cahier des charges. Chaque KPI répond à une décision. Catalogue éligible : LDLC a déjà un site espagnol (ldlc.com/es-es) qui liste 368 smartphones sur les 376 du site français (comparaison par marque, relevé du 13/11/2026). L'assortiment n'est donc pas un frein : déploiement du catalogue complet possible. La part de marché de LDLC en France est une estimation de l'équipe (CA particuliers / marché des biens techniques).</aside>
</section>"""
cat=[r for r in de if r["region"]=="Catalogne"]
rows_cat="".join(f'<tr><td>{esc(r["ville"])}</td><td class="r">{fr(float(r["distance_route_km"]),0)} km</td><td class="r">{fr(float(r["duree_route_h"]))} h</td><td class="r">{fr(float(r["nb_points_de_vente"]),0)}</td><td class="r">{fr(float(r["points_de_vente_pour_100k_hab"]))}</td></tr>' for r in sorted(cat,key=lambda r: float(r["distance_route_km"])))
S["terrain"]=f"""<section id="terrain">
<h2>La Catalogne est la plus proche de nos hubs, et déjà très équipée</h2>
<div class="split2">
<table class="kt">
<tr><th>Ville</th><th class="r">Route depuis l'Isère</th><th class="r">Durée</th><th class="r">Points de vente</th><th class="r">Pour 100 000 hab.</th></tr>
{rows_cat}
</table>
<div class="side"><p class="num">21,5 %</p><p class="cap">part de marché de MediaMarkt, leader en Espagne (24,6 % en magasins)</p><p class="num">{fr(avg_all,0)} km</p><p class="cap">distance moyenne des 10 grandes villes au hub le plus proche (Madrid : {fr(float(mad["distance_route_km"]),0)} km depuis Nantes)</p></div>
</div>
<p class="source">Sources : OpenStreetMap (Overpass, magasins de téléphonie, d'électronique et d'informatique par commune), OSRM (voiture, depuis le centre de la commune du hub), Ceconomy. OSM est contributif : un magasin absent n'est pas compté</p>
<aside>45 s. La Catalogne est la zone logique : à 6 à 8 heures de route du hub de l'Isère. Les villes moyennes catalanes ont plus de points de vente par habitant que Barcelone. Limite : on mesure par commune, pas encore par zone de chalandise (temps de trajet autour d'un magasin).</aside>
</section>"""
S["ia"]=f"""<section id="ia">
<h2>La brique IA : une synthèse rédigée à partir de nos chiffres, en direct</h2>
<div class="split2">
<div class="cards">
<div class="card"><h3>Ce qu'elle reçoit</h3><p>tous les KPIs du dashboard, les réglages du simulateur et la liste des limites</p></div>
<div class="card"><h3>Ce qu'elle doit respecter</h3><p>n'utiliser que ces chiffres, dire quand un chiffre vient d'une hypothèse, 220 mots maximum</p></div>
</div>
<div class="card iacard"><p class="tagline">Structure imposée</p><p class="big">1. Constats chiffrés<br>2. Recommandation<br>3. Ce qui fragilise l'analyse<br>4. Données à collecter</p></div>
</div>
<p class="body">Le Comex change une hypothèse dans le simulateur, la synthèse se réécrit avec les nouveaux chiffres.</p>
<p class="source">Claude, appelé depuis le dashboard ; version script dans src/ai/synthese.py (API Claude) pour la collecte hebdomadaire</p>
<aside>30 s. Démo en direct dans le dashboard : baisser la marge brute à 15 % dans le simulateur, puis générer la synthèse. Montrer qu'elle signale les hypothèses.</aside>
</section>"""
S["reco"]=f"""<section id="reco" class="dark">
<h2>Notre recommandation : No-Go magasins en 2027</h2>
<div class="cards c3">
<div class="card choice"><p class="tagline">Ce qu'on recommande</p><h3>Renforcer la vente en ligne</h3><p>depuis les hubs français, sans loyer ni personnel en Espagne</p></div>
<div class="card"><p class="tagline">Conditions pour passer en Go</p><h3>Trois seuils</h3><p>prix Android à moins de 5 % des concurrents, marge post-taxe d'au moins 22 %, loyer en centre commercial confirmé</p></div>
<div class="card"><p class="tagline">Next steps</p><h3>Décider en 2028</h3><p>coûts d'achat réels de LDLC, prix MediaMarkt Espagne, catalogue complet, loyers en périphérie</p></div>
</div>
<table class="kt axes">
<tr><td>Marché et potentiel</td><td class="go">favorable</td><td>Prix et marges</td><td class="nogo">bloquant</td><td>Réseau</td><td class="mid">à préciser</td></tr>
<tr><td>Logistique et taxes</td><td class="go">favorable</td><td>Assortiment</td><td class="go">favorable</td><td></td><td></td></tr>
</table>
<p class="source light">La collecte continue chaque semaine : la recommandation se met à jour avec les données</p>
<aside>1 min 30. Rubens. Trancher : No-Go magasins, Go online. Les conditions de succès rendent la décision réversible. Limites à assumer si on nous les demande : une seule enseigne espagnole relevée, marge téléphonie non publiée, loyer proxy, OSM incomplet, canon digital de 2017 à vérifier.</aside>
</section>"""

order=["cover","reponse","entreprise","methode","etoile","kpis","marche","prix","marge","terrain","pilote","ia","reco"]
for k,v in S.items(): open(f"project/slides/{k}.html","w").write(v)
now=datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
deck={"v":5,"createdOnFiles":{"v":1,"at":now},"lists":"css","format":{"v":1,"shared":["project/deck.css"]},
 "title":"LDLC en Espagne : recommandation au Comex","order":order,"cover":"cover",
 "sections":{"s1":{"description":"La question et notre réponse","start":"cover"},"s2":{"description":"L'entreprise, la méthode et la base de données","start":"entreprise"},"s3":{"description":"Les chiffres : marché, prix, marge, terrain, magasin pilote","start":"marche"},"s4":{"description":"La recommandation au Comex","start":"reco"}},
 "faces":{"space-grotesk":{"family":"Space Grotesk","href":"https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400..700&display=swap"},"inter":{"family":"Inter","href":"https://fonts.googleapis.com/css2?family=Inter:wght@400..700&display=swap"}},"designSystems":[]}
json.dump(deck,open("project/deck.json","w"),ensure_ascii=False,indent=1)
