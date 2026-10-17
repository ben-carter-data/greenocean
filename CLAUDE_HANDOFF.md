# Passation Codex → Claude — actualisée le 15 octobre 2026

## État actuel — 15-10-2026

Le travail demandé dans `prompt-maestro-greenocean.md` a été implémenté et
vérifié localement. Cette section prévaut sur les consignes de revue par étapes
et les états anciens conservés plus bas comme historique. Le parcours public
actuel ouvre le Dashboard ; il n'attend pas une nouvelle étape « sí ».

Correction du 15-10 après retour utilisateur : les trois représentations utiles
du pipeline sont de nouveau visibles dans leur ordre d'origine. Le mini parcours
ODEPA → Ingesta → ETL → Data warehouse → Panel remplace la longue vue d'ensemble
textuelle en haut. Il affiche les chiffres et états réels, avec des tuiles
flottantes et un flux illustratif lorsque l'animation est activée. Viennent ensuite
le parcours complet par couches et l'architecture par plateformes, tous deux
visibles directement, sans accordéon. Le commutateur anime les trois SVG ; les
points d'état restent liés à la dernière exécution. Une compatibilité de hot reload
accepte aussi l'ancienne signature du mini builder afin qu'une session Streamlit
déjà ouverte ne plante pas pendant la mise à jour. Capture antérieure des deux
grands schémas : `docs/revision-2026-10-15/pipeline-diagramas-restaurados.png`.

Le Dashboard initial met les produits en premier : tableau Top N (8–20) avec
variété, qualité, canal, portée, unité, prix précédent, prix actuel, changement
en pesos et en pourcentage, signal et lien vers Données. Le classement peut
montrer les changements absolus les plus grands, les hausses, les baisses ou
les changements inhabituels. Un produit est sélectionné au départ ; cliquer
un autre produit actualise son prix et ses 12 semaines d'historique. Les
compteurs sont secondaires et disent qu'ils comptent des combinaisons
comparables, pas des produits uniques. Le lien vers Données conserve le
produit, la semaine, les filtres et les réglages Top N/ordre pour le retour.

Sémantique : la comparaison hebdomadaire utilise exactement la semaine
précédente, mêmes produit/variété/qualité/unité/canal et même portée. Une
semaine manquante ou un prix antérieur nul reste sans comparaison ; aucune
valeur n'est inventée. Le prix national est la moyenne simple des régions
disponibles à chaque date ; l'interface indique les séries dont la couverture
régionale a changé. Les alertes gardent leur calcul canonique national et leur
portée est nommée lorsque l'on filtre une région. Le graphique d'historique
coupe les lignes aux semaines absentes. L'ancienne dona faisant double emploi
avec les compteurs et la courbe saisonnière répétée ont été retirées.

La page Données commence par la granularité et la table paginée. L'accès
depuis le Dashboard préremplit exactement le produit et les deux semaines.
Une première colonne « Comparación semanal » explique les lignes sans prix
précédent ; les colonnes numériques restent numériques pour la précision,
le tri natif et le CSV. Limite constatée de Streamlit : dans certaines
colonnes numériques vides, sa grille affiche encore `None` malgré le
formatage ; la première colonne donne le sens en langage clair.

Pipeline présente désormais deux parcours distincts : mise à jour hebdomadaire
ODEPA → GitHub Actions → ETL → tests → base/rapport et consultation navigateur
→ Streamlit → SQLite → résultat. Les flèches numérotées disent où chaque
opération s'exécute et les conséquences d'un échec. Les deux diagrammes SVG
originaux restent visibles directement sous le résumé ; leur animation
illustratrice n'est pas présentée comme un travail en cours. Modèle explique la granularité avant ses
relations ; DevOps explique ses responsabilités. Les détails déroulants du
contenu sont ouverts par défaut.

Le Dashboard garde quatre palettes : Corporativo, Vantablack, Blue Light,
Dark Grey. Le choix du thème est dans la cabecera. La cabecera mobile a reçu
un fond opaque pour ne plus recouvrir le texte pendant le défilement ; le
tableau reste dans son propre espace défilant. Captures de vérification dans
`docs/revision-2026-10-15/README.md` (écran large, étroit, clair et sombre,
Données, Historique, Pipeline, Modèle, DevOps).

