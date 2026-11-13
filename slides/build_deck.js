// Génère slides/LDLC_Espagne_Comex.pptx à partir de slides/data.json (chiffres du dashboard).
// Usage : node slides/build_deck.js   (python slides/export_data.py régénère data.json)
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const path = require("path");
const { applyTheme } = require(process.env.PPTX_SKILL_DIR + "/scripts/apply_theme.js");

const D = JSON.parse(fs.readFileSync(path.join(__dirname, "data.json"), "utf8"));
const OUT = path.join(__dirname, "LDLC_Espagne_Comex.pptx");

const THEME = {
  name: "LDLC Espagne",
  headFontFace: "Arial", bodyFontFace: "Arial",
  colors: { dk1: "202124", lt1: "FFFFFF", dk2: "5F6368", lt2: "F1F3F4",
    accent1: "1565C0", accent2: "4285F4", accent3: "F4A340", accent4: "D93025", accent5: "188038", accent6: "DADCE0",
    hlink: "1565C0", folHlink: "5F6368" },
};
const HEX = { blue: "1565C0", s1: "4285F4", s2: "F4A340", ink: "202124", grey: "5F6368", line: "DADCE0", bad: "D93025", good: "188038", soft: "F1F3F4" };

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9"; // 10 x 5.625 in
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "LDLC en Espagne : Go ou No-Go ?";
pres.author = "Georges Do Xuan, Thomas Lefevbre, Benjamin Chabani, Rubens Le Scao";
const C = pres.SchemeColor;

pres.defineSlideMaster({
  title: "QUESTION", background: { color: "FFFFFF" },
  objects: [],
  slideNumber: undefined,
});
pres.defineSlideMaster({
  title: "CONTENU", background: { color: "FFFFFF" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.7, fontSize: 28, bold: true, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: { x: 9.2, y: 5.2, w: 0.4, h: 0.25, fontSize: 10, color: C.text2, align: "right" },
});
pres.defineSlideMaster({
  title: "FINAL", background: { color: "FFFFFF" },
  objects: [{ placeholder: { options: { name: "title", type: "title", x: 0.5, y: 0.3, w: 9, h: 0.7, fontSize: 28, bold: true, color: C.text1, align: "left", valign: "middle", margin: 0 }, text: "" } }],
  slideNumber: { x: 9.2, y: 5.2, w: 0.4, h: 0.25, fontSize: 10, color: C.text2, align: "right" },
});

/* ---------- chiffres ---------- */
const fr = (n, d = 1) => n.toLocaleString("fr-FR", { minimumFractionDigits: d, maximumFractionDigits: d });
const pc = (n, d = 1) => fr(n * 100, d) + " %";
const sg = n => (n > 0 ? "+" : "") + fr(n);
const es = D.es, fra = D.fr;
const esLast = es[es.length - 1][1], frLast = fra[fra.length - 1][1];
const gES = esLast / es[es.length - 2][1] - 1, gFR = frLast / fra[fra.length - 2][1] - 1;
const syn = Object.fromEntries(D.syn.map(r => [r.perimetre, r.indice]));
const avg = a => a.reduce((s, x) => s + x, 0) / a.length;
const mApple = avg(D.marge.filter(r => r.famille === "Apple").map(r => r.marge_si_alignement));
const mAnd = avg(D.marge.filter(r => r.famille === "Android").map(r => r.marge_si_alignement));
const bcn = D.dens.find(r => r.ville === "Barcelona");
const rankBcn = [...D.dens].sort((a, b) => b.points_de_vente_pour_100k_hab - a.points_de_vente_pour_100k_hab).findIndex(r => r.ville === "Barcelona") + 1;
const mk = k => D.market_rows.find(r => r.indicateur === k);
const short = s => s.replace(/ 5G/, "").replace(/ Go$/, "");

/* ---------- briques ---------- */
function card(slide, name, x, y, w, h, title, value, delta, tone) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: "FFFFFF" }, line: { color: HEX.line, width: 1 }, objectName: name + " cadre" });
  slide.addText(title, { x, y: y + 0.08, w, h: 0.28, fontSize: 12, color: C.text1, align: "center", isTextBox: true, margin: 0, objectName: name + " titre" });
  slide.addText(value, { x, y: y + 0.36, w, h: 0.5, fontSize: 28, bold: true, color: C.text1, align: "center", isTextBox: true, margin: 0, objectName: name + " valeur" });
  const col = tone === "bad" ? HEX.bad : tone === "good" ? HEX.good : HEX.grey;
  slide.addText(delta, { x, y: y + 0.88, w, h: 0.25, fontSize: 12, color: col, align: "center", isTextBox: true, margin: 0, objectName: name + " variation" });
}
function analysis(slide, runs) {
  slide.addText(runs, { x: 0.5, y: 4.3, w: 9, h: 0.85, fontSize: 14, color: C.text1, align: "left", valign: "top", isTextBox: true, margin: 0, objectName: "Analyse" });
}
const t = (text, bold) => ({ text, options: { bold: !!bold } });
const axisBase = { catAxisLabelFontFace: "Arial", valAxisLabelFontFace: "Arial", catAxisLabelFontSize: 10, valAxisLabelFontSize: 10, catAxisLabelColor: "5F6368", valAxisLabelColor: "5F6368",
  valGridLine: { color: "E8EAED", size: 0.5 }, catGridLine: { style: "none" }, dataLabelFontFace: "Arial", dataLabelFontSize: 10, dataLabelColor: "202124", showTitle: true, titleFontFace: "Arial", titleFontSize: 12, titleColor: "202124" };
