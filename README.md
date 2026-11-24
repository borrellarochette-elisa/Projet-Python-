
Groupe : Elisa Borrellarochette, Lisa Murcia et Léonard Ribon

## Projet python pour "Python pour la data science" 

Le projet tourne autour de l'évolution des droits de douane des États-Unis avec ses partenaires commerciaux et le lien avec les échanges.

### Composition de dépôt Git Hub :

Le dossier Projet-Python comporte :
- Le fichier Rapport final.ipynb est le notebook destiné au correcteur. Il rassemble les analyses, le code et les explications du projet ainsi que le téléchargement des packages utilisés.

Pour plus de détails, notamment sur l'importation des données les dossiers suivant sont également disponibles :
- Un dossier Importation des données : 2 scripts qui permettent l'importation par API des données utilisées ainsi qu'un script permettant la création du jeu de données final.
- Un dossier Statistiques descriptives : 3 scripts dont Manipulation des données.py qui s'intéresse aux droits de douane, Cartes.py pour afficher les cartes dynamiques ainsi que Econométrie.py qui réalise la partie économétrique du projet.
- Un dossier données complémentaires : script qui permet d'importer des données complémentaires provenant de la Banque Mondiale et du CEPII utiles pour les contrôles en économétrie.

**Remarque :**
Du fait de l'importation par API, la récupération du jeu de données peut prendre plusieurs heures. Pour éviter ce temps le téléchargement des différents fichiers csv se fait dans un dossier data exclu du dépôt GitHub. La base finale est conservée sur le stockage S3 de SSP Cloud et accessible par un lien public. Le notebook charge directement ce fichier, sans relancer les requêtes auprès du Census Bureau.Les scripts sont conservés dans le dépôt, la reconstruction restant donc possible.
**Cela explique pourquoi le code de l'importation des données est exclu du rapport final et contient seulement ces explications.**