Validation de cette passe : `154 passed` pour les tests ciblés Dashboard,
modèle de la première page, architecture et explorateur de données ; compilation
Python et `git diff --check` réussis. Les tests comparent aussi plusieurs prix
à des requêtes indépendantes et couvrent les cas de semaine précédente
absente et de prix antérieur nul. Aucun commit ni push. Ne pas attribuer à
Codex les changements locaux préexistants de Claude ; `git status` contient
encore son travail et cette passe mélangés dans les fichiers partagés.

Pour reprendre : vérifier d'abord `git status`, le présent état et les captures.
Si une amélioration doit supprimer les `None` de la grille native, préserver la
précision et le tri numérique ainsi que l'export brut ; ne pas transformer
silencieusement les données manquantes en zéro.

## Demande et contraintes de l’utilisateur

Reprendre le travail interrompu de Claude en conservant ce qui est déjà établi.
**Aucun push.** Procéder dans cet ordre, avec captures avant/après, pytest et
un « sí » de l’utilisateur entre chaque étape :

1. États gris et cause visible des erreurs GitHub.
2. Responsivité du diagramme.
3. Fusion de Pipeline dans El proyecto et nouvelle première page.
4. T-44 : Vantablack par défaut et cyan.
5. T-32.

Pour l’étape 3 : El proyecto devient la page d’accueil ; pipeline vivant complet
en haut, puis les trois phrases, chiffres et parcours. Un seul diagramme.
Le diagramme détaillé, DevOps (T-51), sécurité, observabilité et rapports vont
dans un onglet Arquitectura. Pipeline disparaît du menu, avec redirection de
l’ancien lien vers cet onglet. Enregistrer la décision au prochain numéro D libre.

## État trouvé à la reprise

Claude avait déjà modifié ces fichiers, sans commit :

- `bi/architecture.py` : points uniquement pour les états connus ; `etl_run`
  reçoit l’état de la dernière charge ; Secretos, Logs et Correo sans point
  lorsqu’aucun état réel n’est disponible.
- `bi/control.py` : fonction `describe_github_error` en espagnol.
- `bi/dashboard.py` : erreurs visibles, cache GitHub de cinq minutes, dernière
  réponse valide conservée et repli sur la dernière charge enregistrée.
- `docs/MANUAL.md` : dépannage AttributeError après push avec Manage app → Reboot,
  et explication des erreurs GitHub.
- Tests associés dans `tests/test_architecture.py`, `tests/test_control.py`
  et `tests/test_dashboard.py`.

Ne pas attribuer tous ces changements à Codex : ils étaient déjà présents.

## Changements supplémentaires effectués par Codex

Dans `bi/control.py`, renforcement de `describe_github_error` :

- Une date `X-RateLimit-Reset` absente ou invalide ne provoque plus d’exception.
- Le texte « sans clé, 60 par heure » est utilisé uniquement si
  `X-RateLimit-Limit` vaut `60` ; sinon le message reste générique.
- Pour les codes HTTP inconnus, utilisation d’un texte contrôlé au lieu de
  `response.reason`, afin de ne pas afficher de texte non filtré.

Dans `tests/test_control.py` : adaptation du cas de limite à 60 et ajout d’un
test couvrant une date invalide et un `response.reason` contenant un faux secret.

Copies des anciennes captures de Claude conservées dans :

- `docs/revision-paso1/antes/pipeline.png`
- `docs/revision-paso1/despues/pipeline.png`

Ces images précèdent les derniers ajustements de Codex. Elles ne constituent
pas une capture du scénario 403 simulé.

## Vérifications

- `.venv/bin/python -m pytest -q` : **200 passed**, environ 126 secondes.
- `git diff --check` : OK.
- Pipeline local ouvert dans Chrome sur `http://localhost:8602/pipeline`.
  Vérification visuelle : Secretos n’a plus de point.
- Simulation d’un HTTP 403 avec Streamlit AppTest : aucune exception et avertissement
  confirmé : « No se pudo consultar GitHub: GitHub respondió 403: se agotó el límite
  de consultas sin clave (60 por hora). »

## Point non terminé et prochaine action