function content(section, title, notes) {
  const s = pres.addSlide({ masterName: "CONTENU", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  if (notes) s.addNotes(notes);
  return s;
}

/* ---------- 1. question ---------- */
pres.addSection({ title: "Contexte" });
{
  const s = pres.addSlide({ masterName: "QUESTION", sectionTitle: "Contexte" });
  s.addText("Ouvrir des magasins LDLC en Espagne, sur la téléphonie, est-il réalisable et rentable ?", { x: 1.2, y: 1.6, w: 7.6, h: 1.6, fontSize: 30, color: C.text1, align: "center", valign: "middle", isTextBox: true, objectName: "Question" });
  s.addText("Groupe LDLC : 125 magasins, CA 554,1 M€, magasins espagnols fermés en 2020", { x: 1.2, y: 3.6, w: 7.6, h: 0.4, fontSize: 14, color: C.text2, align: "center", isTextBox: true, objectName: "Contexte" });
  s.addText("Georges Do Xuan, Thomas Lefevbre, Benjamin Chabani, Rubens Le Scao", { x: 1.2, y: 4.8, w: 7.6, h: 0.3, fontSize: 12, color: C.text2, align: "center", isTextBox: true, objectName: "Équipe" });
  s.addNotes("Question posée par le Comex. Périmètre : smartphones. Pays : Espagne. On y répond avec 11 KPIs, tous visibles dans le dashboard.");
}

/* ---------- 2. marché ---------- */
pres.addSection({ title: "Analyse" });
{
  const s = content("Analyse", "Marché : l'Espagne croît deux fois plus vite", "Eurostat, NACE G474, volume des ventes en magasins spécialisés, corrigé des jours ouvrables. Base 100 en 2021.");
  card(s, "KPI Espagne", 0.5, 1.15, 2.6, 1.2, "Espagne 2025", fr(esLast), `${sg(esLast - 100)} pts vs 2021`, "good");
  card(s, "KPI France", 0.5, 2.55, 2.6, 1.2, "France 2025", fr(frLast), `${sg(frLast - 100)} pts vs 2021`, "good");
  s.addChart(pres.charts.LINE, [
    { name: "Espagne", labels: es.map(r => String(r[0])), values: es.map(r => r[1]) },
    { name: "France", labels: fra.map(r => String(r[0])), values: fra.map(r => r[1]) },
  ], { x: 3.3, y: 1.1, w: 6.2, h: 3.1, ...axisBase, title: "VOLUME DES VENTES, BASE 100 EN 2021", chartColors: [HEX.s1, HEX.s2], lineSize: 3, lineDataSymbolSize: 7, showValue: true, dataLabelPosition: "t", dataLabelFormatCode: "0.0", showLegend: true, legendPos: "b", legendFontFace: "Arial", legendFontSize: 10, valAxisMinVal: 80, valAxisMaxVal: 180 });
  analysis(s, [t("Depuis 2021, le commerce high-tech spécialisé gagne "), t(`${fr(esLast - 100)} %`, true), t(" en Espagne contre "), t(`${fr(frLast - 100)} %`, true), t(" en France. En 2025, l'Espagne croît de "), t(`${sg(gES * 100)} %`, true), t(" contre "), t(`${sg(gFR * 100)} %`, true), t(" : le marché est porteur.")]);
}

/* ---------- 3. taille du marché ---------- */
{
  const tel = mk("marche_telephonie") && D.tel;
  const mm = D.market_rows.find(r => r.indicateur === "part_marche_mediamarkt");
  const apple = D.market_rows.find(r => r.indicateur === "part_parc_apple").valeur, sam = D.market_rows.find(r => r.indicateur === "part_parc_samsung").valeur, xia = D.market_rows.find(r => r.indicateur === "part_parc_xiaomi").valeur;
  const s = content("Analyse", "Un marché de 3,6 Md€, déjà occupé", "Marché téléphonie : 29,9 % de 12 000 M€ de biens techniques (calcul équipe). Parc : parts de marques en Espagne.");
  card(s, "KPI marché", 0.5, 1.15, 2.6, 1.2, "Marché téléphonie 2024", `${fr(D.tel.valeur / 1000)} Md€`, "29,9 % des biens techniques", "flat");
  card(s, "KPI leader", 0.5, 2.55, 2.6, 1.2, "Part de MediaMarkt", pc(mm.valeur), "leader espagnol", "flat");
  s.addChart(pres.charts.BAR, [{ name: "Part du parc", labels: ["Apple", "Samsung", "Xiaomi"], values: [apple * 100, sam * 100, xia * 100] }],
    { x: 3.3, y: 1.1, w: 6.2, h: 3.1, ...axisBase, barDir: "col", title: "PART DU PARC DE MOBILES EN ESPAGNE (%)", chartColors: [HEX.s1], showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 40, barGapWidthPct: 80 });
  analysis(s, [t("La téléphonie pèse "), t("3,6 Md€", true), t(" en Espagne. Apple ("), t(pc(apple), true), t(") et Samsung ("), t(pc(sam), true), t(") dominent le parc, et MediaMarkt détient "), t(pc(mm.valeur), true), t(" du marché : LDLC arrive face à un leader installé.")]);
}

/* ---------- 4. prix ---------- */
{
  const rows = [...D.idx].sort((a, b) => b.indice_es_vs_fr - a.indice_es_vs_fr);
  const s = content("Analyse", "Prix : Android bien moins cher en Espagne", "Indice = prix HT du concurrent espagnol (PcComponentes) / prix HT LDLC France x 100. 11 modèles appariés, un seul jour de relevé.");
  card(s, "KPI Apple", 0.5, 1.15, 2.6, 1.2, "Indice Apple", fr(syn.Apple), `${fr(syn.Apple - 100)} % vs France`, "bad");
  card(s, "KPI Android", 0.5, 2.55, 2.6, 1.2, "Indice Android", fr(syn.Android), `${fr(syn.Android - 100)} % vs France`, "bad");
  s.addChart(pres.charts.BAR, [{ name: "Indice", labels: rows.map(r => short(r.modele)), values: rows.map(r => r.indice_es_vs_fr) }],
    { x: 3.3, y: 1.1, w: 6.2, h: 3.2, ...axisBase, barDir: "bar", catAxisOrientation: "maxMin", title: "INDICE DE PRIX ESPAGNE / FRANCE (100 = PARITÉ)", chartColors: rows.map(r => r.famille === "Apple" ? HEX.s1 : HEX.s2), showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 120, barGapWidthPct: 40 });
  analysis(s, [t("Pour un même modèle, l'Espagne est en moyenne "), t(`${fr(100 - syn["Tous modèles"])} %`, true), t(" moins chère hors taxes. L'écart est faible sur Apple ("), t(fr(syn.Apple), true), t(") mais fort sur Android ("), t(fr(syn.Android), true), t(") : LDLC devrait baisser ses prix pour s'aligner.")]);
}

/* ---------- 5. marge ---------- */
{
  const rows = [...D.marge].sort((a, b) => b.marge_si_alignement - a.marge_si_alignement);
  const s = content("Analyse", "Marge : s'aligner fait passer Android sous zéro", "Coût d'achat estimé = prix HT France x (1 - 24,5 %). 24,5 % est la marge brute du groupe, appliquée à la téléphonie par hypothèse. Seuil de marge : 22 %.");
  card(s, "KPI Apple", 0.5, 1.15, 2.6, 1.2, "Marge Apple", pc(mApple), `${sg((mApple - 0.22) * 100)} pts vs seuil 22 %`, "bad");
  card(s, "KPI Android", 0.5, 2.55, 2.6, 1.2, "Marge Android", pc(mAnd), `${sg((mAnd - 0.22) * 100)} pts vs seuil 22 %`, "bad");
  s.addChart(pres.charts.BAR, [{ name: "Marge", labels: rows.map(r => short(r.modele)), values: rows.map(r => r.marge_si_alignement * 100) }],
    { x: 3.3, y: 1.1, w: 6.2, h: 3.2, ...axisBase, barDir: "bar", catAxisOrientation: "maxMin", catAxisLabelPos: "low", title: "MARGE SI LDLC S'ALIGNE SUR LE PRIX ESPAGNOL (%)", chartColors: rows.map(r => r.famille === "Apple" ? HEX.s1 : HEX.s2), showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0", showLegend: false, valAxisMinVal: -20, valAxisMaxVal: 30, barGapWidthPct: 40 });
  analysis(s, [t("En vendant au prix espagnol, la marge tombe à "), t(pc(mAnd), true), t(" sur Android : LDLC vendrait à perte. Sur Apple, elle atteint "), t(pc(mApple), true), t(", juste sous le seuil de "), t("22 %", true), t(". Hypothèse : marge brute du groupe appliquée à la téléphonie.")]);
}

/* ---------- 6. concurrence ---------- */
{
  const rows = [...D.dens].sort((a, b) => b.points_de_vente_pour_100k_hab - a.points_de_vente_pour_100k_hab);
  const s = content("Analyse", "Barcelone : peu saturée mais éloignée", "Points de vente téléphonie, électronique et informatique recensés dans OpenStreetMap, rapportés à la population. Hub le plus proche : Saint-Quentin-Fallavier.");
  card(s, "KPI densité", 0.5, 1.15, 2.6, 1.2, "Densité Barcelone", fr(bcn.points_de_vente_pour_100k_hab), `${rankBcn}e sur ${D.dens.length} villes`, "flat");
  card(s, "KPI distance", 0.5, 2.55, 2.6, 1.2, "Distance au hub", `${fr(bcn.distance_route_km, 0)} km`, `${fr(bcn.duree_route_h)} h de route`, "flat");
  s.addChart(pres.charts.BAR, [{ name: "Densité", labels: rows.map(r => r.ville), values: rows.map(r => r.points_de_vente_pour_100k_hab) }],
    { x: 3.3, y: 1.1, w: 6.2, h: 3.2, ...axisBase, barDir: "bar", catAxisOrientation: "maxMin", title: "POINTS DE VENTE POUR 100 000 HABITANTS", chartColors: rows.map(r => r.ville === "Barcelona" ? HEX.s1 : "BDC1C6"), showValue: true, dataLabelPosition: "outEnd", dataLabelFormatCode: "0.0", showLegend: false, valAxisMinVal: 0, valAxisMaxVal: 70, barGapWidthPct: 40 });
  analysis(s, [t("Barcelone compte "), t(fr(bcn.points_de_vente_pour_100k_hab), true), t(" points de vente pour 100 000 habitants, une densité moyenne parmi les 10 villes. Le hub LDLC le plus proche est à "), t(`${fr(bcn.distance_route_km, 0)} km`, true), t(" : la logistique est un coût à intégrer.")]);
}

/* ---------- 7. magasin pilote ---------- */
{
  const sim = D.sim;
  const ca135 = (150 * 135 * 12 + sim.pers) / sim.contrib;
  const xs = []; for (let l = 10; l <= 300; l += 20) xs.push(l);
  const ys = xs.map(l => (150 * l * 12 + sim.pers) / sim.contrib / 1e6);
  const s = content("Analyse", `Pilote : ${fr(sim.ca / 1e6)} M€ de CA pour le point mort`, `Magasin de 150 m2, 14,8 EUR/m2/mois (mediane de 3 annonces de centres commerciaux a Barcelone, echantillon tres petit), 4 ETP, salaire brut 18 887 EUR (convention du commerce de Catalogne), charges patronales 30,7 %, marge brute 24,5 %, autres charges variables 5 %. A 135 EUR/m2/mois (rue de Bilbao), le CA au point mort monte a ${fr(ca135 / 1e6)} M EUR, soit ${pc(ca135 / sim.marche_ville, 2)} du marche.`);
  card(s, "KPI CA", 0.5, 1.15, 2.6, 1.2, "CA point mort", `${fr(sim.ca / 1e6)} M€`, `${fr(sim.fixes / 1e3, 0)} k€ de charges fixes`, "flat");
  card(s, "KPI part", 0.5, 2.55, 2.6, 1.2, "Part de marché requise", pc(sim.part, 2), `${sg((sim.part - 0.01) * 100)} pt vs 1 % visé`, sim.part > 0.01 ? "bad" : "good");
  s.addChart(pres.charts.LINE, [{ name: "CA au point mort", labels: xs.map(String), values: ys }],
    { x: 3.3, y: 1.1, w: 6.2, h: 3.1, ...axisBase, title: "CA AU POINT MORT SELON LE LOYER (M€, € PAR M² ET PAR MOIS)", chartColors: [HEX.s1], lineSize: 3, lineDataSymbol: "none", showValue: false, showLegend: false, valAxisMinVal: 0, valAxisLabelFormatCode: "0.0" });
  analysis(s, [t("Un magasin de 150 m² doit vendre "), t(`${fr(sim.ca / 1e6)} M€`, true), t(" pour couvrir son loyer et son personnel, soit "), t(pc(sim.part, 2), true), t(` du marché téléphonie de Barcelone (${fr(sim.marche_ville / 1e6, 0)} M€) : ${sim.part > 0.01 ? "au-dessus" : "sous"} le repère de 1 %. Avec un loyer de rue commerçante (135 €/m²), il faudrait `), t(`${fr(ca135 / 1e6)} M€`, true), t(` (${pc(ca135 / sim.marche_ville, 2)}).`)]);
}

/* ---------- 8. conclusion ---------- */
pres.addSection({ title: "Conclusion" });
{
  const s = pres.addSlide({ masterName: "FINAL", sectionTitle: "Conclusion" });
  s.addText("Conclusion : No-Go en l'état", { placeholder: "title" });
  s.addNotes("Les seuils de prix et de marge ne sont pas tenus. Celui de part de marché l'est avec un loyer de centre commercial, pas avec celui d'une rue commerçante. Apple est proche des seuils, Android est intenable. Avant de rouvrir le dossier : élargir le relevé de prix, obtenir la marge réelle de la téléphonie, confirmer le loyer.");
  const hd = txt => ({ text: txt, options: { bold: true, color: "FFFFFF", fill: { color: HEX.blue }, align: "center", fontSize: 14 } });
  const cell = (txt, o = {}) => ({ text: txt, options: { fontSize: 14, color: "202124", align: "center", ...o } });
  s.addTable([
    [hd("Seuil"), hd("Résultat"), hd("Verdict")],
    [cell("Indice de prix d'au moins 95", { align: "left" }), cell(`Apple ${fr(syn.Apple)}, Android ${fr(syn.Android)}`), cell("Non tenu", { color: HEX.bad, bold: true })],
    [cell("Marge si alignement d'au moins 22 %", { align: "left" }), cell(`Apple ${pc(mApple)}, Android ${pc(mAnd)}`), cell("Non tenu", { color: HEX.bad, bold: true })],
    [cell("Part de marché requise d'au plus 1 %", { align: "left" }), cell(pc(D.sim.part, 2)), D.sim.part > 0.01 ? cell("Non tenu", { color: HEX.bad, bold: true }) : cell("Tenu", { color: HEX.good, bold: true })],
  ], { x: 0.5, y: 1.2, w: 9, colW: [4.2, 3.1, 1.7], rowH: 0.45, border: { type: "solid", pt: 0.75, color: HEX.line }, objectName: "Tableau des seuils" });
  s.addText([
    { text: "Pour rouvrir le dossier", options: { bold: true, breakLine: true, fontSize: 16 } },
    { text: "Relever les prix chez d'autres enseignes et sur tout le catalogue", options: { bullet: true, breakLine: true } },
    { text: "Obtenir la marge réelle de LDLC sur la téléphonie", options: { bullet: true, breakLine: true } },
    { text: "Tester Apple seul : c'est le plus proche des seuils", options: { bullet: true, breakLine: true } },
    { text: "Confirmer le loyer réel à Barcelone (aujourd'hui 3 annonces)", options: { bullet: true } },
  ], { x: 0.5, y: 3.3, w: 9, h: 1.7, fontSize: 14, color: C.text1, valign: "top", paraSpaceAfter: 6, isTextBox: true, margin: 0, objectName: "Prochaines étapes" });
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("écrit", OUT);
})();