**L’étape 1 n’est pas encore clôturée et aucun « sí » pour l’étape 2 n’a été donné.**
Il reste à obtenir une capture visible du cas d’erreur GitHub simulé.
Une copie temporaire servie sur le port 8603 est restée blanche dans Chrome,
alors que son rendu AppTest produit bien l’avertissement attendu.
Résoudre cette vérification visuelle, présenter le résultat, puis demander
le « sí » de l’utilisateur avant de passer à la responsivité.

## Outils temporaires et état de travail

- Script de simulation, hors dépôt : `/private/tmp/monitor-step1-failure.py`.
  Il remplace les appels de lecture GitHub par un HTTP 403 simulé et affiche
  la page Centro de control. Ne pas intégrer ce mock à l’application.
- Un serveur de vérification a été lancé sur le port 8603 ; vérifier s’il tourne
  encore avant de le réutiliser. Le port 8602 était déjà occupé par le panel local.
- Anciennes captures et scripts de Claude :
  `/private/tmp/claude-501/-Users-carter-Desktop-monitor-precios-hito1/5bd9a839-b954-440f-9b24-5bf897d3d55d/scratchpad/`.
- Aucun commit ni push effectué par Codex. Les étapes 2 à 5 n’ont pas été modifiées.
- Le fichier présent est une note de passation ; il ne remplace pas les consignes
  du projet ou les demandes de l’utilisateur.

## 13-10-2026 — Nouvelle demande de refonte UX

L’utilisateur a demandé un portfolio qui ouvre par les données, puis le pipeline
et l’architecture sur la même page, un menu latéral direct, du code visible dans
des accordéons ouverts, des Top N avant les filtres, un dialogue initial de profil
et deux thèmes lisibles (Vantablack / Corporativo). Cette demande remplace l’ancien
ordre d’accueil. Aucun push autorisé ni effectué.

Implémentation Codex :
- Dashboard avec Top N réels, alertes, puis les diagrammes existants du pipeline
  et de l’infrastructure. Contrôles de ranking facultatifs et export CSV.
- Navigation en quatre groupes, entrées directes pour BA, BI, modèle, code,
  DevOps, monitoring, exécutions et documents. Anciennes adresses redirigées.
- Dialogue de profil avant tout contenu ; profil conservé dans la session et
  les liens internes. Le profil guide, sans contrôle d’accès.
- Code Python public en accordéons dossier/fichier ouverts, descriptions et
  source locale réelle ; puis schémas SQL et catalogue existant de queries.
- Palette sombre à surfaces pizarre ; Claro retiré du sélecteur et migré vers
  Corporativo. Ancienne palette gardée pour compatibilité des exports/tests.
- Décision D-060 dans docs/DECISIONES.md.

Les fichiers bi/explorer.py, tests/test_explorer.py et plusieurs changements
préalables de charts/dashboard/project étaient déjà modifiés au début de cette
reprise. Ne pas les attribuer intégralement à Codex ni les écraser.

Vérification visuelle de cette refonte : formulaire initial dans Safari,
dashboard Vantablack dans Chrome/Safari, Corporativo et code en accordéons dans
Safari. La vue étroite, vérifiée avec le zoom navigateur, a révélé des pourcentages
tronqués : les Top N ont maintenant des barres HTML dédiées aux petits écrans,
avec libellés complets et valeurs signées ; les graphiques Altair restent sur
ordinateur. Le changement de base native vérifie le choix stocké par Streamlit,
car st.context.theme est inféré du fond CSS et pouvait masquer un désaccord
entre palette et widgets. Un garde limite le rechargement à une fois par changement.
Le texte du bouton primaire cian est sombre pour son contraste.

Serveur de revue : http://127.0.0.1:8612/ (session locale, aucun déploiement).
Les captures avant/après ont été affichées dans la conversation ; elles ne sont
pas enregistrées comme nouveaux fichiers dans docs/revision-paso1.

Suite finale : `.venv/bin/python -m pytest -q` → **260 passed, 8 skipped**
en 34,10 s. Les huit skips sont les contrôles HTTP de liens publics, ignorés par
les tests existants quand le réseau est inaccessible. `git diff --check` : OK.
Aucun commit ni push de cette refonte.

## 13-10-2026 — Instruction suivante : « nada debe estar duplicado »

Suppression des copies de contenu entre pages :
- Top N uniquement dans Dashboard ; Análisis garde les vues filtrées et un lien.
- Infrastructure uniquement dans Dashboard ; DevOps garde ses explications et un lien.
- État et légende du pipeline une seule fois sur la page d’accueil.
- Liste détaillée d’alertes uniquement dans Análisis ; résumé chiffré sur Dashboard.
- Queries uniquement dans Datos y SQL → Queries ; Código et les indicateurs y renvoient.
- Schémas SQL uniquement dans Código ; Modelo de datos et Queries y renvoient.
- Fonctions Python de réconciliation non recopiées dans les queries : lien vers le fichier.
- Lien de KPI avec `consulta=nom` : la query canonique s’ouvre en premier, une seule fois.
- Anciens renderers de la page d’accueil devenus inutilisés retirés.

Décision D-061. Des tests vérifient que les blocs de source affichés sont uniques
entre toutes les pages, et que les Top N et l’infrastructure ont un seul propriétaire.
Les vues mobiles/desktop d’un même ranking sont des alternatives CSS exclusives,
et les vues filtrées sur des sélections différentes ne sont pas des copies du panorama.
Aucun push.

Validation après déduplication : **263 passed, 8 skipped en 36,37 s** ;
les huit contrôles de liens externes restent ignorés faute de réseau.
`git diff --check` sans erreur.

## 13-10-2026 — Identité du projet, accès direct et diagrammes séparés

Nouvelle instruction de l’utilisateur : supprimer l’identité « portafolio »,
formaliser BA avec mission/vision/périmètre, ouvrir le dashboard après le profil,
sortir les diagrammes du dashboard, rétablir un flux animé, utiliser des formes
selon la fonction et privilégier le menu aux onglets.

Réalisé :
- Dashboard uniquement pour les résultats. Diagrammes uniques dans
  « Pipeline y arquitectura », modèle dans sa propre section.
- Aucune utilisation de st.tabs dans dashboard.py : chaque analyse et les queries
  ont une destination directe. Anciennes URLs/sections redirigées.
- Navigation Anterior / Siguiente en haut et bas de toutes les pages, dans le même
  ordre que les six groupes du menu.
- Définition métier rédigée dans docs/PROYECTO.md → Marco de negocio : mission,
  vision, objectif, périmètre, exclusions et critères d’acceptation, puis exigences,
  stakeholders, sources et livrables.
- Symboles SVG et silhouettes selon le rôle, via les helpers communs ; les cartes
  de sécurité reçoivent explicitement le symbole de bouclier.
- Illustration du flux animée par défaut et contrôlable. Les états restent réels.
  Les builders SVG acceptent animate_flow=None (comportement lié au run), True
  (illustration active) ou False (flux arrêté). La préférence reduced-motion est respectée.
- Tous les profils reviennent au dashboard après validation, même depuis un ancien
  lien de section. Correction de st.switch_page : ne pas réassigner le paramètre
  lié au widget de thème, ce que Streamlit refuse.
- Décision D-062 et manuel actualisés. Les huit tests réseau restent optionnels.

Validation : **279 passed, 8 skipped en 38,75 s**. Les tests couvrent les quatre
profils, les redirections avec thème lié, l’absence d’onglets, les emplacements
uniques du contenu, le parcours et la séparation entre animation et état réel.

Revue visuelle Safari : formulaire, arrivée au dashboard, mission/vision et
page des diagrammes. Le serveur local 8612 conservait l’ancien module architecture
et affichait un TypeError sur animate_flow ; le processus de revue identifié a
été redémarré puis la page rechargée, ce qui a résolu le problème. Le même lien
http://127.0.0.1:8612/ sert la version actuelle. Aucun commit ni push.

## 13-10-2026 — Contrôles du ranking au-dessus des graphiques

À la demande de l’utilisateur, l’accordéon « Ajustar el ranking · Top N, alzas y bajas »
précède maintenant les deux graphiques du dashboard. Il reste unique ; les valeurs
des widgets alimentent directement les rankings et leur export dans le même rendu.
Validation ciblée : **3 passed** (dashboard, classement et rendu mobile),
`git diff --check` sans erreur. Aucun commit ni push.

## 13-10-2026 — Tout ouvert par défaut

Nouvelle consigne globale : tous les accordéons et détails dépliables de toutes
les pages s’ouvrent par défaut, y compris historiques, filtres, tables, KPI,
qualité, documentation et fichiers supplémentaires. Le visiteur peut les refermer.
Le statut détaillé d’une exécution reste ouvert aussi après succès ou erreur.
Cette consigne remplace les anciens choix de détails repliés et du premier
document seul ouvert. Manuel actualisé. Aucun commit ni push.

Validation : **88 tests dashboard réussis** ; contrôle des 25 déclarations
expander/status : toutes avec expanded=True. `git diff --check` sans erreur.

## 13-10-2026 — Dashboard flottant sur un fond alimentaire

Demande : s’inspirer de la référence visuelle de panneaux flottants tout en gardant
les graphiques interactifs. Fond généré avec imagegen, stocké dans
bi/assets/market-background.jpg ; prompt et provenance dans bi/assets/README.md.
Styles isolés dans bi/market_style.py et appliqués seulement au dashboard : voile
selon le thème, surfaces élevées, quatre KPI individuels, graphiques arrondis,
empilement aux petits formats et en-tête compact. Les données restent réelles et
les composants Altair/Streamlit indépendants du fond. Tous les détails restent ouverts.

Revue Safari : fond, surfaces, filtre Bajas qui actualise réellement les barres et
le tableau, rendu Corporativo. Correction d’une course au changement de thème :
le script conserve explicitement tema dans l’URL avant le reload des widgets natifs.
106 tests dashboard/graphiques réussis avant cette dernière correction ; validation
ciblée supplémentaire ci-dessous. D-063 et manuel actualisés. Aucun commit ni push.

Validation complémentaire : 3 tests ciblés réussis (thème et accueil),
`git diff --check` sans erreur. Safari confirme que Corporativo reste sélectionné
après changement via le sélecteur et rechargement ; retour Vantablack vérifié aussi.

## 13-10-2026 — Palette conservée, dominante Vantablack à 70–80 %

Précision de l’utilisateur : garder sa palette, sans un rendu intégralement noir.
Le dashboard réutilise désormais les couleurs exactes de charts.PALETTES : fond
Vantablack, surfaces ardoise, champs plus clairs et accents cyan. Les anciennes
teintes vertes des panneaux et ivoire du voile ont été supprimées. Voile sombre
de 80 à 70 % sur la photo, deux KPI sur une surface field légèrement plus claire.
La cible 70–80 % désigne l’équilibre visuel, pas une mesure de pixels. Corporativo
conserve sa propre palette. Interactions et ouverture par défaut inchangées.

Validation : 5 tests ciblés réussis, `git diff --check` sans erreur. Revue Safari
en Vantablack : panneaux ardoise différenciés, accents cyan et photo visibles.

## 13-10-2026 — Variété graphique et véritable vue 3D

Demande : ajouter des formes de graphiques variées, surtout de la 3D interactive.
Nouveau bi/market_charts.py (Plotly) : anneau de composition des observations de la
dernière semaine, courbes avec aire des prix nationaux sur 12 semaines, scène 3D
région × canal × indice régional et alternative heatmap 2D exclusive. La 3D est
active par défaut. Les rankings Altair restent en dessous, avec leurs contrôles en haut.
Le produit par défaut a le plus d’observations de la semaine (départage stable).
Les courbes et le territoire partagent une clé complète : groupe, produit, variété,
qualité, unité. Les couleurs existantes et la dominante Vantablack restent en place.

Sources : requêtes canoniques K3/K6, filtrage de la semaine en SQLite et cache lié
à la version de la base. L’anneau compte des observations, pas des ventes ; l’indice
100 est national pour le même canal ; aucune interpolation des semaines absentes.
Plotly 6.9.0 installé localement ; requirements.txt : plotly>=5.24,<7. Nouveau module
et styles ajoutés au parcours de code public, descriptions en espagnol. D-064 et
manuel actualisés. Tests sémantiques dans tests/test_market_charts.py, plus intégration
dashboard et bascule 3D/2D sans duplication. Revue Safari : anneau, courbes et vraie
scène WebGL affichés. Aucun commit ni push.

Validation : suite complète **288 passed, 8 skipped en 41,98 s** (liens externes
ignorés sans réseau). Revue Safari : bascule vers la matrice 2D puis retour 3D,
sans affichage simultané ; marges de la courbe et caméra ajustées pour les étiquettes.
`git diff --check` sans erreur.

## 13-10-2026 — Revue après les commits Claude et dashboard de BI

Claude avait ensuite regroupé le projet en six fenêtres et ajouté des pages 3D.
Codex a conservé cette structure, puis corrigé les écarts trouvés lors de la revue :

- Le résumé est maintenant une grille de rapport comparable à Power BI/Looker :
  filtres séparés du titre, quatre indicateurs calculés et cliquables avec mini-graphiques,
  ranking des changements, tendance, composition, ranking des brechas et matrice région × canal.
- La scène 3D région × canal, trop lente à interpréter, ne figure plus dans le résumé.
  La matrice montre immédiatement la valeur et garde les analyses 3D dans la vue avancée.
- La vue plane des brechas avancées trace tous les canaux sélectionnés ; elle ne perd plus
  silencieusement tous les canaux sauf le premier.
- Les vues du rapport se choisissent dans la même cabecera, avec les flèches chronologiques,
  au lieu d'une rangée de sept gros boutons. Le thème se choisit aussi dans cette cabecera ;
  le sélecteur a été retiré du panneau latéral.
- Nouveau thème « Grafito » : gris charbon, panneaux gris profond et accent vert discret.
  L'ancien libellé provisoire est migré automatiquement vers Grafito au reload.
- Les quatre indicateurs ouvrent leur analyse canonique sans copier le contenu. Les anciennes
  URLs `seccion=Enlaces` sont résolues par fenêtre malgré les titres désormais numérotés.
- Les détails que Claude avait refermés sont de nouveau ouverts par défaut, conformément à
  la consigne globale de l'utilisateur.

Revue visuelle Safari sur `http://127.0.0.1:8612/` : cabecera compacte, Vantablack,
Grafito, deux rangées du rapport, heatmap et table ouverte ; aucun chevauchement observé.
Validation finale : **294 passed, 8 skipped en 43,80 s** ; les skips restent les liens
externes sans réseau. `git diff --check` sans erreur. Aucun commit ni push.

## 13-10-2026 — Aucun contrôle technique au-dessus du rapport

Le widget flottant de développement Streamlit (« File change / Rerun / Always rerun »)
recouvrait le contenu sur les fenêtres étroites. Le CSS global masque désormais
`stStatusWidget` sur toutes les pages et `.streamlit/config.toml` utilise
`client.toolbarMode = "viewer"` afin de retirer aussi les actions de développeur du
rapport. Test automatisé ajouté. Vérification Safari effectuée en provoquant un nouveau
changement après rechargement : le watcher a réagi, mais aucun texte ni bouton flottant
n'est apparu dans l'interface ou l'arbre d'accessibilité. Validation finale :
**295 passed, 8 skipped en 43,60 s**. Aucun commit ni push.

## 13-10-2026 — Lecture publique simple et SQL sans superposition

La vue « Consulta de datos » a été revue pour une personne sans vocabulaire de
données. Le résumé utilise maintenant « Dentro de lo habitual », « Conviene
revisar », « Cambio poco común » et « Aún sin historial ». Le détail par groupe
a des en-têtes visibles et des boutons courts qui restent lisibles sans symbole.
La table fusionne produit, variété et qualité, écrit l'unité dans le prix et
remplace « variación », « brecha » et « alerta » par des phrases explicites.

Le SQL n'est plus un popover au-dessus de la table. Il est placé après la table,
dans un expander ouvert, avec une phrase précisant que sa lecture est optionnelle.
Les liens publics vers les calculs n'affichent plus K1–K8 ; ces identifiants restent
uniquement dans les adresses et le code. La page d'indicateurs présente désormais
les noms complets. Les consultations SQL commencent par la question en langage
courant, puis donnent leur nom technique.

Le brief réutilisable pour la suite est dans `docs/UX_READABILITY_PROMPT.md` :
lecture possible à 12 ans, langage courant, unités visibles, aucun code interne
dans l'interface publique, ordre résumé → détail → technique, aucun chevauchement,
aucune duplication et vérification des trois palettes. Revue Safari Grafito :
libellés complets, table compacte, SQL sous la table et aucune superposition.
Validation finale : **295 passed, 8 skipped en 40,83 s** ; `git diff --check`
sans erreur. Aucun commit ni push.